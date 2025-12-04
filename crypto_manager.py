import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# 1. UTILITY: Generate a random salt
# A 'salt' is random data added to a password before hashing. 
# It ensures that if two users have the password "123456", 
# their hashes look completely different.
def generate_salt():
    return os.urandom(16) # Returns 16 random bytes

# 2. HASHING: For the Master Password (One-Way)
def hash_master_password(plain_password, salt):
    # We use PBKDF2, a standard algorithm that is intentionally slow 
    # to stop hackers from guessing billions of passwords a second.
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000, # Repeat the math 480,000 times
    )
    # We encode it in base64 so it's safe to store as text in the DB
    return base64.urlsafe_b64encode(kdf.derive(plain_password.encode())).decode()

def verify_master_password(plain_password, stored_salt_hex, stored_hash):
    # To verify, we just run the same math on the input
    # and check if the result matches what we have in the DB.
    
    # Convert the stored salt from Hex (text) back to bytes
    salt_bytes = bytes.fromhex(stored_salt_hex)
    
    new_hash = hash_master_password(plain_password, salt_bytes)
    return new_hash == stored_hash

# 3. ENCRYPTION KEY DERIVATION
# We turn the Master Password into a key for the "Safe"
def derive_encryption_key(master_password, salt_bytes):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt_bytes,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

# 4. ENCRYPTION: For the Vault Data (Two-Way)
def encrypt_val(key, plain_text):
    f = Fernet(key)
    # Fernet handles the heavy lifting of AES encryption
    return f.encrypt(plain_text.encode()).decode()

def decrypt_val(key, encrypted_text):
    f = Fernet(key)
    return f.decrypt(encrypted_text.encode()).decode()