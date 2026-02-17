"""
Seed inicial para ambiente cloud (Render).
Redireciona para seed_cloud_light com parâmetros adequados.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from seed_cloud_light import run_light_seed
    sys.exit(run_light_seed())
