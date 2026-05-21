import os
import shutil

backend_dir = r"c:\Users\rafae\Dev\mercadinhosys\backend"
services_email = os.path.join(backend_dir, "app", "services", "email_service.py")
utils_email = os.path.join(backend_dir, "app", "utils", "email_service.py")

# 1. Merge the files
with open(services_email, 'r', encoding='utf-8') as f:
    services_content = f.read()

with open(utils_email, 'r', encoding='utf-8') as f:
    utils_content = f.read()

# Replace the print in utils_email content
utils_content = utils_content.replace(
    'print(f"Erro ao enviar email genérico: {e}")',
    'current_app.logger.error(f"Erro ao enviar email genérico: {e}")'
)

# Append services to utils, then save as services
merged_content = utils_content + "\n\n# -- Merged from services/email_service.py --\n\n" + services_content

with open(services_email, 'w', encoding='utf-8') as f:
    f.write(merged_content)

# 2. Delete utils
os.remove(utils_email)

# 3. Replace imports across the codebase
for root, dirs, files in os.walk(backend_dir):
    if 'site-packages' in root or '.git' in root or '__pycache__' in root or 'venv' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'app.utils.email_service' in content:
                content = content.replace('app.utils.email_service', 'app.services.email_service')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated imports in {filepath}")

print("Merge module and references updated successfully.")
