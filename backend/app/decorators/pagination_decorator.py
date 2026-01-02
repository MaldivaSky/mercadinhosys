"""
Decorator para aplicar paginação automaticamente em endpoints
"""

from functools import wraps
from flask import request, jsonify
from app.utils.pagination import Pagination


def paginated_response(schema=None, max_per_page=100):
    """
    Decorator para endpoints que retornam listas paginadas

    Args:
        schema: Marshmallow schema para serialização
        max_per_page: Número máximo de itens por página
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Executar a função original para obter a query
                result = f(*args, **kwargs)

                # Se a função retornou uma resposta Flask diretamente
                if isinstance(result, tuple) and len(result) == 2:
                    response, status_code = result
                    if isinstance(response, dict) and "data" in response:
                        # Já é uma resposta paginada
                        return jsonify(response), status_code

                # Caso contrário, assumir que result é uma query
                query = result

                # Criar paginação
                paginator = Pagination(query, schema)
                paginator.max_per_page = max_per_page

                return jsonify(paginator.paginate()), 200

            except Exception as e:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Erro na paginação",
                            "message": str(e),
                        }
                    ),
                    500,
                )

        return decorated_function

    return decorator


def paginated_list(model, schema=None, filters=None, order_by=None):
    """
    Decorator para endpoints de listagem simples

    Args:
        model: Modelo SQLAlchemy
        schema: Marshmallow schema
        filters: Filtros a aplicar (dict)
        order_by: Campo para ordenação
    """

    def decorator(f):
        @wraps(f)
        @paginated_response(schema)
        def decorated_function(*args, **kwargs):
            try:
                # Aplicar filtros básicos
                query = model.query

                # Aplicar filtros adicionais da função decorada
                if filters:
                    for key, value in filters.items():
                        if hasattr(model, key):
                            query = query.filter(getattr(model, key) == value)

                # Aplicar ordenação
                if order_by and hasattr(model, order_by):
                    query = query.order_by(getattr(model, order_by).desc())

                return query
            except Exception as e:
                raise Exception(f"Erro ao criar query: {str(e)}")

        return decorated_function

    return decorator
