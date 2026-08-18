# Backups

The only stateful piece is the Postgres database (the `db-data` Docker
volume). Everything else (backend, frontend) is rebuilt from source on
every deploy, so a backup strategy only needs to cover the database.

## Manual backup

```bash
docker compose exec -T db pg_dump -U grade_tracker grade_tracker | gzip > grade_tracker_$(date +%F).sql.gz
```

## Restore

```bash
gunzip -c grade_tracker_2026-08-18.sql.gz | docker compose exec -T db psql -U grade_tracker grade_tracker
```

Restoring into a database that already has tables will fail on conflicts -
either restore into a fresh volume, or drop/recreate the schema first.

## Automated daily backups (server-side cron)

Once the app runs on a server, add a cron job there (not in this repo -
it's server configuration, not application code):

```cron
# /etc/cron.d/grade-tracker-backup
0 3 * * * root cd /path/to/grade_tracker && docker compose exec -T db pg_dump -U grade_tracker grade_tracker | gzip > /path/to/backups/grade_tracker_$(date +\%F).sql.gz && find /path/to/backups -name '*.sql.gz' -mtime +14 -delete
```

Adjust the retention (`-mtime +14`) and backup path to taste. For anything
beyond "a directory on the same disk", copy the resulting `.sql.gz` off the
server too (e.g. to object storage) - a backup that lives only on the
machine it's backing up doesn't protect against that machine failing.
