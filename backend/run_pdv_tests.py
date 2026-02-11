"""
🚀 Script para executar os testes críticos do PDV

Uso:
    python backend/run_pdv_tests.py
    
Ou com pytest:
    pytest backend/tests/test_pdv_critical_flow.py -v
"""

import sys
import os
import subprocess

def main():
    print("\n" + "🧪 " + "="*68)
    print("🧪  EXECUTANDO TESTES CRÍTICOS DO PDV")
    print("🧪 " + "="*68 + "\n")
    
    # Verificar se pytest está instalado
    try:
        import pytest
        print("✅ pytest encontrado\n")
        
        # Executar testes com pytest
        test_file = os.path.join('tests', 'test_pdv_critical_flow.py')
        
        print(f"📂 Executando: {test_file}\n")
        
        result = pytest.main([
            test_file,
            '-v',  # Verbose
            '--tb=short',  # Traceback curto
            '--color=yes',  # Colorir output
            '-s'  # Mostrar prints
        ])
        
        print("\n" + "="*70)
        if result == 0:
            print("✅ TODOS OS TESTES PASSARAM!")
            print("="*70)
            print("\n🎉 Sistema PDV está estável e pronto para próxima fase!")
            print("\nPróximos passos:")
            print("  1. ✅ Testes críticos do PDV concluídos")
            print("  2. 🔄 Implementar validações e tratamento de erros")
            print("  3. 🔄 Criar seed data unificado")
        else:
            print("❌ ALGUNS TESTES FALHARAM!")
            print("="*70)
            print("\n⚠️  Revise os erros acima e corrija antes de prosseguir.")
        
        return result
        
    except ImportError:
        print("⚠️  pytest não instalado!")
        print("\nPara instalar:")
        print("  pip install pytest\n")
        
        print("Tentando executar testes manualmente...\n")
        
        # Executar diretamente com Python
        test_file = os.path.join('tests', 'test_pdv_critical_flow.py')
        result = subprocess.run([sys.executable, test_file])
        
        return result.returncode

if __name__ == '__main__':
    sys.exit(main())
