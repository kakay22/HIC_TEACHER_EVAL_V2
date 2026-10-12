from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class EducationLevel(models.TextChoices):
    COLLEGE = "COLLEGE", "College"
    BASIC = "BASIC", "Basic Education"


class Section(models.Model):
    prefix = models.CharField(max_length=1, unique=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.prefix}. {self.title}"


class Question(models.Model):
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    order = models.PositiveIntegerField()
    text = models.TextField()

    class Meta:
        unique_together = ("section", "order")
        ordering = ["section__prefix", "order"]

    def __str__(self):
        return f"{self.section.prefix}{self.order}. {self.text[:50]}..."


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


class Teacher(models.Model):
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    specialization = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    education_level = models.CharField(
        max_length=20,
        choices=EducationLevel.choices,
        default=EducationLevel.COLLEGE,
        db_index=True,
    )
    courses = models.ManyToManyField(
        "Course",
        blank=True,
        related_name="teachers",
    )

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class EvaluationPeriod(models.Model):
    class Semester(models.TextChoices):
        FIRST = "1st", "1st Semester"
        SECOND = "2nd", "2nd Semester"

    education_level = models.CharField(
        max_length=20,
        choices=EducationLevel.choices,
        default=EducationLevel.COLLEGE,
        db_index=True,
    )
    academic_year = models.CharField(
        max_length=20,
        help_text="Example: 2026-2027",
    )
    semester = models.CharField(
        max_length=20,
        choices=Semester.choices,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_open = models.BooleanField(
        default=False,
        help_text="Only one evaluation period can be open per division.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # One period per division per semester/year
            models.UniqueConstraint(
                fields=["education_level", "academic_year", "semester"],
                name="unique_period_per_division",
            ),
            # At most one OPEN period per division (College and Basic can both be open)
            models.UniqueConstraint(
                fields=["education_level"],
                condition=Q(is_open=True),
                name="one_open_period_per_division",
            ),
        ]

    def clean(self):
        super().clean()

        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    "end_date": "The end date cannot be before the start date."
                })

    def __str__(self):
        status = "Open" if self.is_open else "Closed"
        return (
            f"{self.get_education_level_display()} - "
            f"{self.academic_year} - "
            f"{self.get_semester_display()} ({status})"
        )


class TeacherEvaluation(models.Model):
    teacher = models.ForeignKey(
        "Teacher",
        on_delete=models.PROTECT,
        related_name="evaluations",
    )
    education_level = models.CharField(
        max_length=20,
        choices=EducationLevel.choices,
        default=EducationLevel.COLLEGE,
        db_index=True,
    )
    student_id = models.CharField(max_length=50)
    student_name = models.CharField(max_length=100, null=True, blank=True)
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        "Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    semester = models.CharField(max_length=20, blank=True)
    academic_year = models.CharField(max_length=20, blank=True)
    year_level = models.CharField(max_length=20, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    overall_rating = models.FloatField(null=True, blank=True)
    commendable_features = models.TextField(blank=True, null=True)
    suggestions_improvement = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (
            "teacher",
            "student_id",
            "subject",
            "course",
            "semester",
            "academic_year",
            "education_level",
        )

    @property
    def overall_computed_rating(self):
        ratings = []

        for item in self.items.all():
            try:
                value = float(item.rating)
                ratings.append(value)
            except (ValueError, TypeError):
                continue

        if ratings:
            return round(sum(ratings) / len(ratings), 2)

        return None


class EvaluationItem(models.Model):
    evaluation = models.ForeignKey(
        TeacherEvaluation,
        on_delete=models.CASCADE,
        related_name="items",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    rating = models.CharField(
        max_length=2,
        choices=[
            ("5", "Outstanding"),
            ("4", "Good"),
            ("3", "Average"),
            ("2", "Needs Improvement"),
            ("1", "Unsatisfactory"),
            ("N", "Not Observed"),
        ],
    )

    def __str__(self):
        return (
            f"{self.question.section.prefix}"
            f"{self.question.order} - {self.rating}"
        )


class Student(models.Model):
    student_id = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.student_id


class SectionEvaluation(models.Model):
    evaluation = models.ForeignKey(
        TeacherEvaluation,
        on_delete=models.CASCADE,
        related_name="section_scores",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
    )
    average_rating = models.FloatField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
