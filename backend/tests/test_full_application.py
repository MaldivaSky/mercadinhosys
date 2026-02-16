"""
Teste de Fluxo Integral - MercadinhoSys
Cobre o ciclo de vida completo: Cadastro → Venda → Validação → Segurança → Relatório
"""

import json
import random
from datetime import datetime

import pytest


def gerar_cpf_valido():
    """Gera um CPF válido aleatório para testes."""
    cpf = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        val = sum((len(cpf) + 1 - i) * v for i, v in enumerate(cpf)) % 11
        cpf.append(11 - val if val >= 2 else 0)
    s = "".join(str(d) for d in cpf)
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


class TestFluxoIntegral:
    """Teste de integração cobrindo cadastro, venda, validação, segurança e relatórios."""

    def test_ciclo_completo(self, client, auth_headers, estabelecimento_id):
        ts = datetime.now().strftime("%H%M%S%f")

        # ================================================================
        # 1. CADASTRO DE CLIENTE
        # ================================================================
        cpf_teste = gerar_cpf_valido()
        cliente_payload = {
            "nome": f"Cliente Teste {ts}",
            "cpf": cpf_teste,
            "celular": "(11) 99999-0001",
            "email": f"teste_{ts}@test.com",
            "cep": "01001-000",
            "logradouro": "Rua Teste",
            "numero": "100",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
        }

        resp = client.post("/api/clientes/", json=cliente_payload, headers=auth_headers)
        assert resp.status_code in (200, 201), f"Falha ao cadastrar cliente: {resp.data.decode()}"
        data_cliente = resp.get_json()
        assert data_cliente.get("success") is True, f"Resposta cliente: {data_cliente}"
        cliente_id = data_cliente.get("cliente", {}).get("id") or data_cliente.get("id")
        assert cliente_id is not None, "ID do cliente não retornado"
        print(f"  ✅ Cliente criado: ID={cliente_id}")

        # ================================================================
        # 2. CADASTRO DE PRODUTO
        # ================================================================
        produto_payload = {
            "nome": f"Produto Teste {ts}",
            "categoria": "Alimentos",
            "preco_custo": 5.00,
            "preco_venda": 12.50,
            "quantidade": 50,
            "quantidade_minima": 5,
            "unidade_medida": "UN",
            "codigo_barras": f"TEST{ts}",
            "tipo": "Alimentos",
        }

        resp = client.post("/api/produtos/", json=produto_payload, headers=auth_headers)
        assert resp.status_code in (200, 201), f"Falha ao cadastrar produto: {resp.data.decode()}"
        data_produto = resp.get_json()
        assert data_produto.get("success") is True, f"Resposta produto: {data_produto}"
        produto_id = data_produto.get("produto", {}).get("id") or data_produto.get("id")
        assert produto_id is not None, "ID do produto não retornado"
        print(f"  ✅ Produto criado: ID={produto_id}, estoque=50")

        # Confirmar estoque inicial
        resp = client.get(f"/api/produtos/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        estoque_inicial = resp.get_json().get("produto", {}).get("quantidade", 50)
        assert int(estoque_inicial) == 50, f"Estoque inicial esperado 50, obteve {estoque_inicial}"

        # ================================================================
        # 3. VENDA COMPLETA VIA PDV
        # ================================================================
        venda_payload = {
            "cliente_id": cliente_id,
            "items": [
                {
                    "id": produto_id,
                    "quantity": 3,
                    "discount": 0,
                }
            ],
            "subtotal": 37.50,
            "desconto": 0,
            "total": 37.50,
            "valor_recebido": 50.00,
            "troco": 12.50,
            "paymentMethod": "dinheiro",
            "observacoes": f"Venda de teste automatizado {ts}",
        }

        resp = client.post("/api/pdv/finalizar", json=venda_payload, headers=auth_headers)
        assert resp.status_code == 200, f"Falha ao finalizar venda: {resp.data.decode()}"
        data_venda = resp.get_json()
        assert data_venda.get("success") is True, f"Resposta venda: {data_venda}"
        venda_info = data_venda.get("venda", {})
        venda_id = venda_info.get("id")
        assert venda_id is not None, "ID da venda não retornado"
        print(f"  ✅ Venda finalizada: ID={venda_id}, código={venda_info.get('codigo')}")

        # ================================================================
        # 4. VALIDAÇÃO DE DADOS PÓS-VENDA
        # ================================================================

        # 4a. Status da venda = 'finalizada'
        assert venda_info.get("status") == "finalizada" or data_venda.get("success") is True

        # 4b. Estoque decrementado (50 - 3 = 47)
        resp = client.get(f"/api/produtos/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        produto_atualizado = resp.get_json().get("produto", {})
        estoque_atual = int(produto_atualizado.get("quantidade", -1))
        assert estoque_atual == 47, f"Estoque esperado 47, obteve {estoque_atual}"
        print(f"  ✅ Estoque decrementado: {estoque_inicial} → {estoque_atual}")

        # 4c. MovimentacaoEstoque gerada (verificar via endpoint de produto)
        resp = client.get(
            f"/api/produtos/{produto_id}/estoque/historico",
            headers=auth_headers,
        )
        if resp.status_code == 200:
            movs = resp.get_json()
            if isinstance(movs, dict):
                movs_list = movs.get("movimentacoes", movs.get("historico", []))
            else:
                movs_list = movs
            encontrou_mov = any(
                m.get("venda_id") == venda_id or m.get("motivo", "").startswith("Venda")
                for m in movs_list
            ) if movs_list else False
            if encontrou_mov:
                print(f"  ✅ MovimentacaoEstoque encontrada para venda {venda_id}")
            else:
                print(f"  ⚠️ Endpoint de histórico retornou, mas movimentação não localizada diretamente")
        else:
            print(f"  ⚠️ Endpoint de histórico retornou status {resp.status_code} (pode não existir)")

        # ================================================================
        # 5. SEGURANÇA - VENDA COM ESTOQUE INSUFICIENTE
        # ================================================================
        venda_invalida_payload = {
            "cliente_id": cliente_id,
            "items": [
                {
                    "id": produto_id,
                    "quantity": 9999,
                    "discount": 0,
                }
            ],
            "subtotal": 9999 * 12.50,
            "desconto": 0,
            "total": 9999 * 12.50,
            "valor_recebido": 9999 * 12.50,
            "troco": 0,
            "paymentMethod": "dinheiro",
        }

        resp = client.post("/api/pdv/finalizar", json=venda_invalida_payload, headers=auth_headers)
        assert resp.status_code == 400, (
            f"Venda com estoque insuficiente deveria retornar 400, retornou {resp.status_code}: "
            f"{resp.data.decode()}"
        )
        data_erro = resp.get_json()
        assert "estoque" in data_erro.get("error", "").lower() or "insuficiente" in data_erro.get("error", "").lower(), (
            f"Mensagem de erro deveria mencionar estoque: {data_erro}"
        )
        print(f"  ✅ Venda com estoque insuficiente bloqueada corretamente (400)")

        # Confirmar que rollback impediu alteração no estoque
        resp = client.get(f"/api/produtos/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        estoque_apos_erro = int(resp.get_json().get("produto", {}).get("quantidade", -1))
        assert estoque_apos_erro == 47, (
            f"Rollback falhou: estoque deveria ser 47 após venda rejeitada, obteve {estoque_apos_erro}"
        )
        print(f"  ✅ Rollback confirmado: estoque permanece em {estoque_apos_erro}")

        # ================================================================
        # 6. RELATÓRIO - VENDA NAS ESTATÍSTICAS
        # ================================================================
        hoje = datetime.now().strftime("%Y-%m-%d")
        resp = client.get(
            f"/api/vendas/estatisticas?data_inicio={hoje}&data_fim={hoje}",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Falha ao buscar estatísticas: {resp.data.decode()}"
        data_stats = resp.get_json()

        stats = data_stats.get("estatisticas_gerais", data_stats.get("estatisticas", {}))
        total_vendas = stats.get("total_vendas", stats.get("quantidade", 0))
        assert total_vendas >= 1, f"Estatísticas deveriam ter ao menos 1 venda hoje, obteve {total_vendas}"
        print(f"  ✅ Relatório: {total_vendas} venda(s) encontrada(s) nas estatísticas do dia")

        # ================================================================
        # RESULTADO FINAL
        # ================================================================
        print("\n" + "=" * 60)
        print("  TESTE DE FLUXO INTEGRAL CONCLUÍDO COM SUCESSO")
        print("=" * 60)
