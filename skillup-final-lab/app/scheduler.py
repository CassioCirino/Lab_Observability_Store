from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3, json

DBPATH = None
scheduler = BackgroundScheduler()

def init(dbpath):
    global DBPATH
    DBPATH = dbpath
    scheduler.start()
    load_schedules()

def _ensure_tables():
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cron TEXT,
        payload TEXT
    )""")
    conn.commit()
    conn.close()

def load_schedules():
    _ensure_tables()
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    rows = cur.execute("SELECT id,name,cron,payload FROM schedules").fetchall()
    conn.close()
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)
    for sid, name, cron_expr, payload in rows:
        try:
            m,h,d,mo,dow = cron_expr.strip().split()
            scheduler.add_job(lambda p=payload: run_payload(p),
                              trigger='cron', id=str(sid),
                              minute=m, hour=h, day=d, month=mo, day_of_week=dow)
        except Exception as e:
            print("Failed to schedule", name, e)

def run_payload(payload_json):
    try:
        payload = json.loads(payload_json)
    except:
        return
    action = payload.get("action"); fault = payload.get("fault")
    if action in ("enable","disable") and fault:
        conn = sqlite3.connect(DBPATH)
        cur = conn.cursor()
        cur.execute("UPDATE faults SET enabled=? WHERE name=?",
                    (1 if action=="enable" else 0, fault))
        conn.commit(); conn.close()
    elif action=="stress":
        from app.stress import run_stress_once
        run_stress_once(duration=payload.get("duration",60))
    elif action=="attack":
        from app.attack_sim import run_attack_once
        run_attack_once(times=payload.get("times",1))
