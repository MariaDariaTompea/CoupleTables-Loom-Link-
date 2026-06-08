import os
import sqlite3
import string
import random
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

URL: str = os.getenv("SUPABASE_URL", "")
KEY: str = os.getenv("SUPABASE_KEY", "")

class Database:
    def __init__(self):
        self.db_path = "loom.db"
        self._init_sqlite()
        if not URL or not KEY:
            print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment. Running in local SQLite mode.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(URL, KEY)
                print("Successfully connected to Supabase.")
            except Exception as e:
                print(f"Failed to connect to Supabase: {e}. Falling back to SQLite.")
                self.client = None

    def _init_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                region TEXT DEFAULT 'UTC'
            )
        """)
        
        # Create couples (bonds) table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS couples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                created_at TEXT,
                FOREIGN KEY(user1_id) REFERENCES users(id),
                FOREIGN KEY(user2_id) REFERENCES users(id)
            )
        """)
        
        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                couple_id INTEGER,
                title TEXT,
                desc TEXT,
                start_time TEXT,
                end_time TEXT,
                color_index INTEGER,
                FOREIGN KEY(couple_id) REFERENCES couples(id)
            )
        """)
        
        # Create pairing_codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pairing_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code TEXT UNIQUE,
                expires_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Create connection_attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                entered_code TEXT,
                created_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Seed test1 and test2 accounts
        cursor.execute("SELECT id FROM users WHERE name = 'test1'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (name, email, password, region)
                VALUES ('test1', 'test1@example.com', 'test1', 'Europe/Rome')
            """)
        
        cursor.execute("SELECT id FROM users WHERE name = 'test2'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (name, email, password, region)
                VALUES ('test2', 'test2@example.com', 'test2', 'America/New_York')
            """)
            
        conn.commit()
        conn.close()

    def validate_code(self, code):
        """Validates passwords/secret codes: between 4 and 25 characters"""
        return 4 <= len(code) <= 25

    def login_user(self, name, password):
        """Log in a user by name and password"""
        print(f"DB: Attempting login for username: {name}")
        
        # Supabase mode (fallback to SQLite on missing tables or errors)
        if self.client:
            try:
                res = self.client.table("users").select("*").eq("name", name).eq("secret_code", password).execute()
                if res.data:
                    print(f"DB (Supabase): Found user {res.data[0]['id']}")
                    return res.data[0]
            except Exception as e:
                print(f"DB (Supabase) login error: {e}. Trying local SQLite...")
        
        # SQLite fallback
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ? AND password = ?", (name, password))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            print(f"DB (SQLite): Logged in user: {row['name']} (ID: {row['id']})")
            return dict(row)
        else:
            print("DB (SQLite): User not found or incorrect credentials.")
            return None

    def create_user(self, name, email, password, region):
        """Create a new user"""
        print(f"DB: Creating new user: {name}")
        
        # Supabase mode
        if self.client:
            try:
                data = {
                    "name": name,
                    "secret_code": password, # map secret_code to password for backwards compatibility
                    "region": region
                }
                res = self.client.table("users").insert(data).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"DB (Supabase) create error: {e}. Trying local SQLite...")

        # SQLite fallback
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, region)
                VALUES (?, ?, ?, ?)
            """, (name, email, password, region))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "password": password,
                "region": region
            }
        except sqlite3.IntegrityError:
            conn.close()
            print("DB (SQLite): Username already exists.")
            return None
        except Exception as e:
            conn.close()
            print(f"DB (SQLite) error: {e}")
            raise e

    def update_profile(self, user_id, name, password, region):
        """Update user profile details"""
        print(f"DB: Updating profile for user {user_id}")
        
        # Supabase mode
        if self.client and not isinstance(user_id, int):
            try:
                self.client.table("users").update({
                    "name": name,
                    "secret_code": password,
                    "region": region
                }).eq("id", user_id).execute()
            except Exception as e:
                print(f"DB (Supabase) update profile error: {e}. Trying local SQLite...")
        
        # SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET name = ?, password = ?, region = ?
            WHERE id = ?
        """, (name, password, region, user_id))
        conn.commit()
        conn.close()
        return True

    def generate_pairing_code(self, user_id):
        """Generates a 5-minute expiration 20-character pairing code"""
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = ''.join(random.choices(alphabet, k=20))
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        
        # Supabase mode
        if self.client and not isinstance(user_id, int):
            try:
                self.client.table("pairing_codes").delete().eq("user_id", user_id).execute()
                self.client.table("pairing_codes").insert({
                    "user_id": user_id,
                    "code": code,
                    "expires_at": expires_at
                }).execute()
                return code
            except Exception as e:
                print(f"DB (Supabase) pairing code error: {e}. Trying SQLite...")
 
        # SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pairing_codes WHERE user_id = ?", (user_id,))
        cursor.execute("""
            INSERT INTO pairing_codes (user_id, code, expires_at)
            VALUES (?, ?, ?)
        """, (user_id, code, expires_at))
        conn.commit()
        conn.close()
        return code
 
    def submit_pairing_code(self, user_id, partner_code):
        """
        Record a connection attempt. 
        If user_id inputs partner_code (which belongs to Partner), we check:
        Has Partner also input user_id's active pairing code?
        If yes, we establish the bond!
        """
        partner_code = partner_code.strip().upper().replace('0', 'O').replace('1', 'I')
        now_str = datetime.now(timezone.utc).isoformat()
        
        # Supabase mode
        if self.client and not isinstance(user_id, int):
            try:
                # 1. Verify partner_code is active and get partner's user ID
                res = self.client.table("pairing_codes").select("*").eq("code", partner_code).execute()
                if not res.data:
                    print("DB (Supabase): Code not found.")
                    return False
                
                record = res.data[0]
                partner_id = record["user_id"]
                expires_at = record["expires_at"]
                
                # Check expiration
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > expires_dt:
                    print("DB (Supabase): Code expired.")
                    self.client.table("pairing_codes").delete().eq("code", partner_code).execute()
                    return False
                
                if partner_id == user_id:
                    print("DB (Supabase): Cannot pair with yourself.")
                    return False
                
                # 2. Check if couple already exists
                existing1 = self.client.table("couples").select("id").eq("user1_id", user_id).eq("user2_id", partner_id).execute()
                existing2 = self.client.table("couples").select("id").eq("user1_id", partner_id).eq("user2_id", user_id).execute()
                
                if not existing1.data and not existing2.data:
                    # Insert couple row
                    self.client.table("couples").insert({
                        "user1_id": user_id,
                        "user2_id": partner_id
                    }).execute()
                
                # 3. Clean up pairing codes for both users
                self.client.table("pairing_codes").delete().eq("user_id", partner_id).execute()
                self.client.table("pairing_codes").delete().eq("user_id", user_id).execute()
                
                return True
            except Exception as e:
                print(f"DB (Supabase) submit_pairing_code error: {e}. Falling back to SQLite...")

        # SQLite fallback
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. Verify partner_code is active and get partner's user ID
            cursor.execute("SELECT user_id, expires_at FROM pairing_codes WHERE code = ?", (partner_code,))
            res = cursor.fetchone()
            if not res:
                print("DB: Code not found.")
                conn.close()
                return False
            
            partner_id, expires_at = res
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_dt:
                print("DB: Code expired.")
                conn.close()
                return False
            
            if partner_id == user_id:
                print("DB: Cannot pair with yourself.")
                conn.close()
                return False
                
            # 2. Record this user's attempt
            cursor.execute("""
                INSERT INTO connection_attempts (user_id, entered_code, created_at)
                VALUES (?, ?, ?)
            """, (user_id, partner_code, now_str))
            
            # 3. Retrieve user_id's active pairing code to check if partner has entered it
            cursor.execute("SELECT code FROM pairing_codes WHERE user_id = ?", (user_id,))
            user_code_res = cursor.fetchone()
            
            is_paired = False
            if user_code_res:
                user_code = user_code_res[0]
                # Check if partner has submitted user_code
                cursor.execute("""
                    SELECT id FROM connection_attempts 
                    WHERE user_id = ? AND UPPER(entered_code) = ?
                """, (partner_id, user_code))
                partner_attempt = cursor.fetchone()
                
                if partner_attempt:
                    # Mutual match! Establish couple bond
                    # Check if couple already exists
                    cursor.execute("""
                        SELECT id FROM couples 
                        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
                    """, (user_id, partner_id, partner_id, user_id))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO couples (user1_id, user2_id, created_at)
                            VALUES (?, ?, ?)
                        """, (user_id, partner_id, now_str))
                    
                    # Clean up pairing codes and attempts
                    cursor.execute("DELETE FROM pairing_codes WHERE user_id = ? OR user_id = ?", (user_id, partner_id))
                    cursor.execute("DELETE FROM connection_attempts WHERE user_id = ? OR user_id = ?", (user_id, partner_id))
                    is_paired = True
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"DB Error in submit_pairing_code: {e}")
            return False

    def get_couple_id(self, user_id):
        """Get the couple/bond ID between user_id and their partner"""
        if self.client and not isinstance(user_id, int):
            try:
                res = self.client.table("couples").select("id").or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}").execute()
                return res.data[0]['id'] if res.data else None
            except Exception:
                pass
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM couples WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def fetch_user_bonds(self, user_id):
        """Retrieve all bonds (couples) for a user along with partner details"""
        if self.client and not isinstance(user_id, int):
            try:
                # In Supabase we try to fetch couples
                res = self.client.table("couples").select("id, user1_id, user2_id").or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}").execute()
                bonds = []
                for item in res.data:
                    partner_id = item['user2_id'] if item['user1_id'] == user_id else item['user1_id']
                    # Fetch partner name
                    p_res = self.client.table("users").select("name").eq("id", partner_id).execute()
                    partner_name = p_res.data[0]['name'] if p_res.data else f"User {partner_id}"
                    bonds.append({
                        "id": item['id'],
                        "partner_name": partner_name,
                        "partner_id": partner_id
                    })
                return bonds
            except Exception as e:
                print(f"DB (Supabase) fetch bonds error: {e}. Trying SQLite...")

        # SQLite
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.user1_id, c.user2_id, u.name AS partner_name, u.id AS partner_id
            FROM couples c
            JOIN users u ON (c.user1_id = u.id AND c.user2_id = ?) 
                         OR (c.user2_id = u.id AND c.user1_id = ?)
            WHERE c.user1_id = ? OR c.user2_id = ?
        """, (user_id, user_id, user_id, user_id))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def fetch_bond_events(self, couple_id):
        """Fetch all events for a specific couple ID"""
        if self.client and not isinstance(couple_id, int):
            try:
                res = self.client.table("events").select("*").eq("couple_id", couple_id).execute()
                # Map 'description' to 'desc' for code consistency
                events_list = []
                for item in res.data:
                    ev = dict(item)
                    if "description" in ev:
                        ev["desc"] = ev.pop("description")
                    events_list.append(ev)
                return events_list
            except Exception as e:
                print(f"DB (Supabase) fetch events error: {e}. Trying SQLite...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE couple_id = ?", (couple_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_event(self, couple_id, title, desc, start_time, end_time, color_index):
        """Insert a new schedule event into the database"""
        print(f"DEBUG: add_event called: couple_id={couple_id}, title={title}, start_time={start_time}, end_time={end_time}, color_index={color_index}, client_exists={self.client is not None}", flush=True)
        if self.client and not isinstance(couple_id, int):
            try:
                data = {
                    "couple_id": couple_id,
                    "title": title,
                    "description": desc, # Map 'desc' to 'description'
                    "start_time": start_time, # ISO UTC
                    "end_time": end_time,
                    "color_index": color_index
                }
                return self.client.table("events").insert(data).execute()
            except Exception as e:
                print(f"DB (Supabase) add event error: {e}. Trying SQLite...")

        # SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (couple_id, title, desc, start_time, end_time, color_index)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (couple_id, title, desc, start_time, end_time, color_index))
        conn.commit()
        conn.close()
        return True

db = Database()
