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
        return 5 <= len(code) <= 15

    def login_user(self, code):
        if not self.client: 
            print("DB Error: Client not initialized")
            return None
        print(f"DB: Checking for user with code: {code}")
        try:
            res = self.client.table("users").select("*").eq("secret_code", code).execute()
            if res.data:
                print(f"DB: Found existing user: {res.data[0]['id']}")
                return res.data[0]
            else:
                print("DB: User not found.")
                return None
        except Exception as e:
            print(f"DB Error in login_user: {e}")
            raise e

    def create_user(self, name, code):
        if not self.client: return None
        try:
            print(f"DB: Creating new user: {name}")
            new_user = self.client.table("users").insert({"name": name, "secret_code": code, "region": "UTC"}).execute()
            if new_user.data:
                return new_user.data[0]
            return None
        except Exception as e:
            print(f"DB Error in create_user: {e}")
            raise e

    def generate_pairing_code(self, user_id):
        if not self.client: return None
        import string
        import random
        from datetime import datetime, timedelta, timezone
        
        # Generate 20 char code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        
        try:
            # Delete old codes for this user
            self.client.table("pairing_codes").delete().eq("user_id", user_id).execute()
            # Insert new code
            self.client.table("pairing_codes").insert({
                "user_id": user_id,
                "code": code,
                "expires_at": expires_at
            }).execute()
            return code
        except Exception as e:
            print(f"DB Error in generate_pairing_code: {e}")
            return None

    def pair_with_code(self, user_id, pairing_code):
        if not self.client: return None
        from datetime import datetime, timezone
        
        try:
            # Find the code and ensure it hasn't expired
            res = self.client.table("pairing_codes").select("*").eq("code", pairing_code).execute()
            if not res.data:
                print("DB: Pairing code not found.")
                return False
            
            pairing_data = res.data[0]
            expires_at = datetime.fromisoformat(pairing_data['expires_at'].replace('Z', '+00:00'))
            
            if datetime.now(timezone.utc) > expires_at:
                print("DB: Pairing code expired.")
                return False
            
            partner_id = pairing_data['user_id']
            if partner_id == user_id:
                print("DB: Cannot pair with yourself.")
                return False

            # Create the couple link
            self.client.table("couples").insert({"user1_id": partner_id, "user2_id": user_id}).execute()
            # Delete the used code
            self.client.table("pairing_codes").delete().eq("code", pairing_code).execute()
            return True
        except Exception as e:
            print(f"DB Error in pair_with_code: {e}")
            return False

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
