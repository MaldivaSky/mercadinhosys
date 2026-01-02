"""
Sistema de paginação reutilizável para todos os endpoints
"""

from flask import request, jsonify
from math import ceil


class Pagination:
    """Classe para gerenciar paginação de resultados"""

    def __init__(self, query, schema=None):
        """
        Inicializa o objeto de paginação

        Args:
            query: Query SQLAlchemy a ser paginada
            schema: Marshmallow schema para serialização (opcional)
        """
        self.query = query
        self.schema = schema
        self.page = 1
        self.per_page = 20
        self.max_per_page = 100

    def paginate(self):
        """Aplica paginação na query e retorna os resultados paginados"""
        # Obter parâmetros da requisição
        self.page = request.args.get("page", 1, type=int)
        self.per_page = request.args.get("per_page", 20, type=int)

        # Validar parâmetros
        if self.page < 1:
            self.page = 1
        if self.per_page < 1:
            self.per_page = 20
        if self.per_page > self.max_per_page:
            self.per_page = self.max_per_page

        # Aplicar paginação
        paginated = self.query.paginate(
            page=self.page, per_page=self.per_page, error_out=False
        )

        return self._format_response(paginated)

    def _format_response(self, paginated):
        """Formata a resposta padronizada"""
        items = paginated.items

        # Serializar items se houver schema
        if self.schema:
            data = self.schema.dump(items, many=True)
        else:
            # Usar método to_dict() se disponível, senão usar dict()
            data = [
                item.to_dict() if hasattr(item, "to_dict") else vars(item)
                for item in items
            ]

        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": paginated.page,
                "per_page": paginated.per_page,
                "total_pages": paginated.pages,
                "total_items": paginated.total,
                "has_prev": paginated.has_prev,
                "has_next": paginated.has_next,
                "prev_page": paginated.prev_num if paginated.has_prev else None,
                "next_page": paginated.next_num if paginated.has_next else None,
            },
            "meta": {
                "items_count": len(items),
                "showing": f"{((paginated.page - 1) * paginated.per_page) + 1} to {min(paginated.page * paginated.per_page, paginated.total)} of {paginated.total}",
            },
        }


def paginate_query(query, schema=None):
    """
    Função auxiliar para paginação rápida

    Args:
        query: Query SQLAlchemy
        schema: Marshmallow schema (opcional)

    Returns:
        dict: Resposta paginada padronizada
    """
    paginator = Pagination(query, schema)
    return paginator.paginate()


def get_pagination_params():
    """
    Retorna os parâmetros de paginação da requisição atual

    Returns:
        tuple: (page, per_page, offset)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    if per_page > 100:
        per_page = 100

    offset = (page - 1) * per_page
    return page, per_page, offset
