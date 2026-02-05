from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import create_engine, text
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
            conn.execute(text("SELECT 1"))

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
        db_url = (
            current_app.config.get("SQLALCHEMY_DATABASE_URI")
            or os.environ.get("NEON_DATABASE_URL")
            or os.environ.get("DATABASE_URL")
            or ""
        )
        local_counts = {}
        for model in [Estabelecimento, Funcionario, Cliente, Fornecedor, CategoriaProduto, Produto, Venda, VendaItem, Pagamento, MovimentacaoEstoque, Despesa]:
            try:
                local_counts[model.__tablename__] = db.session.query(model).count()
            except Exception:
                local_counts[model.__tablename__] = None
        neon_status = "desabilitado"
        remote_counts = None
        if db_url.startswith(("postgresql://", "postgres://")):
            try:
                engine = create_engine(db_url.replace("postgres://", "postgresql://", 1))
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                neon_status = "online"
                remote_counts = {}
                with engine.connect() as conn:
                    for model in [Estabelecimento, Funcionario, Cliente, Fornecedor, CategoriaProduto, Produto, Venda, VendaItem, Pagamento, MovimentacaoEstoque, Despesa]:
                        try:
                            table = model.__tablename__
                            result = conn.execute(text(f'SELECT COUNT(*) AS c FROM "{table}"'))
                            count = result.scalar()
                            remote_counts[table] = int(count) if count is not None else 0
                        except Exception:
                            remote_counts[model.__tablename__] = None
            except Exception as e:
                neon_status = f"offline: {str(e)[:80]}"
        return jsonify({"success": True, "neon": neon_status, "local_counts": local_counts, "remote_counts": remote_counts}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)[:120]}), 500


@sync_bp.route("/api/sync/db-info", methods=["GET"])
def db_info():
    try:
        uri = current_app.config.get("SQLALCHEMY_DATABASE_URI") or ""
        engine = db.engine
        engine_name = getattr(engine, "name", "unknown")
        is_sqlite = engine_name == "sqlite" or uri.startswith("sqlite://")
        file_exists = None
        file_path = None
        if is_sqlite:
            if uri.startswith("sqlite:///"):
                rel = uri.replace("sqlite:///", "", 1)
                file_path = os.path.abspath(os.path.join(os.getcwd(), rel))
                file_exists = os.path.exists(file_path)
        return jsonify({
            "success": True,
            "uri": uri,
            "engine": engine_name,
            "sqlite_file_path": file_path,
            "sqlite_file_exists": file_exists,
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)[:120]}), 500
