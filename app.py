from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import bcrypt
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "tajny_klic")


def create_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Chyba: DATABASE_URL není nastaven!")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        create_tables(conn)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Chyba připojení k databázi: {e}")
        return None


def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'laborant'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            rc VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            surname VARCHAR(100) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id SERIAL PRIMARY KEY,
            rc VARCHAR(10) NOT NULL,
            leukocytes INTEGER NOT NULL,
            erytrocytes INTEGER NOT NULL,
            hemoglobine INTEGER NOT NULL,
            hematocrite INTEGER NOT NULL,
            trombocytes INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rc) REFERENCES patients(rc) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    print("Tabulky byly úspěšně vytvořeny nebo již existují.")



# Flask aplikace
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result and bcrypt.checkpw(password.encode(), result[0].encode()):
            session["user"] = username
            flash("Přihlášení úspěšné!", "success")
            return redirect(url_for("dashboard"))

        flash("Nesprávné přihlašovací údaje.", "danger")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Musíš se nejdřív přihlásit!", "danger")
        return redirect(url_for("login"))

    username = session["user"]

    return render_template("dashboard.html", username=username)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Odhlášení úspěšné.", "success")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Vyplň všechna pole!", "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, hashed_password, "laborant"))
            conn.commit()
            flash("Registrace úspěšná! Můžeš se přihlásit.", "success")
            return redirect(url_for("login"))
        except psycopg2.Error:
            flash("Uživatelské jméno už existuje!", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")



if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=5000)
