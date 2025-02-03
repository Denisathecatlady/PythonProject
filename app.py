from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import bcrypt

app = Flask(__name__)
app.secret_key = "tajny_klic"

# Připojení k PostgreSQL
def create_connection():
    try:
        conn = psycopg2.connect(
            dbname="lab",
            user="postgres",
            password="coderslab",
            host="localhost",
            port="5432"
        )
        return conn
    except psycopg2.OperationalError:
        print("Databáze 'lab' neexistuje. Vytvářím ji...")
        create_database()
        return create_connection()

def create_database():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="coderslab",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE lab;")
        print("Databáze 'lab' byla úspěšně vytvořena.")
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Chyba při vytváření databáze: {e}")

# Vytvoření tabulek
def create_tables():
    conn = create_connection()
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
    conn.close()

# Hashování hesla
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

# Registrace uživatele
def register_user(username, password, role="laborant"):
    hashed_password = hash_password(password)
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False

        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, hashed_password, role))
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Chyba při registraci uživatele: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Přihlášení uživatele
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT password, role FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result and bcrypt.checkpw(password.encode(), result[0].encode()):
            session["user"] = username
            session["role"] = result[1]
            return True
        return False
    except psycopg2.Error as e:
        print(f"Chyba při přihlašování: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

#Flask
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            if register_user(username, password):
                flash("Registrace úspěšná! Můžeš se přihlásit.", "success")
                return redirect(url_for("login"))
            else:
                flash("Uživatelské jméno už existuje.", "danger")
        else:
            flash("Vyplň všechna pole.", "danger")

    return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if login_user(username, password):
            flash("Přihlášení úspěšné!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Nesprávné přihlašovací údaje.", "danger")

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Musíš se nejdřív přihlásit!", "danger")
        return redirect(url_for("login"))

    username = session["user"]
    role = session["role"]

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT rc, name, surname FROM patients")
    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("dashboard.html", username=username, role=role, patients=patients)

# Přidání pacienta
@app.route("/add_patient", methods=["POST"])
def add_patient():
    if "user" not in session or session["role"] != "laborant":
        flash("Nemáš oprávnění!", "danger")
        return redirect(url_for("dashboard"))

    rc = request.form.get("rc")
    name = request.form.get("name")
    surname = request.form.get("surname")

    if not rc.isdigit() or len(rc) != 10:
        flash("Rodné číslo musí obsahovat přesně 10 číslic!", "danger")
        return redirect(url_for("dashboard"))

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT rc FROM patients WHERE rc = %s", (rc,))
    if cursor.fetchone():
        flash("Pacient s tímto rodným číslem už existuje!", "danger")
    else:
        cursor.execute("INSERT INTO patients (rc, name, surname) VALUES (%s, %s, %s)", (rc, name, surname))
        conn.commit()
        flash("Pacient byl úspěšně přidán!", "success")

    cursor.close()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/add_result", methods=["POST"])
def add_result():
    if "user" not in session or session["role"] != "laborant":
        flash("Nemáš oprávnění!", "danger")
        return redirect(url_for("dashboard"))

    rc = request.form.get("rc")
    leukocytes = request.form.get("leukocytes")
    erytrocytes = request.form.get("erytrocytes")
    hemoglobine = request.form.get("hemoglobine")
    hematocrite = request.form.get("hematocrite")
    trombocytes = request.form.get("trombocytes")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT rc FROM patients WHERE rc = %s", (rc,))
    patient_exists = cursor.fetchone()

    if not patient_exists:
        flash("Pacient s tímto rodným číslem neexistuje!", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("dashboard"))

    try:
        cursor.execute("""
            INSERT INTO results (rc, leukocytes, erytrocytes, hemoglobine, hematocrite, trombocytes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (rc, leukocytes, erytrocytes, hemoglobine, hematocrite, trombocytes))
        conn.commit()
        flash("Výsledek byl úspěšně uložen!", "success")
    except psycopg2.Error as e:
        flash(f"Chyba při ukládání: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))


# Smazání pacienta
@app.route("/delete_patient/<rc>", methods=["POST"])
def delete_patient(rc):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM patients WHERE rc = %s", (rc,))
    conn.commit()

    flash("Pacient byl úspěšně smazán!", "success")
    cursor.close()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/patients", methods=["GET"])
def patients():
    conn = create_connection()
    cursor = conn.cursor()

    # SQL JOIN: Spojí pacienty s jejich laboratorními výsledky
    cursor.execute("""
        SELECT 
            patients.rc, patients.name, patients.surname, 
            results.leukocytes, results.erytrocytes, results.hematocrite, results.hemoglobine, results.trombocytes
        FROM patients
        LEFT JOIN results ON patients.rc = results.rc
    """)
    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("patients.html", patients=patients)

@app.route("/patient_results/<rc>")
def patient_results(rc):
    if "user" not in session or session["role"] != "laborant":
        flash("Nemáš oprávnění!", "danger")
        return redirect(url_for("dashboard"))

    conn = create_connection()
    cursor = conn.cursor()

    # Vybereme data pacienta
    cursor.execute("SELECT name, surname FROM patients WHERE rc = %s", (rc,))
    patient = cursor.fetchone()

    if not patient:
        flash("Pacient nebyl nalezen!", "danger")
        return redirect(url_for("dashboard"))


    cursor.execute("""
        SELECT leukocytes, erytrocytes, hemoglobine, hematocrite, trombocytes, created_at
        FROM results WHERE rc = %s
    """, (rc,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("patient_results.html", patient=patient, rc=rc, results=results)

# Odhlášení
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("Odhlášení úspěšné.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
