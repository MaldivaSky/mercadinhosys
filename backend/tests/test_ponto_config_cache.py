"""
Regressão: obter_configuracao_com_cache NÃO pode cachear a instância ORM entre
requests. Cachear a instância causava
    "Instance <ConfiguracaoHorario> is not bound to a Session"
ao acessar atributos numa request posterior (sessão original já fechada). O fix
cacheia o ID e re-liga via db.session.get() na sessão ativa.

Este teste reproduz o cenário exato: 1ª chamada popula o cache, encerramos a
sessão (como no fim de uma request), e a 2ª chamada (cache hit) deve permitir
acesso a atributo SEM DetachedInstanceError.
"""
from app.models import db, Estabelecimento, ConfiguracaoHorario


def test_config_cache_rebinds_apos_fim_de_request(session):
    import app.routes.ponto as ponto

    # Captura o ID como int puro — depois de remover a sessão qualquer instância
    # do fixture também estaria detached (isso é do teste, não do produto).
    estab_id = int(session.query(Estabelecimento).first().id)

    # Limpa cache de módulo p/ o teste ser determinístico
    ponto._config_id_cache.clear()
    ponto._config_cache_time.clear()

    cfg = ConfiguracaoHorario(estabelecimento_id=estab_id, exigir_foto=False, exigir_localizacao=False)
    session.add(cfg)
    session.commit()

    # 1ª chamada (cache miss): busca e guarda o ID
    c1 = ponto.obter_configuracao_com_cache(estab_id)
    assert c1 is not None
    assert c1.exigir_foto is False

    # Simula o fim de uma request: as instâncias viram "detached".
    db.session.expire_all()
    db.session.remove()

    # 2ª chamada (cache hit pelo ID): deve re-ligar à sessão ativa e permitir
    # acesso a atributo sem lançar DetachedInstanceError. Este acesso é o que
    # quebrava antes.
    c2 = ponto.obter_configuracao_com_cache(estab_id)
    assert c2 is not None
    assert c2.exigir_foto is False
    assert c2.exigir_localizacao is False
