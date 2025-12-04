from flask import Flask, request, jsonify
import sqlite3
import pyotp
import crypto_manager

app = Flask(__name__)

# UTILITY: Database Connection
def get_db_connection():
    conn = sqlite3.connect('vault.db')
    conn.row_factory = sqlite3.Row 
    return conn

# UTILITY: Auth Helper (DRY Principle - Don't Repeat Yourself)
# We need to verify the user for every single action (add, view, delete).
# Instead of writing this code 3 times, we write it once here.
def authenticate_user(username, master_password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user is None:
        return None
    
    # Verify the hash matches
    stored_salt = user['salt']
    stored_hash = user['password_hash']
    
    if crypto_manager.verify_master_password(master_password, stored_salt, stored_hash):
        return user
    else:
        return None

# --- ENDPOINTS ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password_input = data.get('password')
    code_input = data.get('2fa_code')

    # 1. Verify User & Password
    user = authenticate_user(username, password_input)
    if not user:
        return jsonify({"error": "Invalid Credentials"}), 401

    # 2. Verify 2FA
    secret = user['two_factor_secret']
    totp = pyotp.TOTP(secret)
    
    if totp.verify(code_input):
        return jsonify({"message": "LOGIN SUCCESSFUL! Vault Unlocked."}), 200
    else:
        return jsonify({"error": "Invalid 2FA Code"}), 401

@app.route('/api/add_password', methods=['POST'])
def add_password_entry():
    data = request.json
    username = data.get('username')
    master_password = data.get('master_password') # Needed to generate the encryption key
    
    site_name = data.get('site_name')
    site_username = data.get('site_username')
    site_password_plain = data.get('site_password')

    # 1. Authenticate (We don't need 2FA for adding, just the master password check)
    user = authenticate_user(username, master_password)
    if not user:
        return jsonify({"error": "Invalid Credentials"}), 401

    # 2. Derive the Encryption Key
    # We need the user's specific salt to recreate the key
    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)

    # 3. Encrypt the data
    encrypted_pw = crypto_manager.encrypt_val(encryption_key, site_password_plain)

    # 4. Save to DB
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO passwords (user_id, site_name, site_username, encrypted_password)
        VALUES (?, ?, ?, ?)
    ''', (user['id'], site_name, site_username, encrypted_pw))
    conn.commit()
    conn.close()

    return jsonify({"message": "Password Saved & Encrypted"}), 201

@app.route('/api/get_passwords', methods=['POST'])
def get_all_passwords():
    # Note: This is a POST request because we are sending the master_password securely in the body.
    # A GET request would put the password in the URL history (BAD idea).
    
    data = request.json
    username = data.get('username')
    master_password = data.get('master_password')

    # 1. Authenticate
    user = authenticate_user(username, master_password)
    if not user:
        return jsonify({"error": "Invalid Credentials"}), 401

    # 2. Derive Key
    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)

    # 3. Fetch from DB
    conn = get_db_connection()
    # We only get passwords belonging to THIS user (user['id'])
    rows = conn.execute('SELECT * FROM passwords WHERE user_id = ?', (user['id'],)).fetchall()
    conn.close()

    # 4. Decrypt Results
    results = []
    for row in rows:
        decrypted_pw = crypto_manager.decrypt_val(encryption_key, row['encrypted_password'])
        results.append({
            "site": row['site_name'],
            "username": row['site_username'],
            "password": decrypted_pw # Sending back the plain text!
        })

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)