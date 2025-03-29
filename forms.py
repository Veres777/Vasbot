from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
from datetime import date

class RegistrationForm(FlaskForm):
    jmeno = StringField('Jméno', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telegram_id = StringField('Telegram ID', validators=[DataRequired()])
    datum_narozeni = DateField('Datum narození (RRRR-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Registrovat')

    def validate_datum_narozeni(self, field):
        dnes = date.today()
        vek = dnes.year - field.data.year - ((dnes.month, dnes.day) < (field.data.month, field.data.day))
        if vek < 18:
            raise ValidationError("Musíte být starší 18 let.")
