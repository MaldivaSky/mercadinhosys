import pandas as pd
import io
import re
from werkzeug.datastructures import FileStorage

def normalize_header(header):
    """
    Normaliza o cabeçalho para snake_case e remove acentos/caracteres especiais.
    Ex: "Código de Barras" -> "codigo_de_barras"
    """
    import unicodedata
    
    # Remove acentos
    nfkd_form = unicodedata.normalize('NFKD', header)
    header_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Converte para minúsculas e substitui espaços/hifens por underscore
    header_clean = header_ascii.lower().strip()
    header_clean = re.sub(r'[\s\-]+', '_', header_clean)
    
    # Remove caracteres não alfanuméricos exceto underscore
    header_clean = re.sub(r'[^a-z0-9_]', '', header_clean)
    
    return header_clean

def read_import_file(file: FileStorage):
    """
    Lê um arquivo CSV ou Excel e retorna um DataFrame pandas.
    """
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            # Tenta diferentes encodings
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, encoding='latin1')
                
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            raise ValueError("Formato de arquivo não suportado. Use CSV ou Excel (.xlsx).")
            
        # Normaliza cabeçalhos
        df.columns = [normalize_header(col) for col in df.columns]
        
        # Remove linhas vazias
        df.dropna(how='all', inplace=True)
        
        # Converte NaN para None (null no JSON/Python)
        df = df.where(pd.notnull(df), None)
        
        return df.to_dict(orient='records')
        
    except Exception as e:
        raise ValueError(f"Erro ao ler arquivo: {str(e)}")
