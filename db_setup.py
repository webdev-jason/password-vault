import sqlite3

def create_tables():
    # Connect to the database. 
    # If 'vault.db' doesn't exist, this line creates it automatically.
    conn = sqlite3.connect('vault.db')
    cursor = conn.cursor()

    # 1. Create the Users table
    # We store 'salt' and 'password_hash' instead of the real password.
    # We store 'two_factor_secret' for the authenticator app.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            two_factor_secret TEXT
        )
    ''')

    # 2. Create the Passwords table
    # 'encrypted_password' will hold the gibberish string we create later.
    # 'user_id' links this password to the user above (Foreign Key).
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            site_name TEXT NOT NULL,
            site_username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database structure created successfully in 'vault.db'.")

if __name__ == '__main__':
    create_tables()