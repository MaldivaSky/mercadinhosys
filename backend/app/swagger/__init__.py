"""
app/swagger/__init__.py
Configuração do Swagger para documentação da API
"""

from flasgger import Swagger

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/api/docs/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/api/docs/static",
    "swagger_ui": True,
    "specs_route": "/api/docs/",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "MercadinhoSys API",
        "description": "API completa para gestão de mercadinhos e estabelecimentos comerciais",
        "contact": {
            "name": "MaldivaSky Tech",
            "email": "suporte@maldivas.tech",
        },
        "version": "2.0.0",
    },
    "basePath": "/api",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header usando Bearer scheme. Exemplo: 'Bearer {token}'",
        }
    },
    "security": [{"Bearer": []}],
    "tags": [
        {"name": "Auth", "description": "Autenticação e autorização"},
        {"name": "Produtos", "description": "Gestão de produtos e estoque"},
        {"name": "Vendas", "description": "PDV e gestão de vendas"},
        {"name": "Clientes", "description": "Gestão de clientes"},
        {"name": "Funcionários", "description": "Gestão de funcionários"},
        {"name": "Fornecedores", "description": "Gestão de fornecedores"},
        {"name": "Dashboard", "description": "Métricas e analytics"},
        {"name": "Relatórios", "description": "Relatórios gerenciais"},
        {"name": "Configuração", "description": "Configurações do sistema"},
        {"name": "Despesas", "description": "Gestão de despesas"},
    ],
}


def init_swagger(app):
    """Inicializa o Swagger no app"""
    return Swagger(app, config=swagger_config, template=swagger_template)
