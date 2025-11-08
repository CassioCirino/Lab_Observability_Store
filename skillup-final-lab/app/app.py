from flask import Flask, request, render_template, redirect, url_for, session, g, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, sqlite3, time
from datetime import datetime
from app import fault_manager, scheduler as schedmod

# Config
DB = os.environ.get("DATABASE_FILE", "./db/skillup.db")
fault_manager.init_dbpath(DB)
app = Flask(__name__)
app.secret_key = "skillup-secret-key"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.abspath(DB)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# lightweight model via SQLAlchemy for easier queries
class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    fullname = db.Column(db.String)
    password = db.Column(db.String)

class Product(db.Model):
    __tablename__="products"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String)
    name = db.Column(db.String)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

# initialize scheduler
schedmod.init(DB)

# helpers
def get_user(username):
    return User.query.filter_by(username=username).first()

@app.before_request
def attach_request_attrs():
    # add trace-like headers into logs for easier correlation in Dynatrace
    g.request_time = datetime.utcnow().isoformat()

# Routes
@app.route("/", methods=["GET"])
def index():
    if "username" in session:
        user = get_user(session["username"])
        # render the 5 user-tags in format VST## - Nome
        display = f"{user.username} - {user.fullname}"
        # front long task simulation: inject script that triggers long task if enabled
        front_long_ms = fault_manager.should_front_longtask()
        return render_template("home.html", display=display, front_long_ms=front_long_ms)
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","")
        user = get_user(u)
        if user and user.password == p:
            session["username"]=user.username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Credenciais inválidas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/products")
def products():
    prods = Product.query.all()
    # simple json list
    items = [{"sku":p.sku,"name":p.name,"price":p.price,"stock":p.stock} for p in prods]
    return jsonify(items)

# Vulnerable search endpoint (SQLi when enabled)
@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    # simulated sqli vulnerability: when sqli enabled, we purposely build string query
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if fault_manager.is_sqli_enabled():
        # INSECURE: deliberately concatenated SQL
        sql = f"SELECT sku,name,price,stock FROM products WHERE name LIKE '%{q}%' OR sku LIKE '%{q}%'"
        try:
            cur.execute(sql)
            rows = cur.fetchall()
        except Exception as e:
            return f"Query error: {e}", 500
    else:
        # safe parameterized
        q2 = f"%{q}%"
        cur.execute("SELECT sku,name,price,stock FROM products WHERE name LIKE ? OR sku LIKE ?", (q2,q2))
        rows = cur.fetchall()
    conn.close()
    # if SQLi string contains malicious payload, it may be long or error — that's intended
    results = [{"sku":r[0],"name":r[1],"price":r[2],"stock":r[3]} for r in rows]
    # render small page for RUM visibility
    html = "<h2>Resultados</h2>"
    html += "<ul>"
    for r in results:
        html+=f"<li>{r['sku']} - {r['name']} - R${r['price']}</li>"
    html += "</ul>"
    return html

@app.route("/product/<sku>")
def product(sku):
    p = Product.query.filter_by(sku=sku).first()
    if not p:
        return "Not found", 404
    return jsonify({"sku":p.sku,"name":p.name,"price":p.price,"stock":p.stock})

@app.route("/checkout", methods=["POST","GET"])
def checkout():
    # latency injection
    lat = fault_manager.should_latency()
    if lat and lat>0:
        time.sleep(lat/1000.0)
    # dep slow simulation (e.g., calling payment)
    dep = fault_manager.should_dep_slow()
    if dep and dep>0:
        time.sleep(dep/1000.0)
    # error simulation
    err = fault_manager.should_error()
    if err:
        # return configured status code
        return ("Simulated error", err)
    return "Checkout OK"

# Admin endpoints (no auth for simplicity)
@app.route("/admin")
def admin_ui():
    # read faults
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    faults = {r[0]:dict(enabled=r[1],p=r[2],min_ms=r[3],max_ms=r[4],status=r[5],base_ms=r[6],jitter_ms=r[7],front_ms=r[8],sqli_enabled=r[9]) for r in cur.execute("SELECT name,enabled,p,min_ms,max_ms,status,base_ms,jitter_ms,front_ms,sqli_enabled FROM faults")}
    schedules = [row for row in cur.execute("SELECT id,name,cron,payload FROM schedules")]
    conn.close()
    return render_template("admin.html", faults=faults, schedules=schedules)

@app.route("/admin/faults/state")
def faults_state():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    rows = cur.execute("SELECT name,enabled,p,min_ms,max_ms,status,base_ms,jitter_ms,front_ms,sqli_enabled FROM faults").fetchall()
    conn.close()
    resp = {r[0]:{"enabled":bool(r[1]),"p":r[2],"min_ms":r[3],"max_ms":r[4],"status":r[5],"base_ms":r[6],"jitter_ms":r[7],"front_ms":r[8],"sqli_enabled":bool(r[9])} for r in rows}
    return jsonify(resp)

@app.route("/admin/faults/config", methods=["PUT"])
def set_fault_config():
    data = request.json or {}
    # update db partially - accept structure similar to how toggle script uses it
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for k,v in data.items():
        # v is dict of fields to set
        if isinstance(v, dict):
            # map known keys
            if "enabled" in v:
                cur.execute("UPDATE faults SET enabled=? WHERE name=?", (1 if v["enabled"] else 0, k))
            if "p" in v:
                cur.execute("UPDATE faults SET p=? WHERE name=?", (float(v["p"]), k))
            if "minMs" in v or "min_ms" in v:
                cur.execute("UPDATE faults SET min_ms=? WHERE name=?", (int(v.get("minMs",v.get("min_ms",0))), k))
            if "maxMs" in v or "max_ms" in v:
                cur.execute("UPDATE faults SET max_ms=? WHERE name=?", (int(v.get("maxMs",v.get("max_ms",0))), k))
            if "status" in v:
                cur.execute("UPDATE faults SET status=? WHERE name=?", (int(v["status"]), k))
            if "sqli_enabled" in v:
                cur.execute("UPDATE faults SET sqli_enabled=? WHERE name=?", (1 if v["sqli_enabled"] else 0, k))
    conn.commit()
    conn.close()
    schedmod.load_schedules()
    return jsonify({"ok":True})

@app.route("/admin/schedule", methods=["POST"])
def create_schedule():
    # expects JSON: {"name":"latency-on","cron":"0 13 * * *","payload":{"action":"enable","fault":"latency"}}
    data = request.json or {}
    name = data.get("name")
    cron = data.get("cron")
    payload = data.get("payload")
    if not (name and cron and payload):
        return jsonify({"error":"missing"}),400
    import json
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO schedules(name,cron,payload) VALUES (?,?,?)", (name,cron,json.dumps(payload)))
    conn.commit()
    conn.close()
    schedmod.load_schedules()
    return jsonify({"ok":True})

@app.route("/admin/reset", methods=["POST"])
def reset():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE faults SET enabled=0")
    conn.commit()
    conn.close()
    schedmod.load_schedules()
    return jsonify({"ok":True})

@app.route("/admin/run_stress", methods=["POST"])
def run_stress_now():
    data = request.json or {}
    dur = int(data.get("duration",60))
    from app.stress import run_stress_once
    # run in background
    import threading
    t=threading.Thread(target=run_stress_once, args=(dur,), daemon=True)
    t.start()
    return jsonify({"ok":True})

@app.route("/admin/run_attack", methods=["POST"])
def run_attack_now():
    data = request.json or {}
    times = int(data.get("times",5))
    from app.attack_sim import run_attack_once
    import threading
    t=threading.Thread(target=run_attack_once, args=(times,), daemon=True)
    t.start()
    return jsonify({"ok":True})

# status page
@app.route("/status")
def status_page():
    conn = sqlite3.connect(DB)
    faults = {r[0]:bool(r[1]) for r in conn.execute("SELECT name,enabled FROM faults").fetchall()}
    conn.close()
    return render_template("status.html", faults=faults)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8080)
