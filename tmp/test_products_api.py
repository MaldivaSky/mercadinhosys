
import requests

url = "http://localhost:5000/api/produtos/?pagina=1&por_pagina=25&ativos=true&ordenar_por=nome&direcao=asc"
headers = {
    # If it needs authentication, this might fail, but let's see if we get a 500 or 401.
    # The user said they get a 500.
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error connecting: {e}")
