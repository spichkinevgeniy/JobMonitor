# Резервное копирование PostgreSQL

Production-база копируется ежедневно примерно в 00:30 UTC (03:30 по Москве).
Копии создаются в специальном формате PostgreSQL и хранятся 14 дней в каталоге
`/var/backups/jobmonitor/postgres`.

Установка скрипта и systemd units с владельцем `root`:

```bash
sudo install -m 0755 deploy/backup/jobmonitor-pg-backup /usr/local/sbin/
sudo install -m 0644 deploy/backup/jobmonitor-pg-backup.service /etc/systemd/system/
sudo install -m 0644 deploy/backup/jobmonitor-pg-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jobmonitor-pg-backup.timer
```

Ручной запуск и проверка результата:

```bash
sudo systemctl start jobmonitor-pg-backup.service
sudo journalctl -u jobmonitor-pg-backup.service
sudo ls -lh /var/backups/jobmonitor/postgres
```

Эти копии остаются на VPS. Для защиты от потери диска или всего сервера их
необходимо дополнительно отправлять в зашифрованное внешнее хранилище.
