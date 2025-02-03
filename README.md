# LabTrack - Laboratory Results Management

LabTrack is a web-based application built with Flask and PostgreSQL for managing laboratory results of patients. It allows lab technicians ("laborant") to register, log in, add patients, store test results, and view patient data.

## Features
- User authentication (registration, login, logout)
- Role-based access control (admin, lab technician)
- Patient management (add, view, delete patients)
- Laboratory results management (add, view results per patient)
- Secure password hashing with bcrypt
- Database management using PostgreSQL

## Technologies Used
- **Backend:** Flask, Python
- **Database:** PostgreSQL
- **Frontend:** HTML, CSS
- **Security:** bcrypt for password hashing

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3
- PostgreSQL
- Virtual environment tool (venv)

### Step 1: Clone the repository
```sh
 git clone https://github.com/your-repo/LabTrack.git
 cd LabTrack
```

### Step 2: Create a Virtual Environment
```sh
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows
```

### Step 3: Install Dependencies
```sh
pip install -r requirements.txt
```

### Step 4: Configure Database
1. **Start PostgreSQL** and create a database named `lab`.
2. Alternatively, the script will attempt to create it if it does not exist.
3. Update the database credentials in `app.py`:
```python
DB_NAME = "lab"
DB_USER = "postgres"
DB_PASSWORD = "coderslab"
DB_HOST = "localhost"
DB_PORT = "5432"
```

### Step 5: Run the Application
```sh
python app.py
```

The app will be accessible at `http://127.0.0.1:5000/`.

## Usage

### User Roles
- **Admin**: Can view all users.
- **Lab Technician (default)**: Can add patients and manage lab results.

### Register and Login
1. Navigate to `/register` to create an account.
2. Log in at `/login`.

### Managing Patients
- Add a patient with **name, surname, and unique national ID (RC)**.
- View all patients in the **dashboard**.
- Delete patients if necessary.

### Adding Lab Results
- Select a patient and enter test results (leukocytes, erythrocytes, hemoglobin, etc.).

### Viewing Results
- Click **"View Results"** next to a patient to see test history.

## Folder Structure
```
LabTrack/
│── static/
│   ├── style.css     # CSS styles
│── templates/
│   ├── dashboard.html
│   ├── login.html
│   ├── register.html
│   ├── patient_results.html
│── app.py            # Main Flask application
│── README.md         # Documentation
```

## Security Notes
- Passwords are **hashed** using bcrypt.
- Unauthorized users cannot access restricted pages.

## Future Enhancements
- Export lab results to PDF
- Data visualization (graphs, charts)
- Integration with hospital systems (HL7/FHIR API)

## License
MIT License. Feel free to use and modify!

---
Made with ❤️ by Dendoid

