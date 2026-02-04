from flask import Blueprint, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
from app.models import db, Estabelecimento, Funcionario, Cliente, Fornecedor, CategoriaProduto, Produto, Venda, VendaItem, Pagamento, MovimentacaoEstoque, Despesa

sync_bp = Blueprint("sync", __name__)


def _clone_data(instance):
    data = {}
    for col in instance.__table__.columns:
        data[col.name] = getattr(instance, col.name)
    return data


def _upsert(session, model, data, pk_field="id"):
    pk_value = data.get(pk_field)
    if pk_value is None:
        return False
    obj = session.query(model).get(pk_value)
    if obj:
        for k, v in data.items():
            setattr(obj, k, v)
        return True
    else:
        session.add(model(**data))
        return False


@sync_bp.route("/api/sync/replicar", methods=["POST"])
def replicar_para_neon():
    try:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return jsonify({"success": False, "message": "DATABASE_URL não configurada"}), 400

        engine = create_engine(db_url)
        # Teste de conexão
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        RemoteSession = sessionmaker(bind=engine)
        remote_session = RemoteSession()

        # Garantir schema
        db.metadata.create_all(engine)

        models = [
            Estabelecimento,
            Funcionario,
            Cliente,
            Fornecedor,
            CategoriaProduto,
            Produto,
            Venda,
            VendaItem,
            Pagamento,
            MovimentacaoEstoque,
            Despesa,
        ]

        since = request.args.get("since")
        resultado = {}
        for model in models:
            query = db.session.query(model)
            if since:
                try:
                    from datetime import datetime
                    since_dt = datetime.fromisoformat(since)
                except Exception:
                    return jsonify({"success": False, "message": "Parâmetro 'since' inválido"}), 400
                ts_field = None
                if hasattr(model, "updated_at"):
                    ts_field = getattr(model, "updated_at")
                elif hasattr(model, "created_at"):
                    ts_field = getattr(model, "created_at")
                if ts_field is not None:
                    query = query.filter(ts_field >= since_dt)
            rows = query.all()
            inseridos = 0
            atualizados = 0
            for r in rows:
                data = _clone_data(r)
                updated = _upsert(remote_session, model, data)
                if updated:
                    atualizados += 1
                else:
                    inseridos += 1
            remote_session.commit()
            resultado[model.__tablename__] = {
                "inseridos": inseridos,
                "atualizados": atualizados,
                "total_local": len(rows),
            }

        return jsonify({"success": True, "resultado": resultado}), 200

    except SQLAlchemyError as e:
        if 'remote_session' in locals():
            remote_session.rollback()
        return jsonify({"success": False, "message": f"Erro SQLAlchemy: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao replicar: {str(e)}"}), 500


@sync_bp.route("/api/sync/health", methods=["GET"])
def sync_health():
    try:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return jsonify({"success": True, "neon": "desabilitado"})
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return jsonify({"success": True, "neon": "online"}), 200
    except Exception as e:
        return jsonify({"success": True, "neon": f"offline: {str(e)[:80]}"}), 200
