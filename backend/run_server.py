import os
import sys
import threading
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CERT_FILE = os.path.join(BASE_DIR, "cert.pem")
KEY_FILE = os.path.join(BASE_DIR, "key.pem")

def run_https():
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        print(">> [HTTPS] Servidor Seguro iniciado em: https://0.0.0.0:8443 (Permite câmera nativa no navegador do celular)")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8443,
            ssl_certfile=CERT_FILE,
            ssl_keyfile=KEY_FILE,
            log_level="info"
        )
    else:
        print(">> [HTTPS] Certificados cert.pem / key.pem não encontrados.")

def run_http():
    print(">> [HTTP] Servidor padrão iniciado em: http://0.0.0.0:8080")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

if __name__ == "__main__":
    # Start HTTPS in a background daemon thread
    https_thread = threading.Thread(target=run_https, daemon=True)
    https_thread.start()
    
    # Run HTTP in the main thread
    run_http()
