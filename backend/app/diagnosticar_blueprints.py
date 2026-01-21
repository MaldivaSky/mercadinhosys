#!/usr/bin/env python3
"""
Diagnóstico dos blueprints
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def listar_conteudo_arquivo(caminho):
    """Lista conteúdo de um arquivo"""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()
            # Pega apenas as primeiras 20 linhas
            for i, linha in enumerate(linhas[:20]):
                print(f"{i+1:3}: {linha.rstrip()}")
            if len(linhas) > 20:
                print(f"... ({len(linhas)-20} linhas restantes)")
    except Exception as e:
        print(f"Erro ao ler {caminho}: {e}")


def diagnosticar():
    print("🔍 DIAGNÓSTICO DE BLUEPRINTS")
    print("=" * 60)

    # Verificar estrutura
    print("\n📁 Estrutura de routes:")
    routes_path = os.path.join("app", "routes")
    if os.path.exists(routes_path):
        arquivos = os.listdir(routes_path)
        for arquivo in sorted(arquivos):
            if arquivo.endswith(".py"):
                print(f"  • {arquivo}")

    # Verificar dashboard.py especificamente
    print("\n📊 Conteúdo de dashboard.py (primeiras linhas):")
    dashboard_path = os.path.join("app", "routes", "dashboard.py")
    if os.path.exists(dashboard_path):
        listar_conteudo_arquivo(dashboard_path)
    else:
        print("❌ Arquivo dashboard.py não encontrado!")

    # Testar importação
    print("\n🧪 Testando importações:")
    try:
        import importlib

        module = importlib.import_module("app.routes.dashboard")

        print("✅ Módulo dashboard importado com sucesso")
        print("\n🔍 Atributos do módulo:")
        for attr in dir(module):
            if not attr.startswith("_"):
                print(f"  • {attr}")

        # Procurar por blueprint
        blueprint_candidates = [
            attr
            for attr in dir(module)
            if "blueprint" in attr.lower()
            or attr in ["dashboard", "bp", "dashboard_bp"]
        ]
        if blueprint_candidates:
            print(f"\n🎯 Possíveis blueprints: {blueprint_candidates}")
            for candidate in blueprint_candidates:
                obj = getattr(module, candidate)
                print(f"  {candidate}: {type(obj)}")
        else:
            print("\n⚠️  Nenhum blueprint óbvio encontrado")

    except ImportError as e:
        print(f"❌ Erro ao importar: {e}")


if __name__ == "__main__":
    diagnosticar()
