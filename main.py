import os
import requests
from fastapi import FastAPI, HTTPException
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

app = FastAPI()

# Configuration MikroTik
MIKROTIK_HOST = os.getenv("MIKROTIK_HOST", "http://192.168.20.1/rest")
MIKROTIK_USER = os.getenv("MIKROTIK_USER", "admin")
MIKROTIK_PASS = os.getenv("MIKROTIK_PASS", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

def fetch_mikrotik_leases():
    """Fonction utilitaire pour interroger les bails DHCP actifs du MikroTik"""
    try:
        url = f"{MIKROTIK_HOST}/ip/dhcp-server/lease"
        response = requests.get(
            url, 
            auth=(MIKROTIK_USER, MIKROTIK_PASS), 
            verify=False, 
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"status": "online", "message": "Luna Cyber MikroTik Bot est actif !"}

@app.get("/api/active-users")
def get_active_users():
    leases = fetch_mikrotik_leases()
    if isinstance(leases, dict) and "error" in leases:
        raise HTTPException(status_code=500, detail=leases["error"])
    return {"active_leases": leases}

# --- LOGIQUE DU BOT TELEGRAM ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start envoyée au bot"""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Bonjour {user_name} ! 🚀 Bienvenue sur le bot de gestion de Luna Cyber.\n\n"
        "Commandes disponibles :\n"
        "/users - Afficher les utilisateurs/bails DHCP actifs sur le MikroTik"
    )

async def active_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /users pour lister les connexions depuis Telegram"""
    await update.message.reply_text("🔄 Interrogation du routeur MikroTik en cours...")
    
    leases = fetch_mikrotik_leases()
    if not leases:
        await update.message.reply_text("❌ Impossible de joindre le routeur ou aucune réponse reçue.")
        return
    
    if isinstance(leases, dict) and "error" in leases:
        await update.message.reply_text(f"⚠️ Erreur de connexion : {leases['error']}")
        return

    # Formater la liste des utilisateurs actifs
    message = "📋 **Utilisateurs / Bails Actifs (MikroTik)** :\n\nfor lease in leases:\n"
    count = 0
    for lease in leases:
        if lease.get("status") == "bound":
            ip = lease.get("address", "N/A")
            mac = lease.get("mac-address", "N/A")
            host = lease.get("host-name", "Inconnu")
            message += f"• **{host}**\n  IP: `{ip}`\n  MAC: `{mac}`\n\n"
            count += 1
            
    if count == 0:
        message = "ℹ️ Aucun bail actif pour le moment."
    else:
        message = f"Total actifs : {count}\n\n" + message

    await update.message.reply_text(message, parse_mode="Markdown")

# Initialisation du Bot Telegram au démarrage de l'application
if TELEGRAM_TOKEN:
    telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("users", active_users_command))
    
    # Lancement du bot en arrière-plan (Polling)
    # Note: Sur Render, le polling fonctionne si le service tourne en continu (instances payantes) 
    # ou via des webhooks pour les instances gratuites. Testons d'abord le déploiement.
    try:
        telegram_app.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"Erreur Telegram polling: {e}")
