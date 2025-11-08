from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3, json
from importlib import import_module
import time

DBPATH = None
scheduler = BackgroundScheduler()

def init(dbpath):
    global DBPATH
    DBPATH = dbpath
    scheduler.start()
    load_schedules()

def load_schedules():
    conn = sqlite3.connect(DBPATH)
    cur = conn.cursor()
    rows = cur.execute("SELECT id,name,cron,payload FROM schedules").fetchall()
    conn.close()
    # clear all jobs
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)
    for r in rows:
        sid, name, cron_expr, payload = r
        # cron_expr simple format: "min hour day month dow" like cron
        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                continue
            minute, hour, day, month, dow = parts
            scheduler.add_job(func=lambda p=payload: run_payload(p),
                              trigger='cron',
                              id=str(sid),
                              minute=minute, hour=hour, day=day, month=month, day_of_week=dow)
        except Exception as e:
            print("Failed to schedule", name, e)

def run_payload(payload_json):
    try:
        payload = json.loads(payload_json)
    except:
        return
    # payload example: {"action":"enable","fault":"latency"}
    action = payload.get("action")
    fault = payload.get("fault")
    if action in ("enable","disable") and fault:
        conn = sqlite3.connect(DBPATH)
        cur = conn.cursor()
        if action=="enable":
            cur.execute("UPDATE faults SET enabled=1 WHERE name=?",(fault,))
        else:
            cur.execute("UPDATE faults SET enabled=0 WHERE name=?",(fault,))
        conn.commit()
        conn.close()
    elif action=="stress":
        # call stress function
        from app.stress import run_stress_once
        run_stress_once(duration=payload.get("duration",60))
    elif action=="attack":
        from app.attack_sim import run_attack_once
        run_attack_once(times=payload.get("times",1))
