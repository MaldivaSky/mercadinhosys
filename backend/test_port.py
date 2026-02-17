import socket
import sys

def check_port():
    host = "REDACTED_HOST"
    port = 10662
    timeout = 10
    
    print(f"Verificando {host}:{port}...")
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            print(f"✅ Porta {port} está ABERTA no host {host}!")
            return True
    except socket.timeout:
        print(f"❌ Erro: Timeout de {timeout}s atingido ao tentar conectar a {host}:{port}.")
        return False
    except socket.gaierror:
        print(f"❌ Erro: Não foi possível resolver o host {host}.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    if check_port():
        sys.exit(0)
    else:
        sys.exit(1)
