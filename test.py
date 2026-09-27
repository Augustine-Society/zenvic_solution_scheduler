from supabase import create_client

SUPABASE_URL = "https://dmvdhuaysbimgwbfwydo.supabase.co"
SUPABASE_KEY = "sb_publishable_UTSSYpx9YQxMWP5m0I49Yw_qtBAuSMJ"

try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = client.table("workers").select("*").execute()
    print("Database connected successfully!")
    print("Workers in database:", response.data)
except Exception as e:
    print("Connection failed:", e)
