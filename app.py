import os
import csv
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from forms import RegistrationForm  
from models import db, User  
from dotenv import load_dotenv
from bot import run_bot  # Přidáno pro spuštění bota

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "tajnyklic")

# Připojení k databázi – PostgreSQL z Renderu nebo fallback na SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/users.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Přihlašovací údaje pro admina
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password123")

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/registrace", methods=["GET", "POST"])
def registrace():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            jmeno=form.jmeno.data,
            email=form.email.data,
            telegram_id=form.telegram_id.data,
            datum_narozeni=form.datum_narozeni.data
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("platba", telegram_id=user.telegram_id))
    return render_template("registrace.html", form=form)


@app.route("/platba")
def platba():
    telegram_id = request.args.get("telegram_id")
    if not telegram_id:
        telegram_id = "Neznámé ID"
    return render_template("platba.html", telegram_id=telegram_id)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        return render_template("admin.html", error="Neplatný email nebo heslo")

    if not session.get("admin_logged_in"):
        return render_template("admin.html")

    users = User.query.all()
    return render_template("admin.html", users=users)


@app.route("/export")
def export():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    users = User.query.all()
    si = []
    header = ["ID", "Jméno", "Email", "Telegram ID", "Datum narození"]
    si.append(header)

    for u in users:
        si.append([
            u.id,
            u.jmeno,
            u.email,
            u.telegram_id,
            u.datum_narozeni.strftime("%Y-%m-%d")
        ])

    response = make_response('\n'.join([';'.join(map(str, row)) for row in si]))
    response.headers["Content-Disposition"] = "attachment; filename=registrace.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin")


@app.route("/check-user", methods=["POST"])
def check_user():
    data = request.get_json()
    telegram_id = data.get("telegram_id")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user:
        return {"registered": True}
    else:
        return {"registered": False}


# ✅ Spuštění Flasku + Telegram bota zároveň
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import threading

    load_dotenv()

    from bot import run_bot  # ujisti se, že importuješ správnou funkci z bot.py

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
