import qrcode
import pyotp

def make_qr():
    print("--- 2FA QR GENERATOR ---")
    
    # 1. Input the info you just created
    username = input("Enter the username (e.g., admin): ")
    secret = input("Paste the 2FA Secret you saved: ")
    
    # 2. Create the Provisioning URI
    # This creates the link: otpauth://totp/PasswordVault:admin?secret=...
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username, 
        issuer_name='PasswordVault'
    )
    
    # 3. Create the QR Code Image
    # We create a standard QR code object
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    # 4. Save it to a file
    img = qr.make_image(fill='black', back_color='white')
    filename = "2fa_qr.png"
    img.save(filename)
    
    print(f"\nSUCCESS: '{filename}' has been created in your folder.")
    print("Open this image file and scan it with your Authenticator App (Google/Authy/etc).")

if __name__ == '__main__':
    make_qr()