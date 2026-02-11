
import sys
import os
from datetime import datetime, date, time, timedelta
import random

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import RegistroPonto, Funcionario, Estabelecimento

def fix_today_ponto():
    app = create_app()
    with app.app_context():
        print("🔧 Corrigindo registros de ponto de HOJE...")
        
        hoje = date.today()
        agora = datetime.now()
        
        # 1. Remover registros futuros de hoje (ou todos de hoje para recriar corretamente)
        print(f"🗑️  Removendo registros de ponto de {hoje}...")
        db.session.query(RegistroPonto).filter(RegistroPonto.data == hoje).delete()
        db.session.commit()
        
        # 2. Recriar registros respeitando o horário atual
        funcionarios = Funcionario.query.filter_by(ativo=True).all()
        estab = Estabelecimento.query.first()
        
        print(f"🕒 Horário atual: {agora.strftime('%H:%M')}")
        print(f"👥 Processando {len(funcionarios)} funcionários...")
        
        registros_criados = 0
        
        for func in funcionarios:
            # Entrada (08:00 +/- variavel)
            # Se agora já passou das 08:00 (considerando atrasos até 09:00)
            hora_entrada_base = datetime.combine(hoje, time(8, 0))
            if agora > hora_entrada_base:
                atraso = random.randint(-10, 30) # minutos
                hora_real = (hora_entrada_base + timedelta(minutes=atraso)).time()
                
                # Só registra se a hora real já aconteceu
                if agora.time() > hora_real:
                    status = "normal"
                    minutos_atraso = 0
                    if atraso > 10:
                        status = "atrasado"
                        minutos_atraso = atraso - 10
                    
                    p1 = RegistroPonto(
                        funcionario_id=func.id,
                        estabelecimento_id=estab.id,
                        data=hoje,
                        hora=hora_real,
                        tipo_registro="entrada",
                        status=status,
                        minutos_atraso=minutos_atraso
                    )
                    db.session.add(p1)
                    registros_criados += 1
            
            # Saída Almoço (12:00)
            hora_almoco = datetime.combine(hoje, time(12, 0))
            if agora > hora_almoco:
                 # Variação pequena
                var = random.randint(0, 10)
                hora_real = (hora_almoco + timedelta(minutes=var)).time()
                
                if agora.time() > hora_real:
                    p2 = RegistroPonto(
                        funcionario_id=func.id,
                        estabelecimento_id=estab.id,
                        data=hoje,
                        hora=hora_real,
                        tipo_registro="saida_almoco"
                    )
                    db.session.add(p2)
                    registros_criados += 1

            # Retorno Almoço (13:00)
            hora_retorno = datetime.combine(hoje, time(13, 0))
            if agora > hora_retorno:
                var = random.randint(0, 10)
                hora_real = (hora_retorno + timedelta(minutes=var)).time()
                
                if agora.time() > hora_real:
                    p3 = RegistroPonto(
                        funcionario_id=func.id,
                        estabelecimento_id=estab.id,
                        data=hoje,
                        hora=hora_real,
                        tipo_registro="retorno_almoco"
                    )
                    db.session.add(p3)
                    registros_criados += 1

            # Saída (17:00)
            hora_saida = datetime.combine(hoje, time(17, 0))
            if agora > hora_saida:
                # Hora extra?
                extras = 0
                if random.random() < 0.2: # 20% chance
                    extras = random.randint(30, 90)
                
                hora_real_dt = hora_saida + timedelta(minutes=extras)
                hora_real = hora_real_dt.time()
                
                if agora.time() > hora_real:
                    p4 = RegistroPonto(
                        funcionario_id=func.id,
                        estabelecimento_id=estab.id,
                        data=hoje,
                        hora=hora_real,
                        tipo_registro="saida"
                    )
                    db.session.add(p4)
                    registros_criados += 1

        db.session.commit()
        print(f"✅ Sucesso! {registros_criados} registros de ponto recriados para hoje.")

if __name__ == "__main__":
    fix_today_ponto()
