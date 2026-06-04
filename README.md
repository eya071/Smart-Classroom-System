# Lumen Classroom

Lumen Classroom er et system jeg har laget for å gjøre det enklere for elever å få hjelp i klasserommet. Istedenfor å rekke opp hånden kan eleven sende en melding digitalt, og læreren svarer via en egen side.

---

## Hva systemet gjør

Eleven logger inn og skriver hva de trenger hjelp med. Læreren ser alle meldinger i et admin-panel og kan svare. Når læreren har svart, får eleven en varsling.

**Elev kan:**

- Registrere seg og logge inn
- Sende forespørsel med tekst og bilde
- Se svar fra læreren
- Få varsling når læreren har svart

**Lærer kan:**

- Logge inn på admin-siden
- Se alle forespørsler fra elever
- Endre status: Ny, Pågår, Løst
- Skrive svar til eleven

---

## Teknologi jeg har brukt

- Python og Flask for backend
- HTML og CSS for frontend
- MariaDB for database
- Raspberry Pi som server
- bcrypt for å kryptere passord

---

## Slik starter du systemet

Installer det som trengs:

```bash
pip install flask pymysql bcrypt python-dotenv
```

Lag databasen i MariaDB:

```sql
CREATE DATABASE lumen_classroom;
USE lumen_classroom;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('elev', 'laerer') NOT NULL,
    class VARCHAR(20)
);

CREATE TABLE requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    name VARCHAR(100),
    message TEXT,
    status ENUM('Ny', 'Pågår', 'Løst') DEFAULT 'Ny',
    image VARCHAR(255),
    reply TEXT,
    read_status BOOLEAN DEFAULT FALSE,
    time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

Lag `.env`-fil:
DB_PASSWORD=ditt_passord
LAERER_KODE=laerer2026

Start Flask:

```bash
python app.py
```

Åpne nettleseren:
http://localhost:5000

---

## Sikkerhet

Passord lagres ikke som vanlig tekst — jeg bruker bcrypt som krypterer passordet. Elever kan ikke gå til admin-siden, og lærere kan ikke sende forespørsler som elever. Feil skrives til lumen.log.

---

## Om prosjektet

Laget av Eya, VG2 Osloskolen, 2026.
Fag: Informasjonsteknologi
