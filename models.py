from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jmeno = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telegram_id = db.Column(db.String(100), nullable=False)
    datum_narozeni = db.Column(db.Date, nullable=False)


