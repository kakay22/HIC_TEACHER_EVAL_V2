import django
from django.http import HttpResponse, request
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import EducationLevel, Section, Question, Teacher, Course, Subject, TeacherEvaluation, EvaluationItem, Student, SectionEvaluation,EvaluationPeriod
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .forms import SectionForm, QuestionForm, EvaluationPeriodForm
from django.core.paginator import Paginator
from .forms import CourseForm
from django.db.models import Count
from django.http import JsonResponse
from django.db.models import ProtectedError
from django.db import transaction, IntegrityError
from datetime import datetime
from collections import defaultdict

from django.db.models import Q
from django.http import HttpResponse
import csv
from reportlab.platypus import SimpleDocTemplate, Table

from django.contrib.staticfiles import finders

def home(request):
    return render(request, "evaluation/landing.html")

def evaluation_form(request, division):
    # --------------------------------------------------
    # DIVISION CONFIGURATION
    # --------------------------------------------------
    if division not in EducationLevel.values:
        return redirect("home")

    form_url_name = (
        "college_evaluation"
        if division == EducationLevel.COLLEGE
        else "basic_education_evaluation"
    )

    template_name = (
        "evaluation/home.html"
        if division == EducationLevel.COLLEGE
        else "evaluation/basic_education.html"
    )

    # --------------------------------------------------
    # PAGE DATA
    # --------------------------------------------------
    sections = Section.objects.prefetch_related(
        "questions"
    ).all()

    teachers = Teacher.objects.filter(
        education_level=division
    ).order_by("last_name", "first_name")

    courses = Course.objects.all()
    subjects = Subject.objects.all()

    active_period = EvaluationPeriod.objects.filter(
        education_level=division,
        is_open=True,
    ).first()

    current_date = timezone.localdate()

    if division == EducationLevel.BASIC:
        year_levels = [
            "Kindergarten",
            "Grade 1",
            "Grade 2",
            "Grade 3",
            "Grade 4",
            "Grade 5",
            "Grade 6",
            "Grade 7",
            "Grade 8",
            "Grade 9",
            "Grade 10",
            "Grade 11",
            "Grade 12",
        ]
    else:
        year_levels = [
            "1st Year",
            "2nd Year",
            "3rd Year",
            "4th Year",
            "5th Year",
        ]

    # --------------------------------------------------
    # HANDLE STUDENT SUBMISSION
    # --------------------------------------------------
    if request.method == "POST":

        # Always get the open period for THIS division.
        active_period = EvaluationPeriod.objects.filter(
            education_level=division,
            is_open=True,
        ).first()

        if not active_period:
            messages.error(
                request,
                "Evaluations are currently closed for this division. "
                "Please wait for the administration to open a semester.",
            )
            return redirect(form_url_name)

        # --------------------------------------------------
        # READ AND NORMALIZE FORM DATA
        # --------------------------------------------------
        student_id = request.POST.get(
            "student_id", ""
        ).strip()

        student_name = request.POST.get(
            "student_name", ""
        ).strip()

        teacher_id = request.POST.get(
            "teacher", ""
        ).strip()

        course_id = request.POST.get(
            "course", ""
        ).strip()

        year_level = request.POST.get(
            "year_level", ""
        ).strip()

        subject_name = " ".join(
            request.POST.get("subject", "").strip().split()
        ).title()

        commendable_features = request.POST.get(
            "commendable_features", ""
        ).strip()

        suggestions_improvement = request.POST.get(
            "suggestions_improvement", ""
        ).strip()

        # --------------------------------------------------
        # REQUIRED FIELDS
        # --------------------------------------------------
        if not all([
            student_id,
            teacher_id,
            course_id,
            year_level,
            subject_name,
        ]):
            messages.error(
                request,
                "Please complete all required fields.",
            )
            return redirect(form_url_name)

        # --------------------------------------------------
        # REGISTERED STUDENT VALIDATION
        # --------------------------------------------------
        student_exists = Student.objects.filter(
            student_id=student_id
        ).exists()

        if not student_exists:
            messages.error(
                request,
                "Your student ID is not registered in the system. "
                "Please verify your ID with the administration.",
            )
            return redirect(form_url_name)

        # --------------------------------------------------
        # VALIDATE TEACHER BELONGS TO THIS DIVISION
        # --------------------------------------------------
        teacher = Teacher.objects.filter(
            pk=teacher_id,
            education_level=division,
        ).first()

        if teacher is None:
            messages.error(
                request,
                "The selected teacher is invalid for this division. "
                "Please refresh the page and select a teacher again.",
            )
            return redirect(form_url_name)

        # --------------------------------------------------
        # VALIDATE COURSE
        # --------------------------------------------------
        course = Course.objects.filter(
            pk=course_id
        ).first()

        if course is None:
            messages.error(
                request,
                "The selected course is invalid. "
                "Please refresh the page and select a course again.",
            )
            return redirect(form_url_name)

        # --------------------------------------------------
        # VALIDATE ALL QUESTION RATINGS
        # --------------------------------------------------
        question_list = []

        for section in sections:
            for question in section.questions.all():
                question_list.append((section, question))

        if not question_list:
            messages.error(
                request,
                "The evaluation form has no questions configured. "
                "Please contact the administration.",
            )
            return redirect(form_url_name)

        allowed_ratings = {"1", "2", "3", "4", "5", "N"}
        submitted_ratings = {}

        for section, question in question_list:
            field_name = f"q_{section.prefix}_{question.order}"
            rating = request.POST.get(
                field_name, ""
            ).strip()

            if rating not in allowed_ratings:
                messages.error(
                    request,
                    "Please answer every evaluation question "
                    "before submitting. You may select "
                    "'Not Observed' when appropriate.",
                )
                return redirect(form_url_name)

            submitted_ratings[question.pk] = rating

        # --------------------------------------------------
        # SAVE EVERYTHING IN ONE TRANSACTION
        # --------------------------------------------------
        try:
            with transaction.atomic():

                # Recheck the open period for this division.
                current_period = EvaluationPeriod.objects.filter(
                    education_level=division,
                    is_open=True,
                ).first()

                if (
                    current_period is None
                    or current_period.pk != active_period.pk
                ):
                    messages.error(
                        request,
                        "The evaluation period has changed or closed. "
                        "Please refresh the page and try again.",
                    )
                    return redirect(form_url_name)

                semester = current_period.semester
                academic_year = current_period.academic_year

                # --------------------------------------------------
                # DUPLICATE SUBMISSION CHECK
                # --------------------------------------------------
                subject = Subject.objects.filter(
                    name__iexact=subject_name
                ).first()

                if subject and TeacherEvaluation.objects.filter(
                    education_level=division,
                    student_id=student_id,
                    teacher=teacher,
                    subject=subject,
                    semester=semester,
                    academic_year=academic_year,
                ).exists():
                    messages.error(
                        request,
                        "You have already submitted an evaluation "
                        "for this teacher and subject during "
                        "the current semester.",
                    )
                    return redirect(form_url_name)

                # Create or retrieve the subject after the duplicate
                # check. This avoids creating unused subjects when
                # a duplicate submission is rejected.
                if subject is None:
                    subject, _ = Subject.objects.get_or_create(
                        name=subject_name
                    )

                # --------------------------------------------------
                # CREATE EVALUATION
                # --------------------------------------------------
                evaluation = TeacherEvaluation.objects.create(
                    education_level=division,
                    student_id=student_id,
                    student_name=student_name,
                    teacher=teacher,
                    subject=subject,
                    course=course,
                    year_level=year_level,
                    semester=semester,
                    academic_year=academic_year,
                    commendable_features=commendable_features,
                    suggestions_improvement=suggestions_improvement,
                )

                # --------------------------------------------------
                # SAVE QUESTION RATINGS AND SECTION TOTALS
                # --------------------------------------------------
                numeric_ratings = []
                section_data = defaultdict(list)

                for section, question in question_list:
                    rating = submitted_ratings[question.pk]

                    EvaluationItem.objects.create(
                        evaluation=evaluation,
                        question=question,
                        rating=rating,
                    )

                    # "N" is valid but excluded from numeric averages.
                    if rating in {"1", "2", "3", "4", "5"}:
                        rating_value = int(rating)
                        numeric_ratings.append(rating_value)

                        section_data[section.pk].append(
                            rating_value
                        )

                # --------------------------------------------------
                # OVERALL RATING
                # --------------------------------------------------
                if numeric_ratings:
                    evaluation.overall_rating = round(
                        sum(numeric_ratings) / len(numeric_ratings),
                        2,
                    )

                    evaluation.save(
                        update_fields=["overall_rating"]
                    )

                # --------------------------------------------------
                # SECTION EVALUATION RECORDS
                # --------------------------------------------------
                sections_by_id = {
                    section.pk: section
                    for section in sections
                }

                for section_id, values in section_data.items():
                    if not values:
                        continue

                    total_score = sum(values)

                    average_rating = round(
                        total_score / len(values),
                        2,
                    )

                    SectionEvaluation.objects.update_or_create(
                        evaluation=evaluation,
                        section=sections_by_id[section_id],
                        defaults={
                            "total_score": total_score,
                            "average_rating": average_rating,
                        },
                    )

        except IntegrityError:
            messages.error(
                request,
                "The evaluation could not be saved because of a "
                "data conflict. You may already have submitted it. "
                "Please refresh the page and try again.",
            )
            return redirect(form_url_name)

        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------
        request.session["last_evaluation_id"] = evaluation.id
        request.session["last_division"] = division

        messages.success(
            request,
            "Your evaluation has been submitted successfully!",
        )

        return redirect("thank_you")

    # --------------------------------------------------
    # RENDER STUDENT EVALUATION PAGE
    # --------------------------------------------------
    context = {
        "sections": sections,
        "teachers": teachers,
        "courses": courses,
        "subjects": subjects,
        "education_level": division,
        "current_academic_year": (
            active_period.academic_year
            if active_period
            else ""
        ),
        "active_period": active_period,
        "year_levels": year_levels,
    }

    return render(request, template_name, context)


# ------------------------------------------------------
# COLLEGE EVALUATION FORM
# ------------------------------------------------------
def college_evaluation(request):
    return evaluation_form(
        request,
        EducationLevel.COLLEGE,
    )


# ------------------------------------------------------
# BASIC EDUCATION EVALUATION FORM
# ------------------------------------------------------
def basic_education_evaluation(request):
    return evaluation_form(
        request,
        EducationLevel.BASIC,
    )



from django.http import JsonResponse
from .models import Student, TeacherEvaluation, Subject


def validate_evaluation(request):
    # --------------------------------------------------
    # AJAX REQUEST CHECK
    # --------------------------------------------------
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return JsonResponse({
            "student_exists": False,
            "duplicate": False,
            "period_open": False,
            "active_period": None,
            "teacher_valid": False,
        })

    # --------------------------------------------------
    # READ REQUEST PARAMETERS
    # --------------------------------------------------
    student_id = request.GET.get("student_id", "").strip()
    teacher_id = request.GET.get("teacher", "").strip()
    subject_name = request.GET.get("subject", "").strip()

    # Accept only the known division values.
    division = request.GET.get(
        "division",
        EducationLevel.COLLEGE,
    ).strip().upper()

    if division not in EducationLevel.values:
        return JsonResponse({
            "student_exists": False,
            "duplicate": False,
            "period_open": False,
            "active_period": None,
            "teacher_valid": False,
            "error": "Invalid education division.",
        }, status=400)

    # --------------------------------------------------
    # REGISTERED STUDENT CHECK
    # --------------------------------------------------
    student_exists = (
        Student.objects.filter(
            student_id=student_id
        ).exists()
        if student_id
        else False
    )

    # --------------------------------------------------
    # TEACHER VALIDATION
    # --------------------------------------------------
    teacher_valid = (
        Teacher.objects.filter(
            pk=teacher_id,
            education_level=division,
        ).exists()
        if teacher_id
        else False
    )

    # --------------------------------------------------
    # ACTIVE PERIOD FOR THIS DIVISION ONLY
    # --------------------------------------------------
    active_period = EvaluationPeriod.objects.filter(
        education_level=division,
        is_open=True,
    ).first()

    # --------------------------------------------------
    # DUPLICATE SUBMISSION CHECK
    # --------------------------------------------------
    duplicate = False

    if (
        active_period
        and student_id
        and teacher_valid
        and subject_name
    ):
        normalized_subject = " ".join(
            subject_name.split()
        )

        duplicate = TeacherEvaluation.objects.filter(
            education_level=division,
            student_id=student_id,
            teacher_id=teacher_id,
            subject__name__iexact=normalized_subject,
            semester=active_period.semester,
            academic_year=active_period.academic_year,
        ).exists()

    # --------------------------------------------------
    # JSON RESPONSE
    # --------------------------------------------------
    return JsonResponse({
        "student_exists": student_exists,
        "duplicate": duplicate,
        "period_open": active_period is not None,
        "teacher_valid": teacher_valid,
        "active_period": (
            {
                "semester": active_period.get_semester_display(),
                "academic_year": active_period.academic_year,
                "education_level": active_period.education_level,
            }
            if active_period
            else None
        ),
    })

def thank_you(request):
    evaluation_id = request.session.get("last_evaluation_id")
    division = request.session.get("last_division")

    evaluation = None
    if evaluation_id:
        evaluation = TeacherEvaluation.objects.filter(id=evaluation_id).first()

    if not evaluation:
        # Send the user back to the form for their own division.
        if division == EducationLevel.BASIC:
            return redirect("basic_education_evaluation")
        if division == EducationLevel.COLLEGE:
            return redirect("college_evaluation")
        # Never submitted anything in this session: go to the landing page.
        return redirect("home")

    return render(request, "evaluation/thankyou.html", {
        "evaluation": evaluation,
        "student_id": evaluation.student_id,
        "education_level": evaluation.education_level,
        "active_period": None,
    })

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect

def admin_login(request):

    username = ""
    password = ""

    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')  # ✅ get checkbox

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)

            # ✅ REMEMBER ME LOGIC
            if not remember:
                request.session.set_expiry(0)  # expires on browser close
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            messages.success(request, "Login successful!")
            return redirect('dashboard_home')

        else:
            messages.error(request, "Invalid credentials or not authorized.")

    return render(request, 'evaluation/admin_login.html', {
        'username': username,
        'password': password
    })


# Admin logout
def admin_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('admin_login')

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import TeacherEvaluation, Teacher, EvaluationItem

@login_required(login_url='admin_login')
def dashboard_home(request):
    semester = request.GET.get('semester')
    academic_year = request.GET.get('academic_year')
    teacher_id = request.GET.get('teacher')

    # AUTO DETECT ACADEMIC YEAR
    current_year = datetime.now().year
    current_month = datetime.now().month

    if current_month >= 6:
        default_academic_year = f"{current_year}-{current_year + 1}"
    else:
        default_academic_year = f"{current_year - 1}-{current_year}"

    # DEFAULT ONLY ON FIRST LOAD
    if academic_year is None:
        academic_year = default_academic_year

    # Only use default on first page load
    if academic_year is None:
        academic_year = default_academic_year

    evaluations_qs = TeacherEvaluation.objects.select_related(
        'teacher', 'subject', 'course'
    )

    if semester:
        evaluations_qs = evaluations_qs.filter(semester=semester)
    if academic_year:
        evaluations_qs = evaluations_qs.filter(academic_year=academic_year)
    if teacher_id:
        evaluations_qs = evaluations_qs.filter(teacher_id=teacher_id)

    # ===============================
    # BASIC SUMMARY COUNTS
    # ===============================
    total_teachers = Teacher.objects.count()
    total_evaluations = evaluations_qs.count()
    total_students = evaluations_qs.values('student_id').distinct().count()

    # ===============================
    # AVERAGE RATING
    # ===============================
    avg_rating_value = evaluations_qs.aggregate(avg=Avg('overall_rating'))['avg']
    avg_rating_value = round(avg_rating_value, 2) if avg_rating_value is not None else 0

    # ===============================
    # RATING DISTRIBUTION
    # ===============================
    rating_counts_qs = (
        EvaluationItem.objects
        .filter(evaluation__in=evaluations_qs)
        .exclude(rating='N')
        .values('rating')
        .annotate(count=Count('id'))
    )

    rating_data = {str(i): 0 for i in range(1, 6)}
    for r in rating_counts_qs:
        rating_data[str(r['rating'])] = r['count']

    # ===============================
    # RECENT EVALUATIONS
    # ===============================
    recent_evaluations = evaluations_qs.order_by('-submitted_at')[:5]

    # ===============================
    # COMPLETION & RESPONSE RATE
    # ===============================
    completion_rate = 100 if total_students else 0
    response_rate = round(total_evaluations / total_students, 2) if total_students else 0

    # ===============================
    # WEEKLY GROWTH RATE
    # ===============================
    today = timezone.now()
    last_7_days = today - timedelta(days=7)
    previous_7_days = today - timedelta(days=14)

    recent_count = TeacherEvaluation.objects.filter(
        submitted_at__gte=last_7_days
    ).count()

    previous_count = TeacherEvaluation.objects.filter(
        submitted_at__gte=previous_7_days,
        submitted_at__lt=last_7_days
    ).count()

    growth_rate = round(
        ((recent_count - previous_count) / previous_count) * 100, 1
    ) if previous_count else 0

    # ===============================
    # TOP TEACHER
    # ===============================
    top_teacher_data = (
        evaluations_qs
        .values('teacher__id', 'teacher__first_name', 'teacher__last_name')
        .annotate(avg=Avg('overall_rating'), total=Count('id'))
        .order_by('-avg')
        .first()
    )

    top_teacher = None
    top_teacher_avg = 0
    if top_teacher_data and top_teacher_data['avg'] is not None:
        top_teacher = top_teacher_data
        top_teacher_avg = round(top_teacher_data['avg'], 2)

    # ===============================
    # QUICK STATS
    # ===============================
    start_of_month = today.replace(day=1)
    monthly_evaluations = evaluations_qs.filter(submitted_at__gte=start_of_month).count()
    active_teachers = evaluations_qs.values('teacher').distinct().count()
    highest_rating = 5.0

    # ===============================
    # STATUS COUNTS
    # ===============================
    completed_count = total_evaluations
    pending_count = 0   # ❗ requires expected submissions to calculate
    inprogress_count = 0

    # ===============================
    # CONTEXT
    # ===============================
    context = {
        'total_teachers': total_teachers,
        'total_evaluations': total_evaluations,
        'total_students': total_students,

        'avg_rating': avg_rating_value,
        'rating_data': rating_data,
        'recent_evaluations': recent_evaluations,

        'completion_rate': completion_rate,
        'growth_rate': growth_rate,
        'top_teacher': top_teacher,
        'top_teacher_avg': top_teacher_avg,

        'completed_count': completed_count,
        'pending_count': pending_count,
        'inprogress_count': inprogress_count,

        'monthly_evaluations': monthly_evaluations,
        'active_teachers': active_teachers,
        'highest_rating': highest_rating,
        'response_rate': response_rate,

        'selected_semester': semester or '',
        'selected_academic_year': academic_year,
        'selected_teacher': teacher_id or '',
        'teachers': Teacher.objects.all(),
    }

    return render(request, 'admins/dashboard_home.html', context)

from django.db.models import Q

from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required(login_url='admin_login')
def teacher_search(request):

    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', 'default')

    teachers = Teacher.objects.prefetch_related('courses').all()

    # ================= SEARCH =================
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    # ================= DEFAULT ORDER FIX =================
    if filter_type == "default":
        teachers = teachers.order_by("first_name")

    teacher_data = []

    for t in teachers:
        stats = compute_teacher_stats(t)

        teacher_data.append({
            "id": t.id,
            "first_name": t.first_name,
            "last_name": t.last_name,
            "specialization": t.specialization or "",
            "courses": [c.name for c in t.courses.all()],
            "total_evaluations": stats.get("total_evaluations", 0) or 0,
            "average_rating": stats["overall_average"],
        })

    # ================= SORTING =================
    if filter_type == "highest_rating":
        teacher_data.sort(key=lambda x: x["average_rating"], reverse=True)

    elif filter_type == "lowest_rating":
        teacher_data.sort(key=lambda x: x["average_rating"])

    elif filter_type == "most_evaluations":
        teacher_data.sort(key=lambda x: x["total_evaluations"], reverse=True)

    return JsonResponse({"teachers": teacher_data})

from django.shortcuts import get_object_or_404, render
from django.db.models import Avg
from .models import Teacher, EvaluationItem

@login_required(login_url='admin_login')
def teacher_detail(request, pk):

    teacher = get_object_or_404(Teacher, pk=pk)

    evaluations = (
        teacher.evaluations
        .prefetch_related(
            'items',
            'section_scores__section'
        )
        .all()
        .order_by("-submitted_at")
    )

    # ================= AVERAGE RATING =================
    evaluation_averages = []

    for evaluation in evaluations:

        section_scores = evaluation.section_scores.all()

        valid_scores = [
            score.average_rating
            for score in section_scores
            if score.average_rating is not None
        ]

        if valid_scores:

            section_avg = (
                sum(valid_scores) / len(valid_scores)
            )

            evaluation_averages.append(section_avg)

    avg_rating = (
        round(sum(evaluation_averages) / len(evaluation_averages), 1)
        if evaluation_averages else 0
    )

    # ================= SECTION INSIGHTS =================
    section_insights = (
        SectionEvaluation.objects
        .filter(evaluation__teacher=teacher)
        .select_related('section')
        .values(
            'section__id',
            'section__prefix',
            'section__title'
        )
        .annotate(
            avg_rating=Avg('average_rating')
        )
        .order_by('section__prefix')
    )

    # ================= STRONGEST / WEAKEST =================
    strongest_section = None
    weakest_section = None

    section_insights_list = list(section_insights)

    if section_insights_list:

        strongest_section = max(
            section_insights_list,
            key=lambda x: x['avg_rating'] or 0
        )

        weakest_section = min(
            section_insights_list,
            key=lambda x: x['avg_rating'] or 0
        )

    context = {
        'teacher': teacher,
        'teacher_evaluations': evaluations,
        'avg_rating': avg_rating,

        # NEW
        'section_insights': section_insights_list,
        'strongest_section': strongest_section,
        'weakest_section': weakest_section,
    }

    return render(
        request,
        'admins/teacher_details.html',
        context
    )

# @login_required(login_url='admin_login')
# def teacher_detail(request, pk):
#     teacher = get_object_or_404(Teacher, pk=pk)
#     evaluations = teacher.evaluations.prefetch_related('items').all().order_by("-submitted_at")

#     # Calculate overall average rating
#     # Convert string ratings '1'..'5' to float
#     all_ratings = []
#     for eval in evaluations:
#         for item in eval.items.all():
#             if item.rating in ['1','2','3','4','5']:
#                 all_ratings.append(int(item.rating))
#     avg_rating = round(sum(all_ratings)/len(all_ratings),2) if all_ratings else 0

#     context = {
#         'teacher': teacher,
#         'teacher_evaluations': evaluations,
#         'avg_rating': avg_rating
#     }
#     return render(request, 'admins/teacher_details.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Course

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
import csv
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table
from .models import TeacherEvaluation, Teacher, Subject
from django.db.models import F


from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import TeacherEvaluation, Teacher, Subject

@login_required(login_url='admin_login')
def evaluations_list(request):
    # ===================== QUERYSET =====================
    qs = TeacherEvaluation.objects.select_related('teacher', 'subject', 'course').prefetch_related('items').order_by('-submitted_at')

    # ===================== FILTERS =====================
    teacher_id = request.GET.get("teacher")
    academic_year = request.GET.get("academic_year")
    semester = request.GET.get("semester")
    search = request.GET.get("search")
    sort = request.GET.get("sort")
    export = request.GET.get("export")

    if teacher_id:
        qs = qs.filter(teacher_id=teacher_id)

    if academic_year:
        qs = qs.filter(academic_year=academic_year)

    if semester:
        qs = qs.filter(semester=semester)

    # ===================== SEARCH =====================
    if search:
        qs = qs.filter(
            Q(teacher__first_name__icontains=search) |
            Q(teacher__last_name__icontains=search) |
            Q(academic_year__name__icontains=search)
        )

    # ===================== UPDATE OVERALL_RATING (BULK) =====================
    updates = []
    for e in qs:
        # Assign overall_rating from computed value
        if hasattr(e, 'overall_computed_rating') and e.overall_computed_rating is not None:
            e.overall_rating = e.overall_computed_rating

        # Compute stars for template
        rating = e.overall_rating or 0
        filled = int(rating)
        half = 1 if (rating - filled) >= 0.5 else 0
        empty = 5 - filled - half

        e.filled_stars_list = range(filled)
        e.half_star_list = range(half)
        e.empty_stars_list = range(empty)

        updates.append(e)

    # Bulk update overall_rating in DB
    if updates:
        TeacherEvaluation.objects.bulk_update(updates, ['overall_rating'])

    # ===================== SORT =====================
    if sort == "date_desc":
        qs = qs.order_by('-submitted_at')
    elif sort == "date_asc":
        qs = qs.order_by('submitted_at')
    elif sort == "rating_desc":
        qs = sorted(qs, key=lambda x: (getattr(x, 'overall_computed_rating', 0) or 0), reverse=True)
    elif sort == "rating_asc":
        qs = sorted(qs, key=lambda x: (getattr(x, 'overall_computed_rating', 0) or 0))

    # ===================== EXPORT =====================
    if export in ["excel", "pdf"]:
        for e in qs:
            ratings = []
            for item in e.items.all():
                value = str(getattr(item, 'rating', '')).strip().upper()
                if value == "N":
                    continue
                try:
                    num = float(value)
                    if 1 <= num <= 5:
                        ratings.append(num)
                except:
                    continue
            e.computed_rating = round(sum(ratings)/len(ratings), 2) if ratings else None

        if export == "excel":
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Evaluations"

            headers = ['Teacher', 'Subject', 'Overall Rating', 'Semester', 'A.Y.', 'Submitted']
            ws.append(headers)

            # Header styling
            for col in range(1, len(headers)+1):
                cell = ws.cell(row=1, column=col)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center')
                cell.fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")

            # Data rows
            for e in qs:
                ws.append([
                    f"{e.teacher.first_name} {e.teacher.last_name}" if e.teacher else "N/A",
                    e.subject.name if e.subject else "N/A",
                    e.computed_rating or "N/A",
                    e.semester,
                    e.academic_year,
                    e.submitted_at.strftime('%Y-%m-%d')
                ])

            # Auto-width
            for col in ws.columns:
                max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
                ws.column_dimensions[get_column_letter(col[0].column)].width = max_length + 5

            ws.freeze_panes = "A2"

            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=Evaluations.xlsx'
            wb.save(response)
            return response

        elif export == "pdf":
            from io import BytesIO
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch

            # -------- Helper: Truncate Text --------
            def truncate(text, max_len=30):
                text = str(text) if text else "N/A"
                return text if len(text) <= max_len else text[:max_len] + "…"

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            elements = []
            styles = getSampleStyleSheet()

            # -------- Custom Styles (Google-like) --------
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Title'],
                fontName='Helvetica-Bold',
                fontSize=18,
                textColor=colors.HexColor("#202124"),
                spaceAfter=14
            )

            header_style = ParagraphStyle(
                'HeaderStyle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=9,
                textColor=colors.white,
                alignment=1,  # center
                leading=11
            )

            cell_style = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=9,
                textColor=colors.HexColor("#202124"),
                leading=11,
                leftIndent=10
            )

            # -------- Title --------
            elements.append(Paragraph("Evaluations Report", title_style))
            elements.append(Spacer(1, 10))

            # -------- Table Data --------
            data = [
                [
                    Paragraph("Teacher<br/><font size=7 color='#E0E0E0'>Name</font>", header_style),
                    Paragraph("Subject<br/><font size=7 color='#E0E0E0'>Course</font>", header_style),
                    Paragraph("Rating<br/><font size=7 color='#E0E0E0'>Overall</font>", header_style),
                    Paragraph("Semester", header_style),
                    Paragraph("A.Y.", header_style),
                    Paragraph("Submitted<br/><font size=7 color='#E0E0E0'>Date</font>", header_style),
                ]
            ]

            for e in qs:
                teacher = f"{e.teacher.first_name} {e.teacher.last_name}" if e.teacher else "N/A"
                subject = e.subject.name if e.subject else "N/A"

                data.append([
                    Paragraph(truncate(teacher, 28), cell_style),
                    Paragraph(truncate(subject, 25), cell_style),
                    Paragraph(str(e.computed_rating or "N/A"), cell_style),
                    Paragraph(truncate(e.semester, 10), cell_style),
                    Paragraph(truncate(e.academic_year, 10), cell_style),
                    Paragraph(e.submitted_at.strftime('%Y-%m-%d'), cell_style),
                ])

            # -------- Table --------
            page_width = doc.width  # usable width inside margins

            table = Table(
                data,
                colWidths=[
                    page_width * 0.28,
                    page_width * 0.22,
                    page_width * 0.10,
                    page_width * 0.12,
                    page_width * 0.12,
                    page_width * 0.16,
                ],
                repeatRows=1
            )

            table.hAlign = 'CENTER'

            # -------- Table Styling (Google-like clean UI) --------
            table.setStyle(TableStyle([

                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4285F4")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

                # Body
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),

                # Zebra stripes (subtle)
                ('BACKGROUND', (0, 2), (-1, -1), colors.HexColor("#F8FAFF")),

                # Alignment
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),

                # Padding (important for clean look)
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

                # Grid (light, modern)
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),

                # Header font
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

                # Vertical align
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            ]))

            elements.append(table)

            doc.build(elements)

            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=Evaluations.pdf'
            return response

    # ===================== PAGINATION =====================
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    academic_years = [
        "2023-2024",
        "2024-2025",
        "2025-2026",
        "2026-2027",
        "2027-2028",
    ]

    # ===================== CONTEXT =====================
    context = {
        'page_obj': page_obj,
        'teachers': Teacher.objects.all(),
        'academic_years': academic_years,
        'selected_teacher': teacher_id or '',
        'selected_academic_year': academic_year or '',
        'selected_semester': semester or '',
        'search': search or '',
        'sort': sort or '',
    }

    return render(request, 'admins/evaluations.html', context)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import TeacherEvaluation
import openpyxl
from openpyxl.styles import Font, Alignment
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .models import TeacherEvaluation

@login_required(login_url='admin_login')
def evaluation_detail(request, evaluation_id):
    from django.contrib.staticfiles import finders
    from io import BytesIO
    from django.http import HttpResponse
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    evaluation = get_object_or_404(
        TeacherEvaluation.objects.prefetch_related('items__question__section'),
        id=evaluation_id
    )

    # ------------------- BUILD SECTIONS DICT -------------------
    sections_dict = {}
    for item in evaluation.items.all():
        section = item.question.section
        if section.prefix not in sections_dict:
            sections_dict[section.prefix] = {
                'title': section.title,
                'items': [],
                'total': 0
            }
        sections_dict[section.prefix]['items'].append(item)
        try:
            rating_num = int(item.rating)
            sections_dict[section.prefix]['total'] += rating_num
        except ValueError:
            pass

    # ------------------- EXPORT LOGIC -------------------
    export_type = request.GET.get('export', None)
    teacher_name = f"{evaluation.teacher.first_name}_{evaluation.teacher.last_name}".replace(" ", "_")

    # ------------------- EXCEL EXPORT -------------------
    if export_type == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Evaluation"

        # Header
        ws.append([f"Teacher Evaluation Report"])
        ws.append([f"Teacher: {evaluation.teacher.first_name} {evaluation.teacher.last_name}"])
        ws.append([f"Semester: {evaluation.semester} | Academic Year: {evaluation.academic_year}"])
        ws.append([f"Submitted At: {evaluation.submitted_at.strftime('%B %d, %Y %I:%M %p')}"])
        ws.append([])

        # Column titles
        ws.append(["Section", "Question", "Rating"])
        for col in range(1, 4):
            ws.cell(row=6, column=col).font = Font(bold=True)
            ws.cell(row=6, column=col).alignment = Alignment(horizontal='center')

        row_num = 7
        for section in sections_dict.values():
            ws.cell(row=row_num, column=1, value=section['title']).font = Font(bold=True)
            row_num += 1
            for idx, item in enumerate(section['items']):
                ws.append(["", f"{item.question.order}. {item.question.text}", item.rating])
                # Alternate row fill
                if idx % 2 == 0:
                    for col in range(1, 4):
                        ws.cell(row=row_num, column=col).fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
                row_num += 1
            # Section total
            ws.append(["", "Section Total", section['total']])
            for col in range(2, 4):
                ws.cell(row=row_num, column=col).font = Font(bold=True)
                ws.cell(row=row_num, column=col).fill = PatternFill(start_color="E5E7EB", end_color="E5E7EB", fill_type="solid")
            row_num += 2

        # Additional Comments
        if evaluation.commendable_features:
            ws.append(["Additional Comments", "Commendable Features", ""])
            ws.append(["", evaluation.commendable_features, ""])
            row_num += 2
        if evaluation.suggestions_improvement:
            ws.append(["Additional Comments", "Suggestions for Improvement", ""])
            ws.append(["", evaluation.suggestions_improvement, ""])
            row_num += 2

        # Auto-adjust column widths
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column].width = max_length + 5

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={teacher_name}_evaluation.xlsx'
        wb.save(response)
        return response

    # ------------------- PDF EXPORT -------------------
    elif export_type == 'pdf':
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # ------------------- HEADER: LOGO + TITLE CENTERED -------------------
        logo_path = finders.find('HIC_LOGO_TRANSPARENT.png')
        logo_img = None
        if logo_path:
            # slightly smaller logo
            logo_img = Image(logo_path, width=1.0*inch, height=1.0*inch)

        header_data = []
        if logo_img:
            header_data.append([logo_img, Paragraph(
                "<b>Teacher Evaluation Report</b><br/><font size=12>Academic Evaluation Record</font>",
                styles['Title']
            )])
            col_widths = [1.0*inch, 4.5*inch]
        else:
            header_data.append([Paragraph(
                "<b>Teacher Evaluation Report</b><br/><font size=12>Academic Evaluation Record</font>",
                styles['Title']
            )])
            col_widths = [6*inch]

        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 18))  # balanced spacing after header

        # ------------------- BASIC INFO -------------------
        info_data = [
            ["Subject", evaluation.subject.name if evaluation.subject else "N/A"],
            ["Teacher", f"{evaluation.teacher.first_name} {evaluation.teacher.last_name}"],
            ["Semester", evaluation.semester],
            ["Academic Year", evaluation.academic_year],
            ["Year Level", evaluation.year_level],
            ["Student ID", evaluation.student_id]
        ]
        if evaluation.student_name:
            info_data.append(["Student Name", evaluation.student_name])
        info_data.append(["Date Submitted", evaluation.submitted_at.strftime('%B %d, %Y %I:%M %p')])

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEBELOW', (1,0), (1,-1), 0.5, colors.gray)
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))

        # ------------------- SECTIONS -------------------
        for prefix, section in sections_dict.items():
            elements.append(Paragraph(f"{prefix}. {section['title']}", styles['Heading3']))
            section_data = [["Question", "Rating"]]
            for idx, item in enumerate(section['items']):
                section_data.append([f"{item.question.order}. {item.question.text}", str(item.rating)])
            section_data.append(["Total Score", str(section['total'])])

            section_table = Table(section_data, colWidths=[4*inch, 2*inch])
            style_list = [
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F46E5")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN',(1,1),(-1,-1),'CENTER'),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.gray),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
            ]
            for i in range(1, len(section_data)-1):
                if i % 2 == 0:
                    style_list.append(('BACKGROUND', (0,i), (-1,i), colors.HexColor("#f3f4f6")))
            style_list.append(('BACKGROUND', (0,len(section_data)-1), (-1,len(section_data)-1), colors.HexColor("#e5e7eb")))
            style_list.append(('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'))
            style_list.append(('FONTNAME', (0,len(section_data)-1), (-1,len(section_data)-1), 'Helvetica-Bold'))
            section_table.setStyle(TableStyle(style_list))
            elements.append(section_table)
            elements.append(Spacer(1, 12))

        # ------------------- ADDITIONAL COMMENTS -------------------
        if evaluation.commendable_features or evaluation.suggestions_improvement:
            elements.append(Paragraph("Additional Comments", styles['Heading2']))
            elements.append(Spacer(1, 6))
            if evaluation.commendable_features:
                elements.append(Paragraph("A. Commendable Features", styles['Heading4']))
                elements.append(Paragraph(evaluation.commendable_features, styles['Normal']))
                elements.append(Spacer(1, 6))
            if evaluation.suggestions_improvement:
                elements.append(Paragraph("B. Suggestions for Improvement", styles['Heading4']))
                elements.append(Paragraph(evaluation.suggestions_improvement, styles['Normal']))
                elements.append(Spacer(1, 6))

        # ------------------- BUILD PDF -------------------
        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={teacher_name}_evaluation.pdf'
        return response

    # ------------------- NORMAL PAGE VIEW -------------------
    context = {
        'evaluation': evaluation,
        'sections': sections_dict
    }
    return render(request, 'admins/evaluation_detail.html', context)

# ------------------ SECTIONS ------------------
@login_required(login_url='admin_login')
def sections_list(request):
    sections = Section.objects.prefetch_related('questions').all()
    return render(request, 'admins/sections.html', {'sections': sections})

@login_required(login_url='admin_login')
def section_add(request):
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section created successfully!')
        else:
            messages.error(request, 'Error creating section.')
    return redirect('sections_list')  # Always redirect back to sections page

@login_required(login_url='admin_login')
def section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section updated successfully!')
        else:
            messages.error(request, 'Error updating section.')
    return redirect('sections_list')

@login_required(login_url='admin_login')
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == 'POST':
        section.delete()
        messages.success(request, 'Section deleted successfully!')
    return redirect('sections_list')

# ------------------ QUESTIONS ------------------
@login_required(login_url='admin_login')
def question_add(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.section = section  # assign the section manually
            question.save()
            messages.success(request, "Question added successfully!")
        else:
            # If form errors, show them for debugging
            messages.error(request, f"Error adding question: {form.errors}")
    return redirect('sections_list')


@login_required(login_url='admin_login')
def question_edit(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        new_text = request.POST.get('text', '').strip()
        if new_text:
            question.text = new_text
            question.save()
            messages.success(request, 'Question updated successfully.')
        else:
            messages.error(request, 'Question text cannot be empty.')
    return redirect('sections_list')  # or your URL name for this page


@login_required(login_url='admin_login')
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
    return redirect('sections_list')


# ------------------- TEACHERS -------------------

from django.db.models import Count, Avg
from django.contrib.auth.decorators import login_required

@login_required(login_url='admin_login')
def teachers_list(request):
    query = request.GET.get('q', '')

    teachers = Teacher.objects.all()

    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    for teacher in teachers:
        stats = compute_teacher_stats(teacher)

        teacher.total_evaluations = stats["total_evaluations"]
        teacher.average_rating = stats["overall_average"]
        teacher.section_averages = stats["section_averages"]

    context = {
        'teachers': teachers,
        'sections': Section.objects.all(),
        'subjects': Subject.objects.all(),
        'courses': Course.objects.all(),
    }

    return render(request, 'admins/teachers.html', context)

def compute_teacher_stats(teacher):
    evaluations = teacher.evaluations.prefetch_related("section_scores__section")

    total_evaluations = evaluations.count()

    section_map = {}

    for evaluation in evaluations:
        for sec in evaluation.section_scores.all():
            if sec.average_rating is None:
                continue

            sid = sec.section_id
            section_map.setdefault(sid, []).append(sec.average_rating)

    # 📊 Section averages
    section_averages = {
        sid: round(sum(values) / len(values), 2)
        for sid, values in section_map.items()
    }

    # ⭐ Overall average (from all section values)
    all_values = [v for values in section_map.values() for v in values]

    overall_avg = round(sum(all_values) / len(all_values), 2) if all_values else 0

    return {
        "total_evaluations": total_evaluations,
        "overall_average": overall_avg,
        "section_averages": section_averages
    }


@login_required(login_url="admin_login")
def teacher_add(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        specialization = request.POST.get("specialization", "").strip()
        education_level = request.POST.get(
            "education_level",
            EducationLevel.COLLEGE,
        ).strip().upper()

        valid_divisions = {
            choice[0] for choice in EducationLevel.choices
        }

        if education_level not in valid_divisions:
            messages.error(request, "Please select a valid division.")
            return redirect("teachers_list")

        teacher = Teacher.objects.create(
            first_name=first_name,
            last_name=last_name,
            specialization=specialization,
            education_level=education_level,
        )

        courses = request.POST.getlist("courses")
        teacher.courses.set(courses)

        messages.success(
            request,
            f"{teacher} added successfully to "
            f"{teacher.get_education_level_display()}.",
        )

    return redirect("teachers_list")


@login_required(login_url="admin_login")
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        specialization = request.POST.get("specialization", "").strip()
        education_level = request.POST.get(
            "education_level",
            teacher.education_level,
        ).strip().upper()

        valid_divisions = {
            choice[0] for choice in EducationLevel.choices
        }

        if education_level not in valid_divisions:
            messages.error(request, "Please select a valid division.")
            return redirect("teachers_list")

        teacher.first_name = first_name
        teacher.last_name = last_name
        teacher.specialization = specialization
        teacher.education_level = education_level
        teacher.save()

        courses = request.POST.getlist("courses")
        teacher.courses.set(courses)

        messages.success(
            request,
            f"{teacher} updated successfully.",
        )

    return redirect("teachers_list")

@login_required(login_url='admin_login')
def teacher_delete(request, pk):

    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == "POST":

        try:
            teacher.delete()
            messages.success(request, "Teacher deleted successfully!")

        except ProtectedError:
            messages.error(
                request,
                "Cannot delete teacher because evaluation records exist."
            )

    return redirect('teachers_list')

# ------------------- COURSES -------------------
@login_required(login_url='admin_login')
def courses_list(request):
    query = request.GET.get('q', '')
    courses_qs = Course.objects.all()
    if query:
        courses_qs = courses_qs.filter(name__icontains=query)

    paginator = Paginator(courses_qs.order_by('name'), 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admins/courses_list.html', {
        'courses': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'query': query,
    })


# ADD Course
@login_required(login_url='admin_login')
def course_add(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course added successfully!")
        else:
            errors = [e for field_errors in form.errors.values() for e in field_errors]
            # Join them into a single string
            messages.error(request, f"❌ {' '.join(errors)}")
    return redirect('courses_list')


# EDIT Course
@login_required(login_url='admin_login')
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully!")
        else:
            errors = [e for field_errors in form.errors.values() for e in field_errors]
            # Join them into a single string
            messages.error(request, f"❌ {' '.join(errors)}")

    return redirect('courses_list')


# DELETE Course
@login_required(login_url='admin_login')
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully!")
    return redirect('courses_list')


# API: Teacher list in JSON for Select2
def teacher_list_json(request):
    division = request.GET.get(
        "division",
        EducationLevel.COLLEGE,
    ).strip().upper()

    # Default to College when the division is missing or invalid.
    if division not in EducationLevel.values:
        division = EducationLevel.COLLEGE

    query = request.GET.get("q", "").strip()

    teachers = Teacher.objects.filter(
        education_level=division,
    ).order_by(
        "last_name",
        "first_name",
        "id",
    )

    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

    results = [
        {
            "id": teacher.id,
            "text": str(teacher),
            "first_name": teacher.first_name or "",
            "last_name": teacher.last_name or "",
        }
        for teacher in teachers[:50]
    ]

    return JsonResponse({
        "results": results,
    })


# ----------------- SUBJECT VIEWS -----------------
@login_required(login_url='admin_login')
def subjects_list(request):
    query = request.GET.get('q', '')
    subjects = Subject.objects.all()
    if query:
        subjects = subjects.filter(name__icontains=query)
    return render(request, 'admins/subject_list.html', {'subjects': subjects})

@login_required(login_url='admin_login')
def subject_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Subject.objects.create(name=name)
            messages.success(request, "Subject added successfully!")
        return redirect('subjects_list')

@login_required(login_url='admin_login')
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            subject.name = name
            subject.save()
            messages.success(request, "Subject updated successfully!")
        return redirect('subjects_list')

@login_required(login_url='admin_login')
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, "Subject deleted successfully!")
        return redirect('subjects_list')


# ============================================================
# EVALUATION PERIOD MANAGEMENT
# ============================================================

from django.views.decorators.http import require_POST


@login_required(login_url="admin_login")
def evaluation_periods_list(request):
    periods = EvaluationPeriod.objects.all()

    open_periods = EvaluationPeriod.objects.filter(
        is_open=True
    )

    context = {
        "periods": periods,
        "open_periods": open_periods,
        "active_period": open_periods.first(),
        "form": EvaluationPeriodForm(),
    }

    return render(
        request,
        "admins/evaluation_periods.html",
        context,
    )

@login_required(login_url="admin_login")
def evaluation_period_add(request):
    if request.method == "POST":
        division = request.POST.get("education_level", "").strip().upper()

        if division not in {"COLLEGE", "BASIC", "BOTH"}:
            messages.error(request, "Please select a valid division.")
            return render(request, "admins/evaluation_period_add.html", {
                "form": EvaluationPeriodForm(request.POST),
                "selected_division": "COLLEGE",
            })

        levels = (
            [EducationLevel.COLLEGE, EducationLevel.BASIC]
            if division == "BOTH" else [division]
        )

        forms_to_save = []
        for level in levels:
            data = request.POST.copy()
            data["education_level"] = level
            forms_to_save.append(EvaluationPeriodForm(data))

        if all(f.is_valid() for f in forms_to_save):
            try:
                with transaction.atomic():
                    for f in forms_to_save:
                        f.save()
            except IntegrityError as e:
                print(e)  # shows which constraint failed in the console
                messages.error(request, "A period with these details already exists for one of the divisions.")
            else:
                messages.success(
                    request,
                    "Evaluation periods created successfully."
                    if len(levels) > 1 else "Evaluation period created successfully.",
                )
                return redirect("evaluation_periods_list")

        bad_form = next((f for f in forms_to_save if not f.is_valid()), forms_to_save[0])
        return render(request, "admins/evaluation_period_add.html", {
            "form": bad_form,
            "selected_division": division,
        })

    return render(request, "admins/evaluation_period_add.html", {
        "form": EvaluationPeriodForm(),
        "selected_division": "COLLEGE",
    })

@login_required(login_url="admin_login")
def evaluation_period_edit(request, pk):
    period = get_object_or_404(EvaluationPeriod, pk=pk)

    if request.method == "POST":
        post_data = request.POST.copy()
        submitted_division = post_data.get("education_level", "").strip().upper()
        make_both = submitted_division == "BOTH"

        # The form saves this period under its own division.
        if make_both:
            post_data["education_level"] = period.education_level

        form = EvaluationPeriodForm(post_data, instance=period)

        if form.is_valid():
            try:
                with transaction.atomic():
                    period = form.save()

                    if make_both:
                        other_level = (
                            EducationLevel.BASIC
                            if period.education_level == EducationLevel.COLLEGE
                            else EducationLevel.COLLEGE
                        )

                        twin = EvaluationPeriod.objects.filter(
                            education_level=other_level,
                            semester=period.semester,
                            academic_year=period.academic_year,
                        ).first()

                        if twin is None:
                            # Clone this period for the other division.
                            twin = EvaluationPeriod.objects.get(pk=period.pk)
                            twin.pk = None
                            twin.id = None
                            twin._state.adding = True
                            twin.education_level = other_level
                            twin.is_open = False
                            twin.save()
                            created = True
                        else:
                            created = False

                        # Keep dates in sync on an existing twin, if your model has them.
                        for field in ("start_date", "end_date"):
                            if hasattr(period, field) and hasattr(twin, field):
                                setattr(twin, field, getattr(period, field))
                        twin.save()

                        # Match the open state of this period.
                        if period.is_open:
                            EvaluationPeriod.objects.exclude(pk=twin.pk).filter(
                                education_level=other_level, is_open=True
                            ).update(is_open=False)
                            twin.is_open = True
                            twin.save(update_fields=["is_open", "updated_at"])
            except IntegrityError:
                messages.error(request, "Could not save. A matching period may already exist.")
            else:
                messages.success(
                    request,
                    "Evaluation period updated for both divisions."
                    if make_both else "Evaluation period updated successfully.",
                )
                return redirect("evaluation_periods_list")

        return render(request, "admins/evaluation_period_add.html", {
            "form": form,
            "period": period,
            "selected_division": period.education_level,
        })

    return render(request, "admins/evaluation_period_add.html", {
        "form": EvaluationPeriodForm(instance=period),
        "period": period,
        "selected_division": period.education_level,
    })

@login_required(login_url="admin_login")
@require_POST
def evaluation_period_open(request, pk):
    period = get_object_or_404(EvaluationPeriod, pk=pk)

    try:
        with transaction.atomic():
            EvaluationPeriod.objects.exclude(
                pk=period.pk
            ).filter(
                is_open=True,
                education_level=period.education_level,   # <-- added
            ).update(is_open=False)

            period.is_open = True
            period.save(update_fields=["is_open", "updated_at"])

        messages.success(
            request,
            f"{period.get_education_level_display()}: "
            f"{period.academic_year} - {period.get_semester_display()} is now open. "
            "Any other open period in this division has been closed.",
        )
    except IntegrityError:
        messages.error(request, "The period could not be opened. Please refresh and try again.")

    return redirect("evaluation_periods_list")


@login_required(login_url="admin_login")
@require_POST
def evaluation_period_close(request, pk):
    period = get_object_or_404(EvaluationPeriod, pk=pk)

    if period.is_open:
        period.is_open = False
        period.save(update_fields=["is_open", "updated_at"])

        messages.success(
            request,
            (
                f"{period.academic_year} - "
                f"{period.get_semester_display()} is now closed. "
                "New student submissions are blocked."
            ),
        )
    else:
        messages.info(request, "This evaluation period is already closed.")

    return redirect("evaluation_periods_list")
