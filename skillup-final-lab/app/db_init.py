#!/usr/bin/env python3
import sys
import sqlite3
from pathlib import Path

DB = sys.argv[1] if len(sys.argv) > 1 else "./db/skillup.db"
p = Path(DB)
p.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB)
c = conn.cursor()

# users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE,
  fullname TEXT,
  password TEXT
)
""")

# products
c.execute("""
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT,
  name TEXT,
  price REAL,
  stock INTEGER
)
""")

# faults config
c.execute("""
CREATE TABLE IF NOT EXISTS faults (
  name TEXT PRIMARY KEY,
  enabled INTEGER,
  p REAL,
  min_ms INTEGER,
  max_ms INTEGER,
  status INTEGER,
  base_ms INTEGER,
  jitter_ms INTEGER,
  front_ms INTEGER,
  sqli_enabled INTEGER
)
""")

# schedules: id, name, cron_expr (simplified using APScheduler's cron)
c.execute("""
CREATE TABLE IF NOT EXISTS schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  cron TEXT,
  payload TEXT
)
""")

# seed users VST01..VST20
existing = list(c.execute("SELECT username FROM users").fetchall())
if not existing:
    for i in range(1,21):
        username = f"VST{str(i).zfill(2)}"
        fullname = f"Usuário {i:02d}"
        password = "pass"  # simple for lab
        c.execute("INSERT INTO users(username,fullname,password) VALUES (?,?,?)",(username,fullname,password))

# seed products
if not list(c.execute("SELECT 1 FROM products LIMIT 1")):
    products = [
        ("SKU101","Notebook Gamer",3999.00,5),
        ("SKU102","Smartphone X",2499.00,10),
        ("SKU103","Monitor 27\"",899.00,8),
        ("SKU104","Teclado Mecânico",299.00,15),
        ("SKU105","Mouse Óptico",129.00,20),
    ]
    for sku,name,price,stock in products:
        c.execute("INSERT INTO products(sku,name,price,stock) VALUES (?,?,?,?)",(sku,name,price,stock))

# default faults row entries
faults = {
  "latency": (0, 0.2, 400, 1200, 0, 300, 600, 200, 0),
  "errors":  (0, 0.1, 0, 0, 500, 300, 600, 200, 0),
  "depSlow": (0, 0.0, 0, 0, 0, 300, 600, 200, 0),
  "frontLongTask": (0, 0.0, 0, 0, 0, 300, 600, 200, 0),
  "sqli": (0, 0.0, 0,0,0,0,0,0,0)
}
for name,(enabled,p,min_ms,max_ms,status,base_ms,jitter_ms,front_ms,sqli) in faults.items():
    c.execute("INSERT OR REPLACE INTO faults(name,enabled,p,min_ms,max_ms,status,base_ms,jitter_ms,front_ms,sqli_enabled) VALUES (?,?,?,?,?,?,?,?,?,?)",
              (name,enabled,p,min_ms,max_ms,status,base_ms,jitter_ms,front_ms,sqli))

conn.commit()
conn.close()
print("Database initialized at", DB)
