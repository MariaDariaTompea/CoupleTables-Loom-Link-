import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

URL: str = os.getenv("SUPABASE_URL", "")
KEY: str = os.getenv("SUPABASE_KEY", "")

class Database:
    def __init__(self):
        if not URL or not KEY:
            print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment.")
            self.client = None
        else:
            self.client: Client = create_client(URL, KEY)
    
    def validate_code(self, code):
        """As per documentation: length between 6 and 15"""
        return 6 <= len(code) <= 15

    def login_user(self, code):
        if not self.client: return None
        # Check if user exists, or create new
        res = self.client.table("users").select("*").eq("secret_code", code).execute()
        if res.data:
            return res.data[0]
        else:
            new_user = self.client.table("users").insert({"secret_code": code, "region": "UTC"}).execute()
            return new_user.data[0]

    def pair_partner(self, user_id, partner_code):
        if not self.client: return None
        # Find partner
        partner_res = self.client.table("users").select("*").eq("secret_code", partner_code).execute()
        if not partner_res.data:
            return False
        
        partner_id = partner_res.data[0]['id']
        # Create bidirectional link in 'couples' table
        self.client.table("couples").insert({"user1_id": user_id, "user2_id": partner_id}).execute()
        return True

    def get_couple_id(self, user_id):
        if not self.client: return None
        res = self.client.table("couples").select("id").or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}").execute()
        return res.data[0]['id'] if res.data else None

    def add_event(self, couple_id, title, desc, start_time, end_time, color_index):
        if not self.client: return None
        data = {
            "couple_id": couple_id,
            "title": title,
            "desc": desc,
            "start_time": start_time, # ISO string UTC
            "end_time": end_time,
            "color_index": color_index
        }
        return self.client.table("events").insert(data).execute()

    def fetch_events(self, couple_id):
        if not self.client: return []
        res = self.client.table("events").select("*").eq("couple_id", couple_id).execute()
        return res.data

db = Database()
