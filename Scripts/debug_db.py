
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase
cred_path = "kai-g-80f9c-firebase-adminsdk-fbsvc-6b239cc1a6.json"
if not os.path.exists(cred_path):
    print(f"Error: {cred_path} not found")
    exit(1)

cred = credentials.Certificate(cred_path)
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

db = firestore.client()

print("--- DEBUGGING FIRESTORE SPECIFIC USERS ---")

# User IDs to check (UID and Email)
target_ids = ["SAz2OrkFIpUSwuVOGhXI", "test@gmail.com"]

for user_id in target_ids:
    print(f"\nScanning User ID: {user_id}")
    
    # Check messages collection existence
    msgs_ref = db.collection('messages').document(user_id).collection('messages').limit(5).stream()
    count = 0
    sample_conv_id = None
    for msg in msgs_ref:
        data = msg.to_dict()
        print(f"   [FOUND MSG] ID: {msg.id} | ConvID: {data.get('conversation_id')}")
        if not sample_conv_id:
            sample_conv_id = data.get('conversation_id')
        count += 1
    
    print(f"   Total Messages Found: {count}")
    
    if count > 0 and sample_conv_id:
        print(f"   Testing Query Filter on ConvID: {sample_conv_id}")
        query = db.collection('messages').document(user_id).collection('messages')
        query = query.where("conversation_id", "==", sample_conv_id)
        results = query.stream()
        matches = 0
        for m in results:
            matches += 1
        print(f"   Query Matches: {matches}")
    else:
        print("   No messages found for this ID.")

