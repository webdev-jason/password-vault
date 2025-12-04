from flask import Flask, request, jsonify, render_template
import sqlite3
import pyotp
import crypto_manager

app = Flask(__name__)

# UTILITY: Database Connection
def get_db_connection():
    conn = sqlite3.connect('vault.db')
    conn.row_factory = sqlite3.Row 
    return conn

# UTILITY: Auth Helper
def authenticate_user(username, master_password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user is None:
        return None
    
    stored_salt = user['salt']
    stored_hash = user['password_hash']
    
    if crypto_manager.verify_master_password(master_password, stored_salt, stored_hash):
        return user
    else:
        return None

# --- WEB ROUTES (The Frontend) ---

@app.route('/')
def index():
    # This looks for 'index.html' inside the 'templates' folder
    return render_template('index.html')

# --- API ROUTES (The Backend) ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password_input = data.get('password')
    code_input = data.get('2fa_code')

    user = authenticate_user(username, password_input)
    if not user:
        return jsonify({"error": "Invalid Credentials"}), 401

    secret = user['two_factor_secret']
    totp = pyotp.TOTP(secret)
    
    if totp.verify(code_input):
        return jsonify({"message": "Success"}), 200
    else:
        return jsonify({"error": "Invalid 2FA Code"}), 401

@app.route('/api/add_password', methods=['POST'])
def add_password_entry():
    data = request.json
    username = data.get('username')
    master_password = data.get('master_password') 
    
    site_name = data.get('site_name')
    site_username = data.get('site_username')
    site_password_plain = data.get('site_password')

    user = authenticate_user(username, master_password)
    if not user:
        return jsonify({"error": "Invalid Credentials"}), 401

    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)
    encrypted_pw = crypto_manager.encrypt_val(encryption_key, site_password_plain)

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO passwords (user_id, site_name, site_username, encrypted_password)
        VALUES (?, ?, ?, ?)
    ''', (user['id'], site_name, site_username, encrypted_pw))
    conn.commit()
    conn.close()

    return jsonify({"message": "Password Saved"}), 201

@app.route('/api/get_passwords', methods=['POST'])
def get_all_passwords():
    data = request.json
    username = data.get('username')
    master_password = data.get('master_password')

    user = authenticate_user(username, master_password)
    if not user:
        return jsonify({"error": "Invalid Credentials"}), 401

    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)

    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM passwords WHERE user_id = ?', (user['id'],)).fetchall()
    conn.close()

    results = []
    for row in rows:
        decrypted_pw = crypto_manager.decrypt_val(encryption_key, row['encrypted_password'])
        results.append({
            "site": row['site_name'],
            "username": row['site_username'],
            "password": decrypted_pw
        })

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)