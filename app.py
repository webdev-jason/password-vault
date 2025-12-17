from flask import Flask, request, jsonify, render_template, make_response
import psycopg2
from psycopg2.extras import RealDictCursor
import pyotp
import crypto_manager
import jwt 
import datetime
import os
import qrcode
import base64
from io import BytesIO
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# UTILITY: Database Connection
def get_db_connection():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return conn

# UTILITY: The "Bouncer"
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'token' in request.cookies:
            token = request.cookies.get('token')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user_id, *args, **kwargs)
    
    return decorated

def verify_password_logic(user_id, master_password):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user: return None
    
    if crypto_manager.verify_master_password(master_password, user['salt'], user['password_hash']):
        return user
    return None

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    # MOBILE FIX: Strip whitespace automatically
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # 1. Validation
    if not username or not password:
        return jsonify({"error": "Username and Password required"}), 400
        
    banned_chars = [' ', '\t', '\n', '\r', '\\', '^', '~', '"', "'", '{', '}', '[', ']', '|', ';']
    
    # Check Password
    for char in banned_chars:
        if char in password:
            return jsonify({"error": "Password contains invalid characters"}), 400
            
    # Check Username for banned chars too
    for char in banned_chars:
        if char in username:
            return jsonify({"error": "Username contains invalid characters"}), 400
            
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 2. Check if exists
        cur.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            return jsonify({"error": "Username already exists"}), 400

        # 3. Create Credentials
        salt = crypto_manager.generate_salt()
        password_hash = crypto_manager.hash_master_password(password, salt)
        two_factor_secret = pyotp.random_base32()

        # 4. Save to DB
        cur.execute('''
            INSERT INTO users (username, password_hash, salt, two_factor_secret)
            VALUES (%s, %s, %s, %s)
        ''', (username, password_hash, salt.hex(), two_factor_secret))
        conn.commit()

        # 5. Generate QR Code
        totp_uri = pyotp.totp.TOTP(two_factor_secret).provisioning_uri(name=username, issuer_name="Password Vault")
        
        img = qrcode.make(totp_uri)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return jsonify({
            "message": "User created", 
            "qr_code": qr_b64, 
            "secret": two_factor_secret,
            "totp_uri": totp_uri 
        }), 201

    except Exception as e:
        conn.rollback()
        print(f"Register Error: {e}") # Log internally
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    # MOBILE FIX: Strip whitespace to handle auto-correct spaces
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user: return jsonify({"error": "User not found"}), 404

    if not crypto_manager.verify_master_password(password, user['salt'], user['password_hash']):
        return jsonify({"error": "Invalid Password"}), 401
    
    totp = pyotp.TOTP(user['two_factor_secret'])
    if not totp.verify(data.get('2fa_code')):
        return jsonify({"error": "Invalid 2FA Code"}), 401

    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    resp = make_response(jsonify({
        "message": "Login Successful", 
        "username": user['username']  
    }))
    resp.set_cookie('token', token, httponly=True, samesite='Strict')
    
    return resp, 200

@app.route('/api/logout', methods=['POST'])
def logout():
    resp = make_response(jsonify({"message": "Logged out"}))
    resp.set_cookie('token', '', expires=0)
    return resp, 200

@app.route('/api/check_session', methods=['GET'])
@token_required
def check_session(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT username FROM users WHERE id = %s', (current_user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return jsonify({"status": "valid", "user_id": current_user_id, "username": user['username']}), 200
    return jsonify({"message": "User not found"}), 401

@app.route('/api/add_password', methods=['POST'])
@token_required 
def add_password_entry(current_user_id):
    data = request.json
    master_password = data.get('master_password') 
    
    user = verify_password_logic(current_user_id, master_password)
    if not user: return jsonify({"error": "Invalid Password"}), 401

    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)
    encrypted_pw = crypto_manager.encrypt_val(encryption_key, data.get('site_password'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO passwords (user_id, site_name, site_username, encrypted_password)
        VALUES (%s, %s, %s, %s)
    ''', (current_user_id, data.get('site_name'), data.get('site_username'), encrypted_pw))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Password Saved"}), 201

@app.route('/api/get_passwords', methods=['POST'])
@token_required
def get_all_passwords(current_user_id):
    data = request.json
    master_password = data.get('master_password')

    user = verify_password_logic(current_user_id, master_password)
    if not user: return jsonify({"error": "Invalid Password"}), 401

    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, site_name, site_username, encrypted_password FROM passwords WHERE user_id = %s', (current_user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for row in rows:
        try:
            decrypted_pw = crypto_manager.decrypt_val(encryption_key, row['encrypted_password'])
            results.append({
                "id": row['id'],
                "site": row['site_name'],
                "username": row['site_username'],
                "password": decrypted_pw
            })
        except Exception: pass

    return jsonify(results), 200

@app.route('/api/update_password', methods=['PUT'])
@token_required
def update_password_entry(current_user_id):
    data = request.json
    password_id = data.get('id')
    master_password = data.get('master_password')
    
    user = verify_password_logic(current_user_id, master_password)
    if not user: return jsonify({"error": "Invalid Password"}), 401

    salt_bytes = bytes.fromhex(user['salt'])
    encryption_key = crypto_manager.derive_encryption_key(master_password, salt_bytes)
    encrypted_pw = crypto_manager.encrypt_val(encryption_key, data.get('site_password'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE passwords 
        SET site_name = %s, site_username = %s, encrypted_password = %s
        WHERE id = %s AND user_id = %s
    ''', (data.get('site_name'), data.get('site_username'), encrypted_pw, password_id, current_user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Updated successfully"}), 200

@app.route('/api/delete_password', methods=['DELETE'])
@token_required
def delete_password_entry(current_user_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM passwords WHERE id = %s AND user_id = %s', (data.get('id'), current_user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Deleted successfully"}), 200

@app.route('/api/update_account', methods=['POST'])
@token_required
def update_account(current_user_id):
    data = request.json
    current_password = data.get('current_password')
    new_username = data.get('new_username')
    new_password = data.get('new_password')

    banned_chars = [' ', '\t', '\n', '\r', '\\', '^', '~', '"', "'", '{', '}', '[', ']', '|', ';']
    if new_password:
        for char in banned_chars:
            if char in new_password:
                return jsonify({"error": "Password contains invalid characters"}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('SELECT * FROM users WHERE id = %s', (current_user_id,))
    user = cur.fetchone()

    if not crypto_manager.verify_master_password(current_password, user['salt'], user['password_hash']):
        cur.close()
        conn.close()
        return jsonify({"error": "Current Password incorrect"}), 401

    try:
        if new_username and new_username != user['username']:
            cur.execute('SELECT id FROM users WHERE username = %s', (new_username,))
            if cur.fetchone():
                raise Exception("Username already taken")
            cur.execute('UPDATE users SET username = %s WHERE id = %s', (new_username, current_user_id))

        if new_password:
            old_salt_bytes = bytes.fromhex(user['salt'])
            old_key = crypto_manager.derive_encryption_key(current_password, old_salt_bytes)

            cur.execute('SELECT id, encrypted_password FROM passwords WHERE user_id = %s', (current_user_id,))
            rows = cur.fetchall()

            new_salt = crypto_manager.generate_salt()
            new_hash = crypto_manager.hash_master_password(new_password, new_salt)
            new_key = crypto_manager.derive_encryption_key(new_password, new_salt)

            for row in rows:
                decrypted = crypto_manager.decrypt_val(old_key, row['encrypted_password'])
                re_encrypted = crypto_manager.encrypt_val(new_key, decrypted)
                cur.execute('UPDATE passwords SET encrypted_password = %s WHERE id = %s', (re_encrypted, row['id']))

            cur.execute('UPDATE users SET password_hash = %s, salt = %s WHERE id = %s', 
                        (new_hash, new_salt.hex(), current_user_id))

        conn.commit()
        return jsonify({"message": "Account updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Account Update Error: {e}") # Log internally
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        cur.close()
        conn.close()

# NEW: Delete Account Route
@app.route('/api/delete_account', methods=['DELETE'])
@token_required
def delete_account(current_user_id):
    data = request.json
    password_check = data.get('password', '').strip() # MOBILE FIX: Strip whitespace
    
    # 1. Verify Password again before deleting
    user = verify_password_logic(current_user_id, password_check)
    if not user: return jsonify({"error": "Invalid Password"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Delete all passwords first
        cur.execute('DELETE FROM passwords WHERE user_id = %s', (current_user_id,))
        # Delete the user
        cur.execute('DELETE FROM users WHERE id = %s', (current_user_id,))
        conn.commit()
        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        print(f"Delete Account Error: {e}") # Log internally
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)