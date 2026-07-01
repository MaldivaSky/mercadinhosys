import os
from datetime import date

from app.models import Despesa, Estabelecimento, SyncQueue, get_model_by_table
from app.routes.sync_cloud import _process_sync_data
from app.services.sync_worker import GuerrillaSyncWorker


def test_get_model_by_table_mapeia_tabelas_criticas():
    tabelas_criticas = [
        "pagamentos",
        "despesas",
        "contas_pagar",
        "movimentacoes_caixa",
        "motoristas",
        "veiculos",
        "entregas",
        "taxas_entrega",
    ]

    for tabela in tabelas_criticas:
        assert get_model_by_table(tabela) is not None, f"Tabela nao mapeada: {tabela}"


def test_sync_queue_monta_payload_compativel():
    item = SyncQueue(
        estabelecimento_id=1,
        tabela="despesas",
        registro_id=99,
        operacao="insert",
        payload_json='{"descricao":"Internet","valor":199.9}',
    )

    payload = item.to_sync_payload()

    assert payload["tabela"] == "despesas"
    assert payload["registro_id"] == 99
    assert payload["operacao"] == "INSERT"
    assert payload["payload"]["descricao"] == "Internet"
    assert payload["payload"]["valor"] == 199.9


def test_worker_envia_payload_completo_para_cloud(app, monkeypatch):
    os.environ["CLOUD_SYNC_TOKEN"] = "token-teste"

    item = SyncQueue(
        estabelecimento_id=1,
        tabela="despesas",
        registro_id=99,
        operacao="update",
        payload_json='{"descricao":"Energia","valor":320.5}',
    )

    capturado = {}

    class FakeResponse:
        status_code = 200

    def fake_post(url, json, timeout, headers):
        capturado["url"] = url
        capturado["json"] = json
        capturado["headers"] = headers
        return FakeResponse()

    worker = GuerrillaSyncWorker(app)
    worker.cloud_api_url = "https://cloud.example"
    worker.sync_token = "token-teste"
    monkeypatch.setattr("app.services.sync_worker.requests.post", fake_post)

    assert worker.envio_para_nuvem(item) is True
    assert capturado["url"] == "https://cloud.example/api/sync/receive"
    assert capturado["json"]["operacao"] == "UPDATE"
    assert capturado["json"]["payload"]["descricao"] == "Energia"
    assert capturado["headers"]["Authorization"] == "Bearer token-teste"


def test_worker_nao_marca_sucesso_sem_config_cloud(app):
    item = SyncQueue(
        estabelecimento_id=1,
        tabela="despesas",
        registro_id=100,
        operacao="update",
        payload_json='{"descricao":"Agua","valor":88.0}',
    )

    worker = GuerrillaSyncWorker(app)
    worker.cloud_api_url = ""
    worker.sync_token = ""

    assert worker.envio_para_nuvem(item) is False


def test_cloud_receiver_processa_payload_json_fallback(session):
    estab = session.query(Estabelecimento).first()
    assert estab is not None

    data = {
        "tabela": "despesas",
        "operacao": "insert",
        "registro_id": 9001,
        "payload_json": (
            '{'
            f'"id":9001,'
            f'"estabelecimento_id":{estab.id},'
            '"descricao":"Internet Fibra",'
            '"categoria":"infraestrutura",'
            '"tipo":"fixa",'
            '"valor":199.90,'
            f'"data_despesa":"{date(2024, 1, 10).isoformat()}"'
            '}'
        ),
    }

    assert _process_sync_data(data, session) is True

    # Espelha tenant autenticado: Despesa tem estabelecimento_id e é filtrada.
    from flask import g, has_request_context
    if has_request_context():
        g.estabelecimento_id = estab.id
    despesa = session.query(Despesa).filter_by(id=9001).first()
    assert despesa is not None
    assert despesa.descricao == "Internet Fibra"
    assert float(despesa.valor) == 199.9
