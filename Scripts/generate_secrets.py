"""
Generate Secrets for Firebase Backend
======================================
Generates JWT secret and encryption key for .env file
"""

import secrets
from cryptography.fernet import Fernet

print("=" * 70)
print("🔐 Generating Secrets for Firebase Backend")
print("=" * 70)

print("\n📝 Copy these values to your .env file:\n")
print("-" * 70)

# Generate JWT Secret Key
jwt_secret = secrets.token_hex(64)
print(f"JWT_SECRET_KEY={jwt_secret}")

# Generate Encryption Key
encryption_key = Fernet.generate_key().decode()
print(f"ENCRYPTION_KEY={encryption_key}")

print("-" * 70)

print("\n✅ Secrets generated successfully!")
print("\nNext steps:")
print("1. Copy the values above")
print("2. Paste them into your .env file")
print("3. Add your Firebase credentials from Firebase Console")
print("4. Run: python test_firebase.py")

print("\n💡 Tip: Keep these secrets safe and NEVER commit them to git!")
