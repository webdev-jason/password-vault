# 🔐 Password Vault

A secure, self-hosted password manager built with **Python Flask** and **PostgreSQL**. Features **Zero-Knowledge Encryption**, **Two-Factor Authentication (2FA)**, and a fully responsive **Progressive Web App (PWA)** interface for mobile devices.

![Project Banner](static/icon.png)
## 🚀 Features

* **Zero-Knowledge Architecture:** Master passwords are never stored. Encryption keys are derived client-side; only encrypted data reaches the server.
* **Two-Factor Authentication (2FA):** Built-in QR code generator for easy setup with Google/Microsoft Authenticator.
* **Progressive Web App (PWA):** Installable on iOS and Android as a native-feeling app (no browser bars).
* **Secure Account Management:**
    * Change Username/Password (triggers automatic vault re-encryption).
    * "Danger Zone" to securely delete accounts and all associated data.
* **Smart Security:**
    * Automatic inactivity logout (5-minute timer).
    * Clipboard auto-clearing logic.
    * Real-time password strength and character validation.
* **User Experience:**
    * Instant search filtering for rapid password retrieval.
    * One-tap "Copy to Clipboard" for passwords and 2FA secrets.
    * Mobile-optimized "Tap to Setup" for authenticators.

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, Flask
* **Database:** PostgreSQL (Cloud-hosted via Neon.tech)
* **Frontend:** HTML5, CSS3 (Modern Variables), Vanilla JavaScript
* **Security:**
    * `cryptography` (Fernet/AES encryption)
    * `pbkdf2` (Key derivation)
    * `pyotp` (Time-based One-Time Passwords)
    * `qrcode` (2FA Setup)
* **Deployment:** Render (Gunicorn)

## ⚙️ Installation & Local Setup

### 1. Clone the Repository
git clone [https://github.com/webdev-jason/password-vault.git](https://github.com/webdev-jason/password-vault.git)
cd password-vault

### 2. Set Up Virtual Environment
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Configure Environment Variables
Create a `.env` file in the root directory to store your private configuration. This keeps your secrets safe from the public code.

```ini
# .env

# Security key for Flask session cookies (Generate a random string)
SECRET_KEY=your_super_secret_random_string_here

# Connection string for your PostgreSQL database
DATABASE_URL=postgresql://user:password@your-neon-db-url.com/dbname

### 5. Initialize the Database
python db_setup.py

### 6. Run the Application
python app.py

Visit http://127.0.0.1:5000 in your browser.

## 📱 Mobile Installation (PWA)
Navigate to your deployed website on your mobile phone (Chrome for Android, Safari for iOS).

Android: Tap the menu (3 dots) -> "Install App" or "Add to Home Screen".

iOS: Tap the "Share" button -> "Add to Home Screen".

The app will appear on your home screen with the custom "PV" Shield icon.

## 🛡️ Security Logic
Encryption: User data is encrypted using a key derived from the Master Password + a unique Salt using PBKDF2-HMAC-SHA256.

Re-Encryption: When a user changes their Master Password, the server decrypts all records using the old key and immediately re-encrypts them with the new key in a single atomic transaction.

Validation: Inputs are sanitized on both the client-side (Regex) and server-side to prevent injection attacks and ensure data integrity.

## 📂 Project Structure
password-vault/
├── static/
│   ├── app.js           # Frontend logic (Encryption handling, UI state)
│   ├── style.css        # Modern CSS variables & Responsive design
│   ├── manifest.json    # PWA Configuration
│   └── icon.png         # App Icon
├── templates/
│   └── index.html       # Single Page Application (SPA) structure
├── app.py               # Main Flask Application & API Routes
├── crypto_manager.py    # Core encryption/decryption logic
├── db_setup.py          # Database initialization script
├── delete_user.py       # Admin utility for account cleanup
└── requirements.txt     # Python dependencies
