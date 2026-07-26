# PostgreSQL backups

The production database is dumped daily at approximately 00:30 UTC (03:30
Moscow time). Backups use PostgreSQL custom format and are retained for 14
days in `/var/backups/jobmonitor/postgres`.

Install the root-owned units on the server:

```bash
sudo install -m 0755 deploy/backup/jobmonitor-pg-backup /usr/local/sbin/
sudo install -m 0644 deploy/backup/jobmonitor-pg-backup.service /etc/systemd/system/
sudo install -m 0644 deploy/backup/jobmonitor-pg-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jobmonitor-pg-backup.timer
```

Run and inspect a backup manually:

```bash
sudo systemctl start jobmonitor-pg-backup.service
sudo journalctl -u jobmonitor-pg-backup.service
sudo ls -lh /var/backups/jobmonitor/postgres
```

These backups remain on the VPS. Copy them to encrypted off-site storage to
protect against disk or server loss.
