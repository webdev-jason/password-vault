import psycopg2
import os
from dotenv import load_dotenv

# Load the connection string from .env
load_dotenv()

def create_tables():
    print("Connecting to Neon Database...")
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cur = conn.cursor()

    # 1. Create Users Table
    # Note: 'SERIAL' is the Postgres way of saying Auto-Increment
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            two_factor_secret TEXT
        )
    ''')

    # 2. Create Passwords Table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            site_name TEXT NOT NULL,
            site_username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    cur.close()
    conn.close()
    print("SUCCESS: Tables created in the Cloud!")

if __name__ == '__main__':
    create_tables()