import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('users.db')
c = conn.cursor()

# إنشاء الجدول إذا لم يكن موجودًا
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                last_login TEXT,
                is_logged_in INTEGER DEFAULT 0,
                ip_address TEXT
            )''')
conn.commit()

username = "admin"
password = "2025"

c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
          (username, hash_password(password)))
conn.commit()
conn.close()

print("✅ تم إضافة حساب admin بنجاح.")
