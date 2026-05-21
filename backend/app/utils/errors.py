"""
Módulo de exceções customizadas da API
"""

class APIError(Exception):
    """Exceção base para erros da API"""
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class EstoqueInsuficienteError(APIError):
    """Erro quando não há estoque suficiente"""
    def __init__(self, produto_nome: str, disponivel: int, solicitado: int):
        super().__init__(
            code="ESTOQUE_INSUFICIENTE",
            message=f"Estoque insuficiente para {produto_nome}",
            status_code=400,
            details={
                "produto": produto_nome,
                "disponivel": disponivel,
                "solicitado": solicitado
            }
        )

class ClienteNaoEncontradoError(APIError):
    """Erro quando cliente não é encontrado"""
    def __init__(self, cliente_id: int):
        super().__init__(
            code="CLIENTE_NAO_ENCONTRADO",
            message=f"Cliente {cliente_id} não encontrado",
            status_code=404,
            details={"cliente_id": cliente_id}
        )

class CaixaFechadoError(APIError):
    """Erro quando caixa está fechado"""
    def __init__(self):
        super().__init__(
            code="CAIXA_FECHADO",
            message="Caixa está fechado. Abra o caixa antes de registrar vendas.",
            status_code=403
        )

class PagamentoInvalidoError(APIError):
    """Erro quando pagamento é inválido"""
    def __init__(self, total_esperado: float, total_recebido: float):
        super().__init__(
            code="PAGAMENTO_INVALIDO",
            message="Valor dos pagamentos não corresponde ao total da venda",
            status_code=400,
            details={
                "total_esperado": total_esperado,
                "total_recebido": total_recebido,
                "diferenca": abs(total_esperado - total_recebido)
            }
        )

class ProdutoNaoEncontradoError(APIError):
    """Erro quando produto não é encontrado"""
    def __init__(self, produto_id: int):
        super().__init__(
            code="PRODUTO_NAO_ENCONTRADO",
            message=f"Produto {produto_id} não encontrado",
            status_code=404,
            details={"produto_id": produto_id}
        )

class FiadoSemClienteError(APIError):
    """Erro quando tenta fazer fiado sem cliente"""
    def __init__(self):
        super().__init__(
            code="CLIENTE_OBRIGATORIO",
            message="Para vender no FIADO é obrigatório selecionar um cliente cadastrado.",
            status_code=400
        )
