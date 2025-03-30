import os
import requests
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import random
import sys
from flask import Flask
from models import db, User  # importujeme model User a přístup k DB
from telegram.constants import ParseMode
import pytz  


# Inicializace Flasku kvůli práci s databází
flask_app = Flask(__name__)
flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db.init_app(flask_app)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
# Načti .env soubor
load_dotenv()

# Token a API klíče
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEYS = [os.getenv("ODDS_API_KEY_1"), os.getenv("ODDS_API_KEY_2")]

# Sporty
SUPPORTED_SPORTS = {
    "Fotbal": "soccer",
    "Basketbal": "basketball",
    "Hokej": "icehockey",
    "Tenis": "tennis"
}

OWNER_ID = 8175755323


# Výchozí nastavení a úložiště nastavení uživatelů
default_settings = {
    "min_odds": 1.05,
    "min_probability": 80,
    "min_minutes": 30
}
user_settings = {}

def is_registered_user(telegram_id):
    with flask_app.app_context():
        return User.query.filter_by(telegram_id=str(telegram_id)).first() is not None

MAX_LENGTH = 4000  # Telegram limit je 4096 znaků, dáme rezervu

async def send_long_message(update, message):
    for i in range(0, len(message), MAX_LENGTH):
        await update.message.reply_text(message[i:i+MAX_LENGTH], parse_mode="Markdown")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = (
        "*Dostupné příkazy:* \n\n"
        "• **/tiket** – *Vygeneruje doporučený tiket.*\n"
        "• **/premium** – *Prémiový tip (jen pro registrované)*\n"
        "• **/nastaveni** – *Upraví parametry tiketu (kurz, čas, pravděpodobnost).*\n"
        "• **/stav** – *Zobrazí aktuální stav přístupu.*\n"
        "• **/debug** – *Ukáže přehled zápasů, které prošly filtrem.*"
    )
    await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text(
        "👋 Vítej! Pro přístup k prémiovým tipům se zaregistruj na webu:\n\n"
        "[🌐 Otevřít registraci](https://vasbot.cz/registrace)",
        parse_mode=ParseMode.MARKDOWN
    )



from telegram.ext import CommandHandler
from datetime import datetime, timezone
import random

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    premium_tips = []
    now = datetime.now(timezone.utc)

    for sport_name, sport_key in SUPPORTED_SPORTS.items():
        for api_key in API_KEYS:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
            params = {
                "apiKey": api_key,
                "regions": "eu",
                "markets": "h2h",
                "dateFormat": "iso",
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for match in data:
                    start_time = datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00"))
                    if start_time <= now:
                        continue

                    home = match.get("home_team", "Neznámý tým")
                    away = match.get("away_team", "Neznámý tým")
                    bookmakers = match.get("bookmakers", [])
                    if not bookmakers:
                        continue

                    outcomes = bookmakers[0].get("markets", [])[0].get("outcomes", [])
                    for outcome in outcomes:
                        odds = outcome["price"]
                        if 1.3 <= odds <= 2.5:
                            probability = round((1 / odds) * 100, 2)
                            if 65 <= probability <= 85:
                                premium_tips.append({
                                    "sport": sport_name,
                                    "home": home,
                                    "away": away,
                                    "team": outcome["name"],
                                    "odds": odds,
                                    "probability": probability,
                                    "time": start_time.strftime("%d.%m.%Y %H:%M")
                                })

            except requests.exceptions.RequestException as e:
                await update.message.reply_text(f"Chyba při načítání dat pro {sport_name}: {e}")
                break

    if premium_tips:
        best_match = random.choice(premium_tips)
        message = (
            "💎 *Prémiový tip dne:*\n\n"
            f"🏟 *Sport:* {best_match['sport']}\n"
            f"⚽ *Zápas:* {best_match['home']} vs {best_match['away']}\n"
            f"⏰ *Čas:* {best_match['time']}\n"
            f"✅ *Doporučená sázka:* {best_match['team']} @ {best_match['odds']}\n"
            f"📈 *Pravděpodobnost výhry:* {best_match['probability']} %"
        )
        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text("Dnes nebyl nalezen žádný vhodný prémiový zápas.")



# /nastaveni
async def nastaveni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    args = context.args
    settings = user_settings.get(chat_id, default_settings.copy())

    if not args:
        await update.message.reply_text(
            f"🛠 Aktuální nastavení:\n\n"
            f"• Minimální kurz (kurz): {settings['min_odds']}\n"
            f"• Minimální pravděpodobnost výhry (pravdepodobnost): {settings['min_probability']} %\n"
            f"• Minimální čas do začátku zápasu (cas): {settings['min_minutes']} minut\n\n"
            f"📌 Pokud chceš změnit nastavení, použij např.:\n"
            f"/nastaveni kurz=1.2 pravdepodobnost=85 cas=45"
        )
        return

    for arg in args:
        if arg.startswith("kurz="):
            try:
                settings["min_odds"] = float(arg.split("=")[1])
            except ValueError:
                pass
        elif arg.startswith("pravdepodobnost="):
            try:
                settings["min_probability"] = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg.startswith("cas="):
            try:
                settings["min_minutes"] = int(arg.split("=")[1])
            except ValueError:
                pass

    user_settings[chat_id] = settings

    await update.message.reply_text(
        f"✅ Nové nastavení uloženo:\n\n"
        f"• Minimální kurz: {settings['min_odds']}\n"
        f"• Minimální pravděpodobnost výhry: {settings['min_probability']} %\n"
        f"• Zápas musí začínat za min. {settings['min_minutes']} minut"
    )

# /debug
async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    settings = user_settings.get(chat_id, default_settings)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=1, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    debug_message = "📊 *Debug info podle aktuálního nastavení:*\n\n"

    for sport_name, sport_key in SUPPORTED_SPORTS.items():
        total_matches = 0
        passed_filters = 0

        for api_key in API_KEYS:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
            params = {
                "apiKey": api_key,
                "regions": "eu",
                "markets": "h2h",
                "dateFormat": "iso",
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code != 200:
                    continue

                data = response.json()
                if not data:
                    continue

                for match in data:
                    commence_time = match.get("commence_time")
                    if not commence_time:
                        continue

                    start_time = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))

                    # 🎯 DNEŠNÍ ZÁPAS
                    if not (today_start <= start_time <= today_end):
                        continue

                    total_matches += 1

                    # ⏳ ČAS DO ZAČÁTKU
                    if (start_time - now) < timedelta(minutes=settings["min_minutes"]):
                        continue

                    bookmakers = match.get("bookmakers", [])
                    if not bookmakers:
                        continue

                    outcomes = bookmakers[0].get("markets", [])[0].get("outcomes", [])
                    if not outcomes:
                        continue

                    best_outcome = min(outcomes, key=lambda x: x["price"])
                    odds = best_outcome["price"]
                    probability = round((1 / odds) * 100, 2)

                    if odds < settings["min_odds"]:
                        continue

                    if probability < settings["min_probability"]:
                        continue

                    passed_filters += 1

                break  # použij jen první funkční API klíč

            except requests.exceptions.RequestException:
                continue

        debug_message += f"• *{sport_name}*: {total_matches} zápasů / {passed_filters} vyhovuje\n"

    await update.message.reply_text(debug_message, parse_mode=ParseMode.MARKDOWN)

# /tiket
async def tiket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    if not is_registered_user(telegram_id):
        await update.message.reply_text(
            "⛔ Tento bot je určen pouze pro registrované uživatele.\n\n"
            "Pokud ještě nemáš přístup, zaregistruj se na webu."
        )
        return

    chat_id = update.effective_chat.id
    ticket_data = []
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=1, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    for sport_name, sport_key in SUPPORTED_SPORTS.items():
        for api_key in API_KEYS:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
            params = {
                "apiKey": api_key,
                "regions": "eu",
                "markets": "h2h",
                "dateFormat": "iso",
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code != 200:
                    continue

                data = response.json()
                if not data:
                    continue

                for match in data:
                    commence_time = match.get("commence_time", "Neznámý čas")
                    start_time = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))

                    # ⏰ Pouze dnešní zápasy
                    if not (today_start <= start_time <= today_end):
                        continue

                    home_team = match.get("home_team", "Neznámý tým")
                    away_team = match.get("away_team", "Neznámý tým")
                    league = match.get("sport_title", "Neznámá liga")
                    bookmakers = match.get("bookmakers", [])
                    if not bookmakers:
                        continue

                    outcomes = bookmakers[0].get("markets", [])[0].get("outcomes", [])
                    if not outcomes:
                        continue

                    best_outcome = min(outcomes, key=lambda x: x["price"])
                    odds = best_outcome["price"]
                    probability = round((1 / odds) * 100, 2)

                    # 🎯 Pouze s pravděpodobností 75 % a více
                    if probability < 75:
                        continue

                    ticket_data.append({
                        "sport": sport_name,
                        "league": league,
                        "home": home_team,
                        "away": away_team,
                        "time": commence_time,
                        "team": best_outcome["name"],
                        "odds": odds,
                        "probability": probability
                    })

                break  # použij první funkční API klíč

            except requests.exceptions.RequestException:
                continue

    if not ticket_data:
        await update.message.reply_text("❌ Nenašly se žádné vhodné zápasy pro dnešní tiket.")
        return

    total_odds = 1
    ticket_message = "🎟 *Dnešní tiket – přehled zápasů:*\n\n"

    for game in ticket_data:
        total_odds *= game["odds"]
        start_utc = datetime.fromisoformat(game["time"].replace("Z", "+00:00"))
        prague_time = start_utc.astimezone(pytz.timezone("Europe/Prague"))
        game_time = prague_time.strftime("%d.%m.%Y %H:%M")
        highlight = "🔥" if game["probability"] >= 75 else ""

        ticket_message += (
            f"{highlight} *{game['sport']} – {game['league']}*\n"
            f"Zápas: {game['home']} vs {game['away']}\n"
            f"Čas: {game_time}\n"
            f"Doporučená sázka: *{game['team']}* @ {game['odds']}\n"
            f"Pravděpodobnost výhry: *{game['probability']} %*\n\n"
        )

    win_probability = round((1 / total_odds) * 100, 2)
    

    await send_long_message(update, ticket_message)



# Spuštění bota
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("premium", premium))
    application.add_handler(CommandHandler("debug", debug))
    application.add_handler(CommandHandler("nastaveni", nastaveni))
    application.add_handler(CommandHandler("tiket", tiket))
    application.add_handler(CommandHandler("stav", stav))
    application.run_polling()

async def stav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    if telegram_id == OWNER_ID:
        await update.message.reply_text("✅ Máš plný přístup jako správce tohoto bota.")
        return

    if is_registered_user(telegram_id):
        await update.message.reply_text("✅ Máš přístup k prémiovým funkcím.")
    else:
        await update.message.reply_text(
            "⛔ Nemáš přístup k tomuto botovi.\n"
            "Zaregistruj se na webu pro získání přístupu."
        )


def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stav", stav))
    application.add_handler(CommandHandler("premium", premium))
    application.add_handler(CommandHandler("tiket", tiket))
    application.add_handler(CommandHandler("debug", debug))
    application.add_handler(CommandHandler("nastaveni", nastaveni))

    print("✅ Telegram bot běží...")
    application.run_polling()

    def is_registered(telegram_id):
        try:
            response = requests.get(f"https://vasbot.cz/api/check_user?id={telegram_id}", timeout=5)
            data = response.json()
            return data["status"] == "ok"
        except:
            return False

# Volitelné spuštění samostatně
if __name__ == "__main__":
    run_bot()


