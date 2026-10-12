from django.core.management.base import BaseCommand
from django.utils import timezone
import random

from evaluation.models import (
    TeacherEvaluation,
    EvaluationItem,
    Teacher,
    Subject,
    Course,
    Question
)

class Command(BaseCommand):
    help = "Seed 100 Teacher Evaluations with ratings"

    def handle(self, *args, **options):
        teachers = list(Teacher.objects.all())
        subjects = list(Subject.objects.all())
        courses = list(Course.objects.all())
        questions = list(Question.objects.select_related("section"))

        if not teachers or not questions:
            self.stdout.write(self.style.ERROR(
                "❌ Teachers or Questions missing. Seed them first."
            ))
            return

        semesters = ["1st Semester", "2nd Semester"]
        academic_years = ["2023-2024", "2024-2025"]
        year_levels = ["1st", "2nd", "3rd", "4th"]

        ratings = ['5', '4', '3', '2', '1', 'N']

        commendations = [
            "Very approachable and supportive.",
            "Explains lessons clearly.",
            "Encourages participation.",
            "Well-organized lectures.",
            "Shows genuine concern for students."
        ]

        suggestions = [
            "More interactive activities.",
            "Improve pacing of lessons.",
            "More examples needed.",
            "More feedback on outputs.",
            "Use more visual aids."
        ]

        created = 0
        attempts = 0
        TARGET = 3000

        while created < TARGET and attempts < TARGET * 5:
            attempts += 1

            teacher = random.choice(teachers)
            subject = teacher.subject or random.choice(subjects)
            course = teacher.course or random.choice(courses)

            semester = random.choice(semesters)
            academic_year = random.choice(academic_years)
            student_id = f"STU-{random.randint(1000, 9999)}"

            # Respect unique_together
            if TeacherEvaluation.objects.filter(
                teacher=teacher,
                student_id=student_id,
                subject=subject,
                semester=semester,
                academic_year=academic_year
            ).exists():
                continue

            evaluation = TeacherEvaluation.objects.create(
                teacher=teacher,
                student_id=student_id,
                student_name=f"Student {random.randint(1, 500)}",
                subject=subject,
                course=course,
                semester=semester,
                academic_year=academic_year,
                year_level=random.choice(year_levels),
                commendable_features=random.choice(commendations),
                suggestions_improvement=random.choice(suggestions),
                submitted_at=timezone.now()
            )

            items = [
                EvaluationItem(
                    evaluation=evaluation,
                    question=question,
                    rating=random.choice(ratings)
                )
                for question in questions
            ]

            EvaluationItem.objects.bulk_create(items)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully created {created} teacher evaluations")
        )
