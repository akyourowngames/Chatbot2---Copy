"""
Test Firebase Connection
=========================
Quick test to verify Firebase is configured correctly
"""

from Backend.FirebaseStorage import get_firebase_storage
from Backend.FirebaseAuth import FirebaseAuth
from Backend.FirebaseDAL import FirebaseDAL

def test_firebase_connection():
    """Test Firebase connection and components"""
    
    print("=" * 60)
    print("🔥 Testing Firebase Connection")
    print("=" * 60)
    
    # Test 1: Firebase Storage
    print("\n1. Testing Firebase Storage...")
    try:
        storage = get_firebase_storage()
        if storage and storage.db:
            print("   ✅ Firebase Storage connected successfully!")
            print(f"   Project ID: {storage.db.project}")
        else:
            print("   ❌ Firebase Storage connection failed")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Firebase Authentication
    print("\n2. Testing Firebase Authentication...")
    try:
        auth = FirebaseAuth(storage.db)
        print("   ✅ FirebaseAuth initialized successfully!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Firebase DAL
    print("\n3. Testing Firebase DAL...")
    try:
        dal = FirebaseDAL(storage.db)
        print("   ✅ FirebaseDAL initialized successfully!")
        
        # Test cache
        cache_stats = dal.get_cache_stats()
        print(f"   Cache size: {cache_stats['size']}/{cache_stats['max_size']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 4: Environment Variables
    print("\n4. Checking Environment Variables...")
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_CREDENTIALS_PATH',
        'JWT_SECRET_KEY',
        'ENCRYPTION_KEY'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value and not value.startswith('your_'):
            print(f"   ✅ {var} is set")
        else:
            print(f"   ❌ {var} is NOT set or using default value")
            all_set = False
    
    if not all_set:
        print("\n   ⚠️  Please update your .env file with actual values")
        print("   See FIREBASE_SETUP_GUIDE.md for instructions")
    
    # Final Summary
    print("\n" + "=" * 60)
    if all_set:
        print("🎉 All Firebase components are working correctly!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start API server: python api_server.py")
        print("2. Test signup: curl -X POST http://localhost:5000/api/v1/auth/signup \\")
        print("                     -H 'Content-Type: application/json' \\")
        print("                     -d '{\"email\":\"test@example.com\",\"password\":\"Test123!\"}'")
        return True
    else:
        print("⚠️  Firebase setup incomplete")
        print("=" * 60)
        print("\nPlease complete the setup:")
        print("1. Follow FIREBASE_SETUP_GUIDE.md")
        print("2. Update .env with your Firebase credentials")
        print("3. Run this test again")
        return False

if __name__ == "__main__":
    test_firebase_connection()
