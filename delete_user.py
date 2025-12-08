import psycopg2
import os
from dotenv import load_dotenv

# Load the connection string from .env
load_dotenv()

def force_delete_user():
    print("--- ADMIN: FORCE DELETE USER ---")
    username = input("Enter the username to delete: ").strip()

    if not username:
        print("Operation cancelled.")
        return

    confirm = input(f"⚠️  Are you sure you want to permanently delete '{username}'? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()

        # 1. Get User ID
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if not user:
            print(f"❌ User '{username}' not found.")
            return

        user_id = user[0]

        # 2. Delete all passwords belonging to this user (Foreign Key cleanup)
        cur.execute("DELETE FROM passwords WHERE user_id = %s", (user_id,))
        passwords_deleted = cur.rowcount

        # 3. Delete the user record
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        conn.commit()
        
        print(f"\n✅ SUCCESS: User '{username}' deleted.")
        print(f"🗑️  Also removed {passwords_deleted} password entries belonging to them.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == '__main__':
    force_delete_user()