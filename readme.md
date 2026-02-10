![GitHub last commit](https://img.shields.io/github/last-commit/webdev-jason/password-vault?style=flat-square)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![GitHub license](https://img.shields.io/github/license/webdev-jason/password-vault?style=flat-square)

# Password Vault

A secure, self-hosted password manager built with Python Flask and PostgreSQL. It features Zero-Knowledge Encryption, Two-Factor Authentication (2FA), and a fully responsive Progressive Web App (PWA) interface for mobile access.

## 🛡️ Security First
<img src="static/readme_icon.png" width="250" alt="Password Vault Shield Logo">

## ✨ Features
* **🔒 Zero-Knowledge Architecture**: Master passwords are never stored. Encryption keys are derived client-side; only encrypted data reaches the server.
* **📲 Progressive Web App (PWA)**: Installable on iOS and Android as a native-feeling app (no browser bars).
* **🔐 Two-Factor Authentication (2FA)**: Built-in QR code generator for easy setup with Google/Microsoft Authenticator.
* **⚡ Smart Security**:
    * Automatic inactivity logout (5-minute timer).
    * Clipboard auto-clearing logic.
    * Real-time password strength and character validation.
* **🔎 User Experience**:
    * Instant search filtering for rapid password retrieval.
    * One-tap "Copy to Clipboard" for passwords and 2FA secrets.
    * Mobile-optimized "Tap to Setup" for authenticators.

## 🛠️ Tech Stack
* **Backend**: Python 3.10+, Flask
* **Database**: PostgreSQL
* **Frontend**: HTML5, CSS3, Vanilla JavaScript
* **Security**:
    * `cryptography`: Fernet/AES encryption
    * `pbkdf2`: Key derivation
    * `pyotp`: Time-based One-Time Passwords

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/webdev-jason/password-vault.git](https://github.com/webdev-jason/password-vault.git)
cd password-vault
```

### 2. Set Up Virtual Environment
**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:

```ini
SECRET_KEY=your_super_secret_flask_key
DATABASE_URL=postgresql://user:password@your-db-url.com/dbname
```

### 5. Initialize the Database
```bash
python db_setup.py
```

### 6. Run the Application
```bash
python app.py
```
Visit `http://127.0.0.1:5000` in your browser.

## 👤 Author
**Jason Sparks** - [GitHub Profile](https://github.com/webdev-jason)

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.