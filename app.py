from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import bcrypt
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "tajny_klic")


app.permanent_session_lifetime = 86400



def create_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Chyba: DATABASE_URL není nastaven!")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn
    except psycopg2.OperationalError as e:
        print(f" Chyba připojení k databázi: {e}")
        return None



def create_tables():
    conn = create_connection()
    if conn:
        with conn.cursor() as cursor:
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
            print("Tabulky byly úspěšně vytvořeny nebo již existují.")
        conn.close()


# Flask aplikace
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/add_result", methods=["POST"])
def add_result():
    if "user" not in session or session.get("role") != "laborant":
        flash("Nemáš oprávnění!", "danger")
        return redirect(url_for("dashboard"))

    rc = request.form.get("rc")
    leukocytes = request.form.get("leukocytes")
    erytrocytes = request.form.get("erytrocytes")
    hemoglobine = request.form.get("hemoglobine")
    hematocrite = request.form.get("hematocrite")
    trombocytes = request.form.get("trombocytes")

    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rc FROM patients WHERE rc = %s", (rc,))
        patient_exists = cursor.fetchone()

        if not patient_exists:
            flash("Pacient s tímto rodným číslem neexistuje!", "danger")
        else:
            try:
                cursor.execute("""
                    INSERT INTO results (rc, leukocytes, erytrocytes, hemoglobine, hematocrite, trombocytes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (rc, leukocytes, erytrocytes, hemoglobine, hematocrite, trombocytes))
                conn.commit()
                flash("Výsledek byl úspěšně uložen!", "success")
            except psycopg2.Error as e:
                flash(f"Chyba při ukládání: {e}", "danger")

        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = create_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT password, role FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()

                if result and bcrypt.checkpw(password.encode(), result[0].encode()):
                    session.permanent = True  # Uchování session
                    session["user"] = username
                    session["role"] = result[1]  # Nastavení role uživatele

                    flash("Přihlášení úspěšné!", "success")
                    return redirect(url_for("dashboard"))

        flash("Nesprávné přihlašovací údaje.", "danger")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("🔒 Musíš se nejdřív přihlásit!", "danger")
        return redirect(url_for("login"))

    username = session["user"]
    role = session.get("role", "laborant")

    conn = create_connection()
    patients, users, results = [], [], []
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT rc, name, surname FROM patients")
            patients = cursor.fetchall()

            cursor.execute("SELECT id, username, role FROM users")
            users = cursor.fetchall()

            cursor.execute("SELECT * FROM results")
            results = cursor.fetchall()
        conn.close()

    return render_template("dashboard.html", username=username, role=role, patients=patients, users=users, results=results)


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
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
        if conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, hashed_password, "laborant"))
                    conn.commit()
                    flash("Registrace úspěšná! Můžeš se přihlásit.", "success")
                    return redirect(url_for("login"))
                except psycopg2.Error:
                    flash("Uživatelské jméno už existuje!", "danger")
            conn.close()

    return render_template("register.html")


# Přidání pacienta
@app.route("/add_patient", methods=["POST"])
def add_patient():
    if "user" not in session or session.get("role") != "laborant":
        flash("⛔ Nemáš oprávnění!", "danger")
        return redirect(url_for("dashboard"))

    rc = request.form.get("rc")
    name = request.form.get("name")
    surname = request.form.get("surname")

    if not rc.isdigit() or len(rc) != 10:
        flash("Rodné číslo musí obsahovat přesně 10 číslic!", "danger")
        return redirect(url_for("dashboard"))

    conn = create_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT rc FROM patients WHERE rc = %s", (rc,))
            if cursor.fetchone():
                flash("Pacient s tímto rodným číslem už existuje!", "danger")
            else:
                cursor.execute("INSERT INTO patients (rc, name, surname) VALUES (%s, %s, %s)", (rc, name, surname))
                conn.commit()
                flash("Pacient byl úspěšně přidán!", "success")
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/delete_patient/<rc>", methods=["POST"])
def delete_patient(rc):
    if "user" not in session or session.get("role") != "laborant":
        flash("Nemáš oprávnění!", "danger")
        return redirect(url_for("dashboard"))

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM patients WHERE rc = %s", (rc,))
    conn.commit()

    flash("Pacient byl úspěšně smazán!", "success")
    cursor.close()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=5000)
