import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from evaluation.models import Student


class Command(BaseCommand):
    help = "Import student IDs from student_1styear_ids_2026.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="student_1styear_ids_2026.csv",
            help="CSV filename or path (default: student_1styear_ids_2026.csv)",
        )

    def handle(self, *args, **options):
        csv_filename = options["file"]

        # Find the CSV in the same directory as manage.py.
        csv_path = Path(csv_filename)

        if not csv_path.is_absolute():
            csv_path = Path.cwd() / csv_path

        if not csv_path.exists():
            raise CommandError(
                f"CSV file not found: {csv_path}\n"
                "Make sure the CSV is in the same directory as manage.py."
            )

        students = []
        seen = set()
        total_rows = 0
        skipped_empty = 0
        skipped_duplicate = 0

        try:
            with open(
                csv_path,
                mode="r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                reader = csv.reader(file)

                for row in reader:
                    total_rows += 1

                    if not row or not row[0].strip():
                        skipped_empty += 1
                        continue

                    student_id = row[0].strip()

                    # Skip a header if the first column is named student_id.
                    if student_id.lower() in {
                        "student_id",
                        "student id",
                        "student number",
                    }:
                        continue

                    if student_id in seen:
                        skipped_duplicate += 1
                        continue

                    seen.add(student_id)
                    students.append(Student(student_id=student_id))

            # Insert in batches to avoid oversized database queries.
            batch_size = 500

            with transaction.atomic():
                Student.objects.bulk_create(
                    students,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    "Student ID import completed successfully!"
                )
            )

            self.stdout.write(f"CSV file: {csv_path}")
            self.stdout.write(f"Rows processed: {total_rows}")
            self.stdout.write(f"Unique IDs in CSV: {len(students)}")
            self.stdout.write(f"Empty rows skipped: {skipped_empty}")
            self.stdout.write(
                f"Duplicate IDs within CSV skipped: {skipped_duplicate}"
            )
            self.stdout.write(
                "Existing database IDs were ignored where conflicts "
                "were detected."
            )

        except (OSError, csv.Error, UnicodeError, IntegrityError) as error:
            raise CommandError(f"Import failed: {error}") from error