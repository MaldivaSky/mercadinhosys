import sys, subprocess, os
env = os.environ.copy()
env['DATABASE_URL'] = 'sqlite:///:memory:'
env['MULTI_TENANT_MODE'] = 'false'
with open("test_out.txt", "w", encoding="utf-8") as f:
    r1 = subprocess.run([sys.executable, "-m", "pytest", "tests/test_vendas_multi.py", "-v"], env=env, stdout=f, stderr=subprocess.STDOUT)
    r2 = subprocess.run([sys.executable, "-m", "pytest", "tests/test_delivery_multi.py", "-v"], env=env, stdout=f, stderr=subprocess.STDOUT)
