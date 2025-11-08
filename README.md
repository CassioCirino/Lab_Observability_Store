# SkillUp Final Lab (Flask) — Observability Training

## Overview
Lightweight lab instrumented for Dynatrace OneAgent. Provides:
- Login + 5 user-tags on UI
- Admin UI to toggle faults and schedule them
- Vulnerability toggles (SQLi) for simulation
- Stress (cpu/mem) and attack simulation scripts
- SQLite DB seeded with VST01..VST20

## Install (on Ubuntu)
sudo ./install.sh
systemctl start skillup-lab.service

## Admin
Open http://IP:8080/admin

## Notes
- This is a training lab. Do not expose publicly without proper network controls.
- To simulate exploitation attempts: use Admin -> run_attack or call /admin/run_attack
