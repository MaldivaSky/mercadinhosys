"""
Testes para o sistema de paginação
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Adiciona o diretório backend ao path se necessário
backend_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


class TestPagination:
    """Testes para a classe Pagination"""

    def test_pagination_defaults(self):
        """Testa valores padrão da paginação"""
        from app.utils.pagination import Pagination

        # Mock da query e do request
        mock_query = Mock()
        mock_paginated = Mock()
        mock_paginated.items = []
        mock_paginated.page = 1
        mock_paginated.per_page = 20
        mock_paginated.pages = 1
        mock_paginated.total = 0
        mock_paginated.has_prev = False
        mock_paginated.has_next = False
        mock_paginated.prev_num = None
        mock_paginated.next_num = None

        mock_query.paginate.return_value = mock_paginated

        mock_request = Mock()
        mock_request.args.get.side_effect = lambda key, default, type=int: default

        with patch("app.utils.pagination.request", mock_request):
            paginator = Pagination(mock_query)
            result = paginator.paginate()

            assert paginator.page == 1
            assert paginator.per_page == 20
            assert "pagination" in result
            assert result["pagination"]["page"] == 1
            assert result["pagination"]["per_page"] == 20
            assert result["success"] is True

    def test_pagination_custom_params(self):
        """Testa parâmetros customizados"""
        from app.utils.pagination import Pagination

        mock_query = Mock()
        mock_paginated = Mock()
        mock_paginated.items = []
        mock_paginated.page = 3
        mock_paginated.per_page = 50
        mock_paginated.pages = 5
        mock_paginated.total = 250
        mock_paginated.has_prev = True
        mock_paginated.has_next = True
        mock_paginated.prev_num = 2
        mock_paginated.next_num = 4

        mock_query.paginate.return_value = mock_paginated

        mock_request = Mock()
        mock_request.args.get.side_effect = lambda key, default, type=int: {
            "page": 3,
            "per_page": 50,
        }.get(key, default)

        with patch("app.utils.pagination.request", mock_request):
            paginator = Pagination(mock_query)
            result = paginator.paginate()

            assert paginator.page == 3
            assert paginator.per_page == 50
            assert result["pagination"]["total_items"] == 250

    def test_pagination_invalid_params(self):
        """Testa parâmetros inválidos"""
        from app.utils.pagination import Pagination

        mock_query = Mock()
        mock_paginated = Mock()
        mock_paginated.items = []
        mock_paginated.page = 1
        mock_paginated.per_page = 20
        mock_paginated.pages = 1
        mock_paginated.total = 0
        mock_paginated.has_prev = False
        mock_paginated.has_next = False
        mock_paginated.prev_num = None
        mock_paginated.next_num = None

        mock_query.paginate.return_value = mock_paginated

        mock_request = Mock()
        mock_request.args.get.side_effect = lambda key, default, type=int: {
            "page": 0,
            "per_page": -5,
        }.get(key, default)

        with patch("app.utils.pagination.request", mock_request):
            paginator = Pagination(mock_query)
            result = paginator.paginate()

            # Deve corrigir valores inválidos
            assert paginator.page == 1  # 0 → 1
            assert paginator.per_page == 20  # -5 → 20

    def test_pagination_max_per_page(self):
        """Testa limite máximo de itens por página"""
        from app.utils.pagination import Pagination

        mock_query = Mock()
        mock_paginated = Mock()
        mock_paginated.items = []
        mock_paginated.page = 1
        mock_paginated.per_page = 100
        mock_paginated.pages = 1
        mock_paginated.total = 0
        mock_paginated.has_prev = False
        mock_paginated.has_next = False
        mock_paginated.prev_num = None
        mock_paginated.next_num = None

        mock_query.paginate.return_value = mock_paginated

        mock_request = Mock()
        mock_request.args.get.side_effect = lambda key, default, type=int: {
            "per_page": 150
        }.get(key, default)

        with patch("app.utils.pagination.request", mock_request):
            paginator = Pagination(mock_query)
            result = paginator.paginate()

            assert paginator.per_page == 100  # Deve limitar a 100

    def test_pagination_with_items(self):
        """Testa paginação com itens contendo to_dict()"""
        from app.utils.pagination import Pagination

        # Mock de items com método to_dict()
        mock_item1 = Mock()
        mock_item1.to_dict.return_value = {"id": 1, "nome": "Item 1"}
        mock_item2 = Mock()
        mock_item2.to_dict.return_value = {"id": 2, "nome": "Item 2"}

        mock_query = Mock()
        mock_paginated = Mock()
        mock_paginated.items = [mock_item1, mock_item2]
        mock_paginated.page = 1
        mock_paginated.per_page = 20
        mock_paginated.pages = 1
        mock_paginated.total = 2
        mock_paginated.has_prev = False
        mock_paginated.has_next = False
        mock_paginated.prev_num = None
        mock_paginated.next_num = None

        mock_query.paginate.return_value = mock_paginated

        mock_request = Mock()
        mock_request.args.get.side_effect = lambda key, default, type=int: default

        with patch("app.utils.pagination.request", mock_request):
            paginator = Pagination(mock_query)
            result = paginator.paginate()

            assert len(result["data"]) == 2
            assert result["data"][0]["id"] == 1
            assert result["meta"]["items_count"] == 2


def test_paginate_query_function():
    """Testa a função auxiliar paginate_query"""
    from app.utils.pagination import paginate_query

    mock_query = Mock()
    mock_paginated = Mock()
    mock_paginated.items = []
    mock_paginated.page = 1
    mock_paginated.per_page = 20
    mock_paginated.pages = 1
    mock_paginated.total = 0
    mock_paginated.has_prev = False
    mock_paginated.has_next = False
    mock_paginated.prev_num = None
    mock_paginated.next_num = None

    mock_query.paginate.return_value = mock_paginated

    mock_request = Mock()
    mock_request.args.get.side_effect = lambda key, default, type=int: default

    with patch("app.utils.pagination.request", mock_request):
        result = paginate_query(mock_query)

        assert "success" in result
        assert "data" in result
        assert "pagination" in result
        assert result["success"] is True


def test_get_pagination_params():
    """Testa a função get_pagination_params"""
    from app.utils.pagination import get_pagination_params

    mock_request = Mock()
    mock_request.args.get.side_effect = lambda key, default, type=int: {
        "page": 2,
        "per_page": 30,
    }.get(key, default)

    with patch("app.utils.pagination.request", mock_request):
        page, per_page, offset = get_pagination_params()

        assert page == 2
        assert per_page == 30
        assert offset == 30  # (2-1) * 30


def test_get_pagination_params_defaults():
    """Testa get_pagination_params com valores padrão"""
    from app.utils.pagination import get_pagination_params

    mock_request = Mock()
    mock_request.args.get.side_effect = lambda key, default, type=int: default

    with patch("app.utils.pagination.request", mock_request):
        page, per_page, offset = get_pagination_params()

        assert page == 1
        assert per_page == 20
        assert offset == 0


def test_get_pagination_params_max_limit():
    """Testa limite máximo em get_pagination_params"""
    from app.utils.pagination import get_pagination_params

    mock_request = Mock()
    mock_request.args.get.side_effect = lambda key, default, type=int: {
        "per_page": 200
    }.get(key, default)

    with patch("app.utils.pagination.request", mock_request):
        page, per_page, offset = get_pagination_params()

        assert per_page == 100  # Deve limitar a 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
