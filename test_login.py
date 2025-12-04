import requests # A library used to send requests to APIs

# This simulates what a frontend website would do
def test_login():
    print("--- LOGIN TEST CLIENT ---")
    
    # 1. Ask user for credentials
    user = input("Username: ")
    pw = input("Master Password: ")
    code = input("Current 6-digit 2FA Code from Phone: ")

    # 2. Bundle it into a JSON packet
    payload = {
        "username": user,
        "password": pw,
        "2fa_code": code
    }

    # 3. Send it to the API
    try:
        # We assume the server is running on localhost port 5000
        response = requests.post('http://127.0.0.1:5000/api/login', json=payload)
        
        # 4. Print the result
        print(f"\nStatus Code: {response.status_code}")
        print(f"Server Response: {response.json()}")
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server. Did you run 'python app.py'?")

if __name__ == '__main__':
    test_login()