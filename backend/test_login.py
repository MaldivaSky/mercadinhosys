import requests

url = 'http://localhost:5000/api/auth/login'
headers = {'Content-Type': 'application/json'}
data = {'username': 'maldivas', 'senha': 'Mald1v@$'}

response = requests.post(url, json=data, headers=headers)
print('Status Code:', response.status_code)
print('Response JSON:', response.json())