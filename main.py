import os
import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Configuration MikroTik (à récupérer plus tard via les variables d'environnement Render)
MIKROTIK_HOST = os.getenv("MIKROTIK_HOST", "http://192.168.88.1/rest")
MIKROTIK_USER = os.getenv("MIKROTIK_USER", "admin")
MIKROTIK_PASS = os.getenv("MIKROTIK_PASS", "")

@app.get("/")
def read_root():
    return {"status": "online", "message": "Luna Cyber MikroTik Bot & Mini App est actif !"}

@app.get("/api/active-users")
def get_active_users():
    """
    Exemple de route pour interroger l'API REST de MikroTik 
    (par exemple, les bails DHCP actifs ou les connexions Hotspot).
    """
    try:
        url = f"{MIKROTIK_HOST}/ip/dhcp-server/lease"
        response = requests.get(
            url, 
            auth=(MIKROTIK_USER, MIKROTIK_PASS), 
            verify=False, 
            timeout=5
        )
        if response.status_code == 200:
            return {"active_leases": response.json()}
        else:
            raise HTTPException(status_code=response.status_code, detail="Erreur de connexion au routeur MikroTik")
    except Exception as e:
        return {"error": str(e), "note": "Vérifiez l'adresse IP et les accès de l'API REST MikroTik."}
