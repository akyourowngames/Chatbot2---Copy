import os
from supabase import create_client

# Load Supabase credentials from environment variables
SUPABASE_URL = 'https://skbfmcwrshxnmaxfqyaw.supabase.co'
SUPABASE_KEY = 'sb_secret_kT3r_lTsBYBLwpv313A0qQ_przZ-Q8v'

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError('Supabase credentials not set in environment variables')

# Create a Supabase client instance (storage only)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# The bucket name used for KAI file storage
BUCKET_NAME = 'kai-files'

def get_bucket():
    """Return the bucket reference, creating it if necessary."""
    try:
        # Check if bucket exists
        buckets = supabase.storage.list_buckets()
        bucket_exists = any(b.name == BUCKET_NAME for b in buckets)
        
        if not bucket_exists:
            # Create bucket if it doesn't exist
            supabase.storage.create_bucket(BUCKET_NAME, options={'public': True})
            
    except Exception as e:
        # If we can't list/create, proceed and hope it exists or error will be raised later
        pass
        
    return supabase.storage.from_(BUCKET_NAME)
