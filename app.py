from flask import Flask, render_template, request, redirect, session, url_for
from forms import RegistrationForm
from models import db, User
import csv
from flask import make_response

app = Flask(__name__)
app.secret_key = "tajnyklic"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Přihlašovací údaje
ADMIN_EMAIL = "spatial_traveller@proton.me"
ADMIN_PASSWORD = "62583425AverMax"

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
        telegram_id = "Neznámé ID"  # záloha, pokud náhodou chybí
    return render_template("platba.html", telegram_id=telegram_id)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))  # po přihlášení redirect

        return render_template("admin.html", error="Neplatný email nebo heslo")

    if not session.get("admin_logged_in"):
        return render_template("admin.html")

    users = User.query.all()
    return render_template("admin.html", users=users)

import csv
from flask import make_response

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


if __name__ == "__main__":
    app.run(debug=True)

