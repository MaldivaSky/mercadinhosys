import urllib.request
import json

url = "http://127.0.0.1:5000/api/auth/login"
data = {"username": "admin", "senha": "admin123"}
data = json.dumps(data).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"Status: {response.status}")
        print(f"Response: {result}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Response: {e.read().decode('utf-8')}")