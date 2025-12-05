import psycopg2
import pyotp 
import crypto_manager
import os
from dotenv import load_dotenv

# Load the connection string from .env
load_dotenv()

def register_user():
    print("--- CREATE ADMIN USER (CLOUD) ---")
    username = input("Enter a username: ")
    password = input("Enter a MASTER password: ")

    # 1. Generate the security bits
    salt = crypto_manager.generate_salt()
    password_hash = crypto_manager.hash_master_password(password, salt)
    two_factor_secret = pyotp.random_base32()

    # 2. Connect to NEON (Cloud)
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()

        # Postgres uses %s for placeholders
        cur.execute('''
            INSERT INTO users (username, password_hash, salt, two_factor_secret)
            VALUES (%s, %s, %s, %s)
        ''', (username, password_hash, salt.hex(), two_factor_secret))
        
        conn.commit()
        print(f"\nSUCCESS: User '{username}' created in the Cloud Database!")
        print(f"2FA Secret: {two_factor_secret}") 
        print("(You will need this secret in a moment to set up your phone app)")
        
        cur.close()
        conn.close()
        
    except psycopg2.errors.UniqueViolation:
        print("\nERROR: That username already exists in the Cloud DB.")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == '__main__':
    register_user()