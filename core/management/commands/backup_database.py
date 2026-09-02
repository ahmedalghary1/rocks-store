import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Create a consistent online backup of the SQLite database."

    def add_arguments(self, parser):
        parser.add_argument("--directory", required=True, help="Existing directory that will receive the backup.")

    def handle(self, *args, **options):
        if connection.vendor != "sqlite":
            raise CommandError("This command is only for SQLite.")
        directory = Path(options["directory"]).expanduser().resolve()
        if not directory.is_dir():
            raise CommandError("Backup directory does not exist.")
        database_path = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if directory == database_path.parent:
            self.stdout.write(self.style.WARNING("Prefer a backup directory on a separate persistent volume."))
        target = directory / f"rocks-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
        if target.exists():
            raise CommandError("Backup target already exists.")
        connection.ensure_connection()
        destination = sqlite3.connect(target)
        try:
            connection.connection.backup(destination)
            result = destination.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                raise CommandError("Backup integrity check failed.")
        finally:
            destination.close()
        self.stdout.write(self.style.SUCCESS(f"Backup created: {target}"))
