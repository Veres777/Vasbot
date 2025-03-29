# 🤖 VasBot – Telegram sázení asistent

**VasBot** je chytrý osobní Telegram bot napojený na Flask backend a sportovní API. Každý den generuje prémiové sázkové tikety s vysokou pravděpodobností výhry a umožňuje správu uživatelů přes jednoduchý web.

---

## 🛠 Funkce

### 🧠 Telegram Bot
- `/start` – úvodní nabídka a odkazy
- `/tiket` – generuje denní sázkový tiket s tipy nad 75 %
- `/premium` – nejlepší tip dne (pouze pro registrované)
- `/stav` – ověření přístupu
- `/nastaveni` – vlastní filtry pro tikety
- `/debug` – testovací výpis

### 🌐 Webová aplikace (Flask)
- Registrace uživatelů
- Ověření účtu podle `telegram_id`
- Platba přes QR nebo PayPal
- Administrace (ukryta)

---

## 🔐 Platební možnosti

- QR kód pro jednorázovou platbu 500 Kč
- (Volitelně) napojení na PayPal

---

## 💡 Technologie

| Technologie | Použití         |
|-------------|-----------------|
| Python      | Backend & Bot   |
| Flask       | Web aplikace    |
| SQLite      | Databáze        |
| Telegram API| Bot komunikace  |
| The Odds API| Sportovní data  |
| HTML/CSS    | Web rozhraní    |

---

## 🔗 Odkazy

- 🌍 Web: [https://vasbot.cz](https://vasbot.cz)
- 🤖 Telegram bot: [https://t.me/Vsadim_bot](https://t.me/Vsadim_bot)

---

## 🔒 Autor & Kontakt

Tento projekt vytvořil **Averianov Sergej** jako portfolio pro ukázku backendových a webových dovedností.

- 📧 Email: spatial_traveller@proton.me
- 💼 Hostivice, Česká republika
