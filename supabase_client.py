from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY

supabase = None  # default to None

if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"[Analytics] Could not connect to Supabase: {e}")
else:
    print("[Analytics] No Supabase URL or key provided, skipping analytics.")