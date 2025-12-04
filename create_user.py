import sqlite3
import pyotp # Generates the 2FA secret
import crypto_manager # Our own math logic

def register_user():
    print("--- CREATE ADMIN USER ---")
    username = input("Enter a username: ")
    password = input("Enter a MASTER password: ")

    # 1. Generate the security bits
    # Create a random salt (raw bytes)
    salt = crypto_manager.generate_salt()
    
    # Hash the password (returns a string)
    password_hash = crypto_manager.hash_master_password(password, salt)
    
    # Generate a random 2FA Secret Key (this is what the QR code contains)
    two_factor_secret = pyotp.random_base32()

    # 2. Save to Database
    conn = sqlite3.connect('vault.db')
    cursor = conn.cursor()

    try:
        # Note: We convert 'salt' to a Hex String (.hex()) so it stores safely as text
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, two_factor_secret)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, salt.hex(), two_factor_secret))
        
        conn.commit()
        print(f"\nSUCCESS: User '{username}' created.")
        print(f"2FA Secret: {two_factor_secret}") 
        print("(You will need this secret in a moment to set up your phone app)")
        
    except sqlite3.IntegrityError:
        print("\nERROR: That username already exists.")
    finally:
        conn.close()

if __name__ == '__main__':
    register_user()