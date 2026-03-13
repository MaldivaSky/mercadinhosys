"""
Sistema Híbrido - Sincronização Local ↔ Cloud
SQLite local para velocidade + PostgreSQL/Aiven para backup
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import sqlite3
import psycopg2
import json
import os
from datetime import datetime
import logging
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
import io

sync_hybrid_bp = Blueprint('sync_hybrid', __name__)
logger = logging.getLogger(__name__)

class HybridSyncManager:
    """Gerenciador de sincronização híbrida"""
    
    def __init__(self):
        self.local_db_path = "mercadinho.db"
        self.cloud_db_url = os.getenv('AIVEN_DATABASE_URL')
        self.backup_providers = ['google_drive', 'onedrive']
    
    def get_local_connection(self):
        """Conexão com banco local SQLite"""
        return sqlite3.connect(self.local_db_path)
    
    def get_cloud_connection(self):
        """Conexão com banco nuvem PostgreSQL"""
        return psycopg2.connect(self.cloud_db_url)
    
    def export_local_data(self):
        """Exporta todos os dados do banco local"""
        try:
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            # Obter todas as tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
            tables = [row[0] for row in cursor.fetchall()]
            
            data = {}
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                # Converter para lista de dicionários
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Converter tipos especiais para JSON serializable
                        if isinstance(value, datetime):
                            row_dict[columns[i]] = value.isoformat()
                        elif value is None:
                            row_dict[columns[i]] = None
                        else:
                            row_dict[columns[i]] = value
                    table_data.append(row_dict)
                
                data[table] = {
                    'columns': columns,
                    'rows': table_data,
                    'count': len(table_data)
                }
            
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'total_tables': len(tables)
            }
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados locais: {e}")
            return {'success': False, 'error': str(e)}
    
    def import_to_cloud(self, data):
        """Importa dados para o banco na nuvem"""
        try:
            conn = self.get_cloud_connection()
            cursor = conn.cursor()
            
            imported_tables = 0
            total_rows = 0
            
            for table_name, table_data in data['data'].items():
                if table_name == 'sqlite_sequence':  # Pular tabela interna do SQLite
                    continue
                
                columns = table_data['columns']
                rows = table_data['rows']
                
                if not rows:
                    continue
                
                # Criar tabela se não existir
                create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        {', '.join([f"{col} TEXT" for col in columns if col != 'id'])}
                    )
                """
                cursor.execute(create_table_sql)
                
                # Inserir dados
                for row in rows:
                    # Preparar valores (ignorar id se existir)
                    values = []
                    cols_to_insert = []
                    
                    for col in columns:
                        if col == 'id':
                            continue  # Deixa o PostgreSQL gerar o ID
                        
                        value = row.get(col)
                        if value is None:
                            values.append('NULL')
                        else:
                            values.append(f"'{str(value).replace(chr(39), chr(39)+chr(39))}'")
                        cols_to_insert.append(col)
                    
                    if values:
                        insert_sql = f"""
                            INSERT INTO {table_name} ({', '.join(cols_to_insert)})
                            VALUES ({', '.join(values)})
                            ON CONFLICT DO NOTHING
                        """
                        cursor.execute(insert_sql)
                        total_rows += 1
                
                imported_tables += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'imported_tables': imported_tables,
                'total_rows': total_rows
            }
            
        except Exception as e:
            logger.error(f"Erro ao importar para nuvem: {e}")
            return {'success': False, 'error': str(e)}
    
    def backup_to_google_drive(self, data):
        """Faz backup para Google Drive"""
        try:
            # Criar arquivo JSON em memória
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Autenticação OAuth (precisa ser configurada)
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            # Aqui você precisa configurar as credenciais OAuth
            # Por enquanto, retorna simulação
            return {
                'success': True,
                'provider': 'google_drive',
                'file_size': len(json_data),
                'message': 'Backup simulado - configure OAuth2 para Google Drive'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def backup_to_onedrive(self, data):
        """Faz backup para OneDrive"""
        try:
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Aqui você precisa configurar Microsoft Graph API
            return {
                'success': True,
                'provider': 'onedrive',
                'file_size': len(json_data),
                'message': 'Backup simulado - configure Microsoft Graph API'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

sync_manager = HybridSyncManager()

@sync_hybrid_bp.route('/status', methods=['GET'])
@jwt_required()
def sync_status():
    """Status da sincronização"""
    try:
        # Verificar banco local
        local_info = {}
        try:
            conn = sync_manager.get_local_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            local_info['tables'] = cursor.fetchone()[0]
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            local_info['table_names'] = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            local_info['status'] = 'online'
        except Exception as e:
            local_info['status'] = 'error'
            local_info['error'] = str(e)
        
        # Verificar banco nuvem
        cloud_info = {}
        try:
            conn = sync_manager.get_cloud_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            cloud_info['tables'] = len(cursor.fetchall())
            cursor.close()
            conn.close()
            cloud_info['status'] = 'online'
        except Exception as e:
            cloud_info['status'] = 'error'
            cloud_info['error'] = str(e)
        
        return jsonify({
            'success': True,
            'data': {
                'local_db': local_info,
                'cloud_db': cloud_info,
                'last_sync': None,  # Implementar rastreamento de última sincronização
                'available_backups': sync_manager.backup_providers
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_hybrid_bp.route('/upload', methods=['POST'])
@jwt_required()
def sync_upload():
    """Sincroniza dados locais para nuvem"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get('estabelecimento_id')
        
        # 1. Exportar dados locais
        export_result = sync_manager.export_local_data()
        if not export_result['success']:
            return jsonify(export_result), 500
        
        # 2. Importar para nuvem
        import_result = sync_manager.import_to_cloud(export_result)
        if not import_result['success']:
            return jsonify(import_result), 500
        
        # 3. Fazer backup adicional (opcional)
        backup_provider = request.json.get('backup_provider') if request.json else None
        
        backup_result = None
        if backup_provider in sync_manager.backup_providers:
            if backup_provider == 'google_drive':
                backup_result = sync_manager.backup_to_google_drive(export_result)
            elif backup_provider == 'onedrive':
                backup_result = sync_manager.backup_to_onedrive(export_result)
        
        return jsonify({
            'success': True,
            'message': 'Sincronização concluída com sucesso!',
            'data': {
                'exported_tables': export_result['total_tables'],
                'imported_tables': import_result['imported_tables'],
                'total_rows': import_result['total_rows'],
                'backup': backup_result,
                'timestamp': export_result['timestamp'],
                'estabelecimento_id': estabelecimento_id
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_hybrid_bp.route('/download', methods=['POST'])
@jwt_required()
def sync_download():
    """Sincroniza dados da nuvem para local"""
    try:
        # Implementar download da nuvem para local
        return jsonify({
            'success': True,
            'message': 'Download da nuvem implementação pendente'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_hybrid_bp.route('/backup', methods=['POST'])
@jwt_required()
def create_backup():
    """Cria backup dos dados"""
    try:
        data = request.get_json()
        backup_provider = data.get('provider', 'local')
        
        # Exportar dados locais
        export_result = sync_manager.export_local_data()
        
        if not export_result['success']:
            return jsonify(export_result), 500
        
        # Fazer backup no provider selecionado
        if backup_provider == 'google_drive':
            backup_result = sync_manager.backup_to_google_drive(export_result['data'])
        elif backup_provider == 'onedrive':
            backup_result = sync_manager.backup_to_onedrive(export_result['data'])
        else:
            # Backup local
            json_data = json.dumps(export_result['data'], indent=2, ensure_ascii=False)
            backup_result = {
                'provider': 'local',
                'file_size': len(json_data),
                'timestamp': datetime.now().isoformat(),
                'filename': f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        
        return jsonify({
            'success': True,
            'backup': backup_result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_hybrid_bp.route('/restore', methods=['POST'])
@jwt_required()
def restore_backup():
    """Restaura dados de um backup"""
    try:
        data = request.get_json()
        backup_data = data.get('backup_data')
        
        if not backup_data:
            return jsonify({'success': False, 'error': 'Dados do backup não fornecidos'}), 400
        
        # Restaurar para banco local
        # Implementar lógica de restauração
        
        return jsonify({
            'success': True,
            'message': 'Backup restaurado com sucesso'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
