import os
from flask import Flask, render_template, request, redirect, session, jsonify
from datetime import datetime
import pymysql
import bcrypt
import logging
from dotenv import load_dotenv
load_dotenv()

LAERER_KODE = os.getenv("LAERER_KODE")
logging.basicConfig(
    filename="lumen.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("werkzeug").propagate = False

app = Flask(__name__)
app.secret_key = "hemmelig_nokkel_123"

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#  Database-tilkobling 
def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        database="lumen_classroom",
        cursorclass=pymysql.cursors.DictCursor
    )


#  Landing 
@app.route("/")
def landing():
    if "name" in session:
        if session.get("role") == "laerer":
            return redirect("/admin")
        return redirect("/hjem")
    return render_template("landing.html")


#  Auth 
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        role     = request.form.get("role", "elev")
        klasse   = request.form.get("class", "").strip()
        kode     = request.form.get("laerer_kode", "").strip()

        if not name or not password:
            error = "Navn og passord er påkrevd."
        elif role == "laerer" and kode != LAERER_KODE:
            error = "Feil lærer-kode."
        else:
            db = get_db()
            try:
                with db.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE name=%s", (name,))
                    if cur.fetchone():
                        error = "Brukernavnet er allerede tatt."
                    else:
                        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
                        cur.execute(
                            "INSERT INTO users (name, password, role, class) VALUES (%s,%s,%s,%s)",
                            (name, hashed, role, klasse if role == "elev" else None)
                        )
                        db.commit()
                        cur.execute("SELECT * FROM users WHERE name=%s", (name,))
                        user = cur.fetchone()
                        session["user_id"] = user["id"]
                        session["name"]    = user["name"]
                        session["role"]    = user["role"]
                        if user["role"] == "laerer":
                            return redirect("/admin")
                        return redirect("/hjem")
            finally:
                db.close()

    return render_template("landing.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE name=%s", (name,))
                user = cur.fetchone()
        finally:
            db.close()

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            error = "Feil brukernavn eller passord."
        else:
            session["user_id"] = user["id"]
            session["name"]    = user["name"]
            session["role"]    = user["role"]
            if user["role"] == "laerer":
                return redirect("/admin")
            return redirect("/hjem")

    return render_template("landing.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


#  Elev 
@app.route("/hjem", methods=["GET", "POST"])
def index():
    if "name" not in session:
        return redirect("/")
    if session.get("role") == "laerer":
        return redirect("/admin")

    if request.method == "POST":
        if session.get("role") != "elev":
            return redirect("/admin")

        image    = request.files.get("image")
        filename = None
        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO requests (user_id, name, message, image) VALUES (%s,%s,%s,%s)",
                    (session["user_id"], session["name"],
                     request.form.get("message") or "Ingen melding", filename)
                )
                db.commit()
        finally:
            db.close()
        return redirect("/hjem?sendt=1")

    return render_template("index.html", name=session["name"])


@app.route("/messages")
def messages():
    if "name" not in session:
        return redirect("/")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM requests WHERE user_id=%s ORDER BY time DESC",
                (session["user_id"],)
            )
            mine = cur.fetchall()
            uleste = sum(1 for r in mine if r["status"] == "Løst" and not r["read_status"])
            cur.execute(
                "UPDATE requests SET read_status=TRUE WHERE user_id=%s AND status='Løst'",
                (session["user_id"],)
            )
            db.commit()
    finally:
        db.close()

    return render_template("messages.html", requests=mine, uleste=uleste)


@app.route("/notifications")
def notifications():
    if "name" not in session:
        return jsonify({"uleste": 0})

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as antall FROM requests WHERE user_id=%s AND status='Løst' AND read_status=FALSE",
                (session["user_id"],)
            )
            row = cur.fetchone()
    finally:
        db.close()

    return jsonify({"uleste": row["antall"]})


# ---------- Admin / Lærer ----------
@app.route("/admin")
def admin():
    if session.get("role") != "laerer":
        return redirect("/")

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM requests ORDER BY time DESC")
            alle = cur.fetchall()
    finally:
        db.close()

    return render_template("admin.html", requests=alle)

@app.route("/hjelp")
def hjelp():
    return render_template("hjelp.html")


@app.route("/update/<int:req_id>", methods=["POST"])
def update(req_id):
    if session.get("role") != "laerer":
        return redirect("/")

    action = request.form.get("action")
    reply  = request.form.get("reply", "")

    db = get_db()
    try:
        with db.cursor() as cur:
            if action == "start":
                cur.execute("UPDATE requests SET status='Pågår' WHERE id=%s", (req_id,))
            elif action == "solve":
                cur.execute(
                    "UPDATE requests SET status='Løst', reply=%s WHERE id=%s",
                    (reply, req_id)
                )
            db.commit()
    finally:
        db.close()

    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)