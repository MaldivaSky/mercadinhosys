# app/utils/auth_utils.py
"""
Centralização de Lógica de Autenticação e Autorização - MercadinhoSys
Evita discrepâncias entre decoradores e garante normalização de status.
"""

def normalize_status(raw_status):
    """
    Normaliza o status do usuário para 'ativo' em caso de valores None, nulos ou vazios.
    Utilizando em decoradores JWT e RBAC.
    """
    if not raw_status:
        return "ativo"
    
    status_str = str(raw_status).lower().strip()
    if status_str in ["none", "null", "", "undefined"]:
        return "ativo"
    
    return status_str

def is_user_active(status):
    """Verifica se o status normalizado é considerado ativo"""
    return normalize_status(status) in ["ativo", "active"]

def get_doctor_info(current_user_id, claims):
    """Gera informações de diagnóstico para o endpoint doctor"""
    raw_status = claims.get("status")
    normalized = normalize_status(raw_status)
    
    return {
        "status": "ready",
        "fingerprint": "MERCADINHOV2_2026_MARCH_15_V1",
        "user_context": {
            "id": current_user_id,
            "raw_status": raw_status,
            "normalized_status": normalized,
            "role": claims.get("role"),
            "establishment_id": claims.get("estabelecimento_id"),
            "is_super_admin": claims.get("is_super_admin", False)
        }
    }
