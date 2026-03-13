# app/routes/configuracao.py
"""
Módulo de Configuração de Elite - MercadinhoSys
Gerenciamento resiliente de configurações e dados do estabelecimento.
Usa SQL direto via query_helpers para evitar falhas de ORM em produção.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models import Configuracao
from app.utils.query_helpers import get_configuracao_safe, get_estabelecimento_full_safe, get_authorized_establishment_id
from app.utils.smart_cache import get_cached_config, set_cached_config, invalidate_config
import json
import traceback

configuracao_bp = Blueprint("configuracao", __name__)

# ==================== CONFIGURAÇÕES ====================

@configuracao_bp.route("/", methods=["GET"])
@jwt_required()
def obter_configuracoes():
    """Obtém configurações do estabelecimento (Padrão Blindado)"""
    try:
        claims = get_jwt()
        estabelecimento_id = get_authorized_establishment_id()
        
        if not estabelecimento_id:
            return jsonify({"success": False, "error": "Estabelecimento não identificado no token ou context"}), 400

        # Tenta buscar do cache primeiro
        config_data = get_cached_config(estabelecimento_id)
        if config_data:
            return jsonify({"success": True, "config": config_data}), 200

        config_data = get_configuracao_safe(estabelecimento_id)
        
        # Se não existir, tenta criar uma padrão via ORM (operação segura inicial)
        if not config_data:
            try:
                nova_config = Configuracao(estabelecimento_id=estabelecimento_id)
                db.session.add(nova_config)
                db.session.commit()
                config_data = get_configuracao_safe(estabelecimento_id)
            except Exception:
                db.session.rollback()
                # Fallback total: retorna objeto default em memória
                config_data = {
                    "cor_principal": "#007bff",
                    "tema_escuro": False,
                    "formas_pagamento": "[]"
                }

        # Salva no cache se encontrou ou criou
        set_cached_config(estabelecimento_id, config_data)

        return jsonify({
            "success": True, 
            "config": config_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"❌ Erro em obter_configuracoes: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao carregar configurações"}), 500


@configuracao_bp.route("/", methods=["PUT"])
@jwt_required()
def atualizar_configuracoes():
    """Atualiza as configurações do estabelecimento com SQL Puro (Blindado contra Schema Drift)"""
    try:
        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()
        role = claims.get("role")
        
        if role not in ["admin", "dono", "gerente", "ADMIN"]:
            return jsonify({"success": False, "error": "Sem permissão para alterar configurações"}), 403

        data = request.get_json() or {}
        
        # Campos permitidos para atualização (Sincronizados com Frontend e Banco)
        allowed_fields = [
            "logo_url", "cor_principal", "tema_escuro", "impressao_automatica",
            "tipo_impressora", "formas_pagamento", "emitir_nfe", "emitir_nfce",
            "controlar_validade", "alerta_estoque_minimo", "dias_alerta_validade",
            "estoque_minimo_padrao", "exibir_preco_tela", "permitir_venda_sem_estoque",
            "desconto_maximo_percentual", "desconto_maximo_funcionario", "arredondamento_valores",
            "tempo_sessao_minutos", "tentativas_senha_bloqueio", "alertas_email", "alertas_whatsapp"
        ]

        # 1. Verifica se já existe configuração para este estabelecimento
        from sqlalchemy import text
        check_sql = "SELECT id FROM configuracoes WHERE estabelecimento_id = :eid LIMIT 1"
        existing = db.session.execute(text(check_sql), {"eid": estabelecimento_id}).fetchone()

        params = {"eid": estabelecimento_id}
        set_clauses = []
        
        # Prepara campos para Update/Insert
        for field in allowed_fields:
            if field in data:
                val = data[field]
                if field == "formas_pagamento" and isinstance(val, list):
                    val = json.dumps(val, ensure_ascii=False)
                
                params[field] = val
                set_clauses.append(f"{field} = :{field}")

        if not set_clauses:
             return jsonify({"success": True, "message": "Nada a atualizar"}), 200

        try:
            if existing:
                # UPDATE
                sql = f"UPDATE configuracoes SET {', '.join(set_clauses)} WHERE estabelecimento_id = :eid"
                db.session.execute(text(sql), params)
            else:
                # INSERT
                # Para insert precisamos garantir que colunas obrigatórias tenham valor ou default do banco assuma
                cols = ["estabelecimento_id"] + [k for k in params.keys() if k != "eid"]
                vals = [":eid"] + [f":{k}" for k in params.keys() if k != "eid"]
                
                sql = f"INSERT INTO configuracoes ({', '.join(cols)}) VALUES ({', '.join(vals)})"
                db.session.execute(text(sql), params)
            
            db.session.commit()
        except Exception as e_sql:
            # Se der erro (ex: coluna não existe), tentamos ignorar a coluna problemática?
            # Por enquanto, logamos e damos rollback. O try-catch externo pega.
            db.session.rollback()
            raise e_sql

        # Invalida o cache
        invalidate_config(estabelecimento_id)

        return jsonify({
            "success": True, 
            "message": "Configurações atualizadas com sucesso",
            "config": get_configuracao_safe(estabelecimento_id)
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em atualizar_configuracoes (SQL): {str(e)}")
        # Tenta retornar erro legível
        return jsonify({"success": False, "error": "Não foi possível salvar as configurações. Verifique o banco de dados."}), 500


# ==================== ESTABELECIMENTO ====================

@configuracao_bp.route("/estabelecimento", methods=["GET"])
@jwt_required()
def get_estabelecimento():
    """Retorna dados do estabelecimento com resiliência total"""
    try:
        claims = get_jwt()
        estabelecimento_id = get_authorized_establishment_id()
        
        dados = get_estabelecimento_full_safe(estabelecimento_id)

        if not dados:
            return jsonify({"success": False, "error": "Dados do estabelecimento não encontrados"}), 404

        return jsonify({
            "success": True, 
            "estabelecimento": dados
        }), 200

    except Exception as e:
        current_app.logger.error(f"❌ Erro em get_estabelecimento: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao carregar dados da empresa"}), 500


@configuracao_bp.route("/estabelecimentos", methods=["GET"])
@jwt_required()
def listar_estabelecimentos():
    """Lista todos os estabelecimentos - apenas para ADMIN (visão multi-loja)"""
    try:
        claims = get_jwt()
        role = claims.get("role", "").lower()

        if role not in ["admin", "dono"]:
            return jsonify({"success": False, "error": "Acesso restrito à administração"}), 403

        from sqlalchemy import text
        sql = text("""
            SELECT 
                e.id, e.nome_fantasia, e.razao_social, e.cnpj, e.telefone, e.email,
                e.logradouro, e.numero, e.bairro, e.cidade, e.estado, e.cep,
                e.ativo, e.regime_tributario,
                CAST(e.data_abertura AS TEXT) as data_abertura,
                (SELECT COUNT(*) FROM funcionarios f WHERE f.estabelecimento_id = e.id AND f.ativo = TRUE) as total_funcionarios,
                (SELECT COUNT(*) FROM produtos p WHERE p.estabelecimento_id = e.id AND p.ativo = TRUE) as total_produtos,
                (SELECT COUNT(*) FROM clientes c WHERE c.estabelecimento_id = e.id AND c.ativo = TRUE) as total_clientes,
                (SELECT COALESCE(SUM(v.total), 0) FROM vendas v WHERE v.estabelecimento_id = e.id AND v.status = 'finalizada') as faturamento_total,
                (SELECT CAST(MAX(v.data_venda) AS TEXT) FROM vendas v WHERE v.estabelecimento_id = e.id) as ultima_venda
            FROM estabelecimentos e
            ORDER BY e.id
        """)
        rows = db.session.execute(sql).fetchall()

        estabelecimentos = []
        for r in rows:
            estabelecimentos.append({
                "id": r[0],
                "nome_fantasia": r[1],
                "razao_social": r[2],
                "cnpj": r[3],
                "telefone": r[4],
                "email": r[5],
                "logradouro": r[6],
                "numero": r[7],
                "bairro": r[8],
                "cidade": r[9],
                "estado": r[10],
                "cep": r[11],
                "ativo": r[12],
                "regime_tributario": r[13],
                "data_abertura": r[14],
                "total_funcionarios": r[15] or 0,
                "total_produtos": r[16] or 0,
                "total_clientes": r[17] or 0,
                "faturamento_total": float(r[18]) if r[18] else 0.0,
                "ultima_venda": r[19],
            })

        return jsonify({"success": True, "estabelecimentos": estabelecimentos}), 200

    except Exception as e:
        current_app.logger.error(f"❌ Erro em listar_estabelecimentos: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao listar estabelecimentos"}), 500


@configuracao_bp.route("/estabelecimento", methods=["PUT"])
@jwt_required()
def update_estabelecimento():
    """Atualização segura do estabelecimento (Somente Admin/Dono)"""
    try:
        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()
        role = claims.get("role")
        is_super = claims.get("is_super_admin", False)
        
        if role not in ["admin", "dono", "ADMIN"] and not is_super:
            return jsonify({"success": False, "error": "Apenas proprietários podem alterar dados da empresa"}), 403

        data = request.get_json() or {}
        
        # Filtro de segurança: campos cadastrais e endereço completo
        campos_update = [
            "nome_fantasia", "razao_social", "telefone", "email", "inscricao_estadual",
            "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "estado"
        ]
        
        from sqlalchemy import text
        set_clauses = []
        params = {"eid": estabelecimento_id}
        
        for c in campos_update:
            if c in data:
                # Sanitização básica para CEP
                val = data[c]
                if c == "cep" and val:
                    val = "".join(filter(str.isdigit, str(val)))
                    if len(val) == 8:
                        val = f"{val[:5]}-{val[5:]}"
                
                set_clauses.append(f"{c} = :{c}")
                params[c] = val
        
        if set_clauses:
            sql = f"UPDATE estabelecimentos SET {', '.join(set_clauses)} WHERE id = :eid"
            current_app.logger.info(f"📊 [DATABASE] Executando Update Estabelecimento ID {estabelecimento_id}")
            current_app.logger.info(f"📊 [PAYLOAD] {params}")
            db.session.execute(text(sql), params)
            db.session.commit()
            current_app.logger.info(f"✅ [SUCCESS] Dados persistidos no banco.")

        return jsonify({
            "success": True, 
            "message": "Dados da empresa atualizados",
            "estabelecimento": get_estabelecimento_full_safe(estabelecimento_id)
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em update_estabelecimento: {str(e)}")
        return jsonify({"success": False, "error": "Falha ao atualizar dados"}), 500
        

# ==================== PREFERÊNCIAS DO USUÁRIO ====================

@configuracao_bp.route("/preferencias", methods=["GET", "PUT"])
@jwt_required()
def preferencias_usuario():
    """
    Gerencia preferências pessoais do usuário (tema, notificações, etc)
    Qualquer usuário pode alterar suas próprias preferências
    """
    try:
        claims = get_jwt()
        user_id = claims.get("sub") or get_jwt_identity()
        estabelecimento_id = get_authorized_establishment_id()
        
        if request.method == "GET":
            try:
                from sqlalchemy import text
                sql = """
                SELECT tema_escuro_pessoal, notificacoes_desktop_pessoal, idioma_pessoal 
                FROM funcionarios_preferencias 
                WHERE funcionario_id = :uid
                """
                result = db.session.execute(text(sql), {"uid": user_id}).fetchone()
            except Exception as e_sql:
                current_app.logger.warning(f"Erro ao buscar preferências (tabela pode não existir): {str(e_sql)}")
                result = None
            
            if result:
                return jsonify({
                    "success": True,
                    "preferencias": {
                        "tema_escuro": result[0],
                        "notificacoes_desktop": result[1],
                        "idioma": result[2] or "pt-BR"
                    }
                }), 200
            else:
                # Retorna preferências padrão
                return jsonify({
                    "success": True,
                    "preferencias": {
                        "tema_escuro": False,
                        "notificacoes_desktop": True,
                        "idioma": "pt-BR"
                    }
                }), 200
        
        elif request.method == "PUT":
            # Atualizar preferências do usuário
            data = request.get_json() or {}
            
            # Campos permitidos para preferências pessoais
            allowed_fields = ["tema_escuro", "notificacoes_desktop", "idioma"]
            
            from sqlalchemy import text
            
            # Verifica se já existe registro de preferências
            check_sql = "SELECT funcionario_id FROM funcionarios_preferencias WHERE funcionario_id = :uid"
            existing = db.session.execute(text(check_sql), {"uid": user_id}).fetchone()
            
            params = {"uid": user_id}
            set_clauses = []
            
            # Prepara campos para Update/Insert
            for field in allowed_fields:
                if field in data:
                    val = data[field]
                    params[field] = val
                    set_clauses.append(f"{field}_pessoal = :{field}")
            
            if not set_clauses:
                return jsonify({"success": True, "message": "Nada a atualizar"}), 200
            
            if existing:
                # Update
                sql = f"UPDATE funcionarios_preferencias SET {', '.join(set_clauses)} WHERE funcionario_id = :uid"
                db.session.execute(text(sql), params)
            else:
                # Insert com valores padrão para campos não fornecidos
                all_params = {
                    "uid": user_id,
                    "tema_escuro": data.get("tema_escuro", False),
                    "notificacoes_desktop": data.get("notificacoes_desktop", True),
                    "idioma": data.get("idioma", "pt-BR")
                }
                sql = """
                INSERT INTO funcionarios_preferencias 
                (funcionario_id, tema_escuro_pessoal, notificacoes_desktop_pessoal, idioma_pessoal)
                VALUES (:uid, :tema_escuro, :notificacoes_desktop, :idioma)
                """
                db.session.execute(text(sql), all_params)
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Preferências atualizadas com sucesso"
            }), 200
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em preferencias_usuario: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao atualizar preferências"}), 500


# ==================== LOGO UPLOAD ====================

@configuracao_bp.route("/logo", methods=["POST"])
@jwt_required()
def upload_logo():
    """Realiza o upload da logo e salva como Base64 (Máxima Portabilidade) - Apenas ADMIN/GERENTE"""
    try:
        from app.utils.query_helpers import get_authorized_establishment_id
        estabelecimento_id = get_authorized_establishment_id()
        user_role = claims.get("role", "").lower()
        
        # Verificação de permissão - apenas ADMIN e GERENTE podem fazer upload
        if user_role not in ["admin", "gerente"]:
            return jsonify({
                "success": False, 
                "error": "Acesso negado. Apenas administradores e gerentes podem alterar a logo."
            }), 403
        
        if 'logo' not in request.files:
            return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
            
        file = request.files['logo']
        if file.filename == '':
            return jsonify({"success": False, "error": "Arquivo vazio"}), 400

        # Validação do tipo de arquivo
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({"success": False, "error": "Tipo de arquivo não permitido. Use PNG, JPG, JPEG, GIF ou WebP."}), 400

        # Validação do tamanho (máximo 5MB)
        file.seek(0, 2)  # Move para o fim
        file_size = file.tell()
        file.seek(0)  # Volta para o início
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({"success": False, "error": "Arquivo muito grande. Tamanho máximo: 5MB"}), 400

        # Converte para Base64 para salvar no banco
        import base64
        file_content = file.read()
        mime_type = file.content_type or "image/png"
        base64_data = f"data:{mime_type};base64,{base64.b64encode(file_content).decode()}"

        from sqlalchemy import text
        
        # Verifica se existe config
        check_sql = "SELECT id FROM configuracoes WHERE estabelecimento_id = :eid LIMIT 1"
        existing = db.session.execute(text(check_sql), {"eid": estabelecimento_id}).fetchone()

        if existing:
            sql = "UPDATE configuracoes SET logo_base64 = :img, logo_url = :img WHERE estabelecimento_id = :eid"
            db.session.execute(text(sql), {"img": base64_data, "eid": estabelecimento_id})
        else:
            sql = "INSERT INTO configuracoes (estabelecimento_id, logo_base64, logo_url) VALUES (:eid, :img, :img)"
            db.session.execute(text(sql), {"eid": estabelecimento_id, "img": base64_data})

        db.session.commit()
        invalidate_config(estabelecimento_id)

        return jsonify({
            "success": True, 
            "logo_url": base64_data,
            "message": "Logo atualizada com sucesso"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Erro em upload_logo: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
