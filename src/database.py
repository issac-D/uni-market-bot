import sqlite3
import logging
import os  # <--- Added to handle folder creation
from src.config import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """Establishes a connection to the database, ensuring the folder exists first."""
    
    # --- FIX FOR RENDER: Create directory if it doesn't exist ---
    directory = os.path.dirname(DB_PATH)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    # -----------------------------------------------------------

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 1. USERS TABLE (Added 'location')
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        is_seller BOOLEAN DEFAULT 0,
        real_name TEXT,
        phone_number TEXT,
        id_number TEXT,
        location TEXT,                -- New: Main, Health, Mehal Meda, Outside
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_blocked BOOLEAN DEFAULT 0
    )
    ''')

    # 2. POSTS TABLE (Added 'condition')
    c.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        category TEXT,
        condition TEXT,               -- New: New / Used
        content TEXT,
        photo_id TEXT,
        hidden_detail TEXT,
        price TEXT,
        status TEXT DEFAULT 'PENDING',
        message_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    ''')
    
    # 3. INTERACTIONS (No changes)
    c.execute('''
    CREATE TABLE IF NOT EXISTS interactions (
        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        status TEXT DEFAULT 'PENDING',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized with v2 Schema")

# --- Helper Methods ---

def get_user(user_id):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def register_seller(user_id, username, real_name, phone_number, id_number, location):
    conn = get_connection()
    conn.execute('''
        INSERT OR REPLACE INTO users (user_id, username, is_seller, real_name, phone_number, id_number, location)
        VALUES (?, ?, 1, ?, ?, ?, ?)
    ''', (user_id, username, real_name, phone_number, id_number, location))
    conn.commit()
    conn.close()

def create_post(user_id, type, category, condition, content, price, photo_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO posts (user_id, type, category, condition, content, price, photo_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING')
    ''', (user_id, type, category, condition, content, price, photo_id))
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id

# New: Admin Tool
def get_all_users():
    conn = get_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users

def update_post_status(post_id, status):
    """Updates the status of a post (APPROVED, REJECTED, SOLD)."""
    conn = get_connection()
    conn.execute('UPDATE posts SET status = ? WHERE post_id = ?', (status, post_id))
    conn.commit()
    conn.close()

def update_post_message_id(post_id, message_id):
    """Links the database post to the actual Telegram Channel message."""
    conn = get_connection()
    conn.execute('UPDATE posts SET message_id = ? WHERE post_id = ?', (message_id, post_id))
    conn.commit()
    conn.close()

def get_post(post_id):
    """Fetch a single post (for admin review)."""
    conn = get_connection()
    post = conn.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,)).fetchone()
    conn.close()
    return post

if __name__ == "__main__":
    init_db()