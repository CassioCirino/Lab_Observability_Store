import sqlite3
import random
from flask import current_app
from typing import Any

DBPATH = None

def init_dbpath(path):
    global DBPATH
    DBPATH = path

def _fetch(name):
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    row = cur.execute("SELECT enabled,p,min_ms,max_ms,status,base_ms,jitter_ms,front_ms,sqli_enabled FROM faults WHERE name=?",(name,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "enabled": bool(row[0]),
        "p": row[1],
        "min_ms": row[2],
        "max_ms": row[3],
        "status": row[4],
        "base_ms": row[5],
        "jitter_ms": row[6],
        "front_ms": row[7],
        "sqli_enabled": bool(row[8])
    }

def should_latency():
    f = _fetch("latency")
    if not f or not f["enabled"]: return 0
    if random.random() < f["p"]:
        return random.randint(f["min_ms"], f["max_ms"])
    return 0

def should_error():
    f = _fetch("errors")
    if not f or not f["enabled"]: return None
    if random.random() < f["p"]:
        return f["status"] or 500
    return None

def should_dep_slow():
    f = _fetch("depSlow")
    if not f or not f["enabled"]: return 0
    return f["base_ms"] + random.randint(0, f["jitter_ms"])

def is_sqli_enabled():
    f = _fetch("sqli")
    return f and f["sqli_enabled"]

def should_front_longtask():
    f = _fetch("frontLongTask")
    if not f or not f["enabled"]: return 0
    return f["front_ms"]
