"""
Módulo de padronização de respostas da API
"""
from flask import jsonify
from typing import Any, Dict, Optional
from datetime import datetime, timezone

class APIResponse:
    """Padroniza respostas da API"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Sucesso", status_code: int = 200):
        """Resposta de sucesso"""
        return jsonify({
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), status_code
    
    @staticmethod
    def error(error_code: str, message: str, details: Optional[Dict] = None, status_code: int = 400):
        """Resposta de erro"""
        return jsonify({
            "success": False,
            "error": error_code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), status_code
    
    @staticmethod
    def paginated(items: list, page: int, per_page: int, total: int, status_code: int = 200):
        """Resposta paginada"""
        return jsonify({
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), status_code
