import requests

BASE_URL = 'http://127.0.0.1:5000/api'

def run_test():
    print("--- VAULT OPERATION TEST ---")
    user = input("Username: ")
    master_pw = input("Master Password: ")
    
    # 1. ADD A PASSWORD
    print("\nAttempting to add 'Netflix'...")
    payload_add = {
        "username": user,
        "master_password": master_pw,
        "site_name": "Netflix",
        "site_username": "cool_guy@email.com",
        "site_password": "SuperSecretNetflixPassword123"
    }
    
    resp = requests.post(f"{BASE_URL}/add_password", json=payload_add)
    print(f"Add Status: {resp.status_code}")
    print(f"Add Response: {resp.json()}")

    if resp.status_code != 201:
        print("Stopping test due to error.")
        return

    # 2. RETRIEVE PASSWORDS
    print("\nAttempting to retrieve passwords...")
    payload_get = {
        "username": user,
        "master_password": master_pw
    }
    
    resp = requests.post(f"{BASE_URL}/get_passwords", json=payload_get)
    
    if resp.status_code == 200:
        passwords = resp.json()
        print(f"\nSUCCESS! Found {len(passwords)} entries:")
        for p in passwords:
            print(f" - Site: {p['site']}")
            print(f"   User: {p['username']}")
            print(f"   Pass: {p['password']}") # Should be readable!
    else:
        print("Failed to retrieve.")
        print(resp.json())

if __name__ == '__main__':
    run_test()