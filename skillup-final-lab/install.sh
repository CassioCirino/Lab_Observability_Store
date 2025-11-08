cat > /etc/systemd/system/skillup-lab.service << 'EOS'
[Unit]
Description=SkillUp Final Lab Flask App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/skillup-final-lab
Environment="PATH=/opt/skillup-final-lab/venv/bin"
Environment="DATABASE_FILE=/opt/skillup-final-lab/db/skillup.db"
ExecStartPre=/opt/skillup-final-lab/venv/bin/python3 /opt/skillup-final-lab/app/db_init.py /opt/skillup-final-lab/db/skillup.db
ExecStart=/opt/skillup-final-lab/venv/bin/gunicorn --bind 0.0.0.0:80 app.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOS
