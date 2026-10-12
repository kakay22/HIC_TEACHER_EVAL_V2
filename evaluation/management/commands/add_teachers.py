from django.core.management.base import BaseCommand
from evaluation.models import Teacher, Course, Subject
import random

FIRST_NAMES = [
    "John", "Maria", "Jose", "Anna", "Mark", "Paul", "Grace", "James",
    "Michael", "Sarah", "David", "Daniel", "Joshua", "Karen", "Ruth"
]

LAST_NAMES = [
    "Cruz", "Reyes", "Santos", "Garcia", "Mendoza", "Torres",
    "Flores", "Ramos", "Aquino", "Villanueva"
]

SEMESTERS = ["1st", "2nd"]
ACADEMIC_YEARS = ["2023-2024", "2024-2025", "2025-2026"]


class Command(BaseCommand):
    help = "Add 500 teachers"

    def handle(self, *args, **kwargs):
        courses = list(Course.objects.all())
        subjects = list(Subject.objects.all())

        if not courses or not subjects:
            self.stdout.write(self.style.ERROR(
                "❌ Please add Course and Subject records first."
            ))
            return

        teachers = []

        for i in range(100):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            teacher = Teacher(
                first_name=first_name,
                last_name=last_name,
                course=random.choice(courses),
                subject=random.choice(subjects),
                semester=random.choice(SEMESTERS),
                academic_year=random.choice(ACADEMIC_YEARS),
            )
            teachers.append(teacher)

        Teacher.objects.bulk_create(teachers)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Successfully created {len(teachers)} teachers"
        ))