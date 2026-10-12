from django.contrib import admin
from .models import Section, Question, Teacher, Course, Subject, TeacherEvaluation, EvaluationItem, Student, SectionEvaluation

# Inline to add questions inside Section
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # allows adding one extra question at a time
    fields = ['order', 'text']
    ordering = ['order']

# Admin for Section
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['prefix', 'title']
    inlines = [QuestionInline]

# Admin for Course
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name']

# Admin for Subject
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name']

# Admin for Teacher
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['get_full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Teacher Name'

# Inline to view EvaluationItems in TeacherEvaluation
class EvaluationItemInline(admin.TabularInline):
    model = EvaluationItem
    extra = 0
    readonly_fields = [
        'get_section', 'get_question_number',
        'question', 'rating',
        'get_course', 'get_subject'
    ]
    can_delete = False

    def get_section(self, obj):
        return obj.question.section.prefix

    def get_question_number(self, obj):
        return obj.question.order

    def get_course(self, obj):
        return obj.evaluation.course.name if obj.evaluation.course else '-'

    def get_subject(self, obj):
        return obj.evaluation.subject.name if obj.evaluation.subject else '-'

# Admin for TeacherEvaluation
@admin.register(TeacherEvaluation)
class TeacherEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'get_teacher_name',
        'subject',
        'course',
        'semester',
        'academic_year',
        'year_level',
        'overall_rating',
        'submitted_at'
    ]

    list_filter = ['subject', 'course', 'semester', 'academic_year', 'year_level']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'student_id']

    readonly_fields = ['submitted_at']

    inlines = [EvaluationItemInline]

    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"
    get_teacher_name.short_description = 'Teacher Name'

# Admin for EvaluationItem (optional: separate list view)
@admin.register(EvaluationItem)
class EvaluationItemAdmin(admin.ModelAdmin):
    list_display = [
        'evaluation',
        'get_section',
        'get_question_number',
        'question',
        'rating',
        'get_course',
        'get_subject'
    ]

    def get_section(self, obj):
        return obj.question.section.prefix

    def get_question_number(self, obj):
        return obj.question.order

    def get_course(self, obj):
        return obj.evaluation.course.name if obj.evaluation.course else '-'

    def get_subject(self, obj):
        return obj.evaluation.subject.name if obj.evaluation.subject else '-'

# ---------- Student Admin ----------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id']
    search_fields = ['student_id']

@admin.register(SectionEvaluation)
class SectionEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "evaluation",
        "section",
        "average_rating",
        "total_score",
    )

    list_filter = ("section",)
    search_fields = ("evaluation__student_id", "evaluation__teacher__first_name", "evaluation__teacher__last_name")

    autocomplete_fields = ("evaluation", "section")