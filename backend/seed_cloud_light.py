
import sys
import os

# Adiciona o diretório atual ao path para garantir que imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from seed_test import main

def run_light_seed():
    """
    Executa o seed_test.py com parâmetros reduzidos para teste rápido na nuvem.
    Parâmetros:
    - 50 produtos (vs 200 normal)
    - 30 fornecedores (vs 50 normal)
    - 30 clientes (vs 100 normal)
    - 90 dias de histórico (vs 300 normal)
    """
    print("🚀 Iniciando Seed Leve para Nuvem (Vercel/Neon)...")
    print("   - Produtos: 50")
    print("   - Fornecedores: 30")
    print("   - Clientes: 30")
    print("   - Histórico: 90 dias")
    print("=" * 50)

    # Força os argumentos para o seed_test
    # Preserva o nome do script (argv[0]) e adiciona os argumentos
    simulated_args = [
        "seed_test.py",
        "--reset",
        "--cloud",
        "--produtos", "50",
        "--fornecedores", "30",
        "--clientes", "30",
        "--dias", "90"
    ]
    
    # Chama a função main do seed_test passando os argumentos simulados
    # Nota: main espera argv ou usa sys.argv se None. 
    # Olhando seed_test.py: def main(argv: Optional[List[str]] = None)
    # Então podemos passar diretamente.
    # Mas sys.exit(main()) espera retorno int.
    
    return main(simulated_args[1:]) # main usa argparse que parseia a lista (sem o nome do script se passar lista)

if __name__ == "__main__":
    sys.exit(run_light_seed())
