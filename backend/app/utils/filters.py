# app/utils/filters.py
class QueryFilter:
    """
    Classe para aplicar filtros dinâmicos baseados em parâmetros de query
    Suporta: equals, contains, gt/lt, between, in_array
    """

    @staticmethod
    def apply_filters(model, query, filter_params):
        # Exemplo: ?categoria=Alimentos&preco_min=10&nome__contains=arroz
        pass
        for param, value in filter_params.items():
            if "__" in param:
                field_name, operation = param.split("__", 1)
            else:
                field_name, operation = param, "equals"

            column = getattr(model, field_name, None)
            if not column:
                continue  # Ignorar campos inválidos

            if operation == "equals":
                query = query.filter(column == value)
            elif operation == "contains":
                query = query.filter(column.ilike(f"%{value}%"))
            elif operation == "gt":
                query = query.filter(column > value)
            elif operation == "lt":
                query = query.filter(column < value)
            elif operation == "between":
                min_val, max_val = value.split(",")
                query = query.filter(column.between(min_val, max_val))
            elif operation == "in_array":
                values = value.split(",")
                query = query.filter(column.in_(values))

        return query