from app import create_app, db
from sqlalchemy import text

app = create_app()

def run_migration():
    with app.app_context():
        try:
            # Check if stripe_customer_id exists
            # We can just try to rename and catch error
            print("Renomeando stripe_customer_id para gateway_customer_id...")
            db.session.execute(text("ALTER TABLE estabelecimentos RENAME COLUMN stripe_customer_id TO gateway_customer_id"))
            db.session.commit()
            print("Coluna stripe_customer_id renomeada com sucesso.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ou coluna já renomeada: {e}")

        try:
            print("Renomeando stripe_subscription_id para gateway_subscription_id...")
            db.session.execute(text("ALTER TABLE estabelecimentos RENAME COLUMN stripe_subscription_id TO gateway_subscription_id"))
            db.session.commit()
            print("Coluna stripe_subscription_id renomeada com sucesso.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ou coluna já renomeada: {e}")

if __name__ == '__main__':
    run_migration()
