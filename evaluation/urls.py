from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --------------------------------------------------
    # PUBLIC PAGES
    # --------------------------------------------------
    path('', views.home, name="home"),
    path(
        "college/",
        views.college_evaluation,
        name="college_evaluation",
    ),
    path(
        "basic-education/",
        views.basic_education_evaluation,
        name="basic_education_evaluation",
    ),
    path(
        "validate-evaluation/",
        views.validate_evaluation,
        name="validate_evaluation",
    ),
    path('thank-you/', views.thank_you, name="thank_you"),

    # --------------------------------------------------
    # ADMIN AUTHENTICATION
    # --------------------------------------------------
    path('admin-login/', views.admin_login, name="admin_login"),
    path('admin-logout/', views.admin_logout, name="admin_logout"),

    # --------------------------------------------------
    # ADMIN DASHBOARD
    # --------------------------------------------------
    path(
        'dashboard-home/',
        views.dashboard_home,
        name="dashboard_home",
    ),

    # --------------------------------------------------
    # TEACHER MANAGEMENT
    # --------------------------------------------------
    path('teachers/', views.teachers_list, name='teachers_list'),
    path(
        'teachers/search/',
        views.teacher_search,
        name='teacher_search',
    ),
    path(
        'api/teachers/',
        views.teacher_list_json,
        name='teacher_list_json',
    ),
    path(
        'teachers/<int:pk>/detail/',
        views.teacher_detail,
        name='teacher_detail',
    ),
    path('teachers/add/', views.teacher_add, name='teacher_add'),
    path(
        'teachers/edit/<int:pk>/',
        views.teacher_edit,
        name='teacher_edit',
    ),
    path(
        'teachers/delete/<int:pk>/',
        views.teacher_delete,
        name='teacher_delete',
    ),

    # --------------------------------------------------
    # EVALUATION RECORDS
    # --------------------------------------------------
    path(
        'evaluations-list/',
        views.evaluations_list,
        name='evaluations_list',
    ),
    path(
        'evaluations/<int:evaluation_id>/',
        views.evaluation_detail,
        name='evaluation_detail',
    ),

    # --------------------------------------------------
    # SECTIONS AND QUESTIONS
    # --------------------------------------------------
    path('sections/', views.sections_list, name='sections_list'),
    path(
        'sections/add/',
        views.section_add,
        name='section_add',
    ),
    path(
        'sections/<int:pk>/edit/',
        views.section_edit,
        name='section_edit',
    ),
    path(
        'sections/<int:pk>/delete/',
        views.section_delete,
        name='section_delete',
    ),
    path(
        'sections/<int:section_id>/questions/add/',
        views.question_add,
        name='question_add',
    ),
    path(
        'questions/<int:question_id>/edit/',
        views.question_edit,
        name='question_edit',
    ),
    path(
        'questions/<int:pk>/delete/',
        views.question_delete,
        name='question_delete',
    ),

    # --------------------------------------------------
    # COURSE MANAGEMENT
    # --------------------------------------------------
    path('courses/', views.courses_list, name='courses_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path(
        'courses/<int:pk>/edit/',
        views.course_edit,
        name='course_edit',
    ),
    path(
        'courses/<int:pk>/delete/',
        views.course_delete,
        name='course_delete',
    ),

    # --------------------------------------------------
    # SUBJECT MANAGEMENT
    # --------------------------------------------------
    path('subjects/', views.subjects_list, name='subjects_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path(
        'subjects/<int:pk>/edit/',
        views.subject_edit,
        name='subject_edit',
    ),
    path(
        'subjects/<int:pk>/delete/',
        views.subject_delete,
        name='subject_delete',
    ),

    # --------------------------------------------------
    # EVALUATION PERIOD MANAGEMENT
    # --------------------------------------------------
    path(
        "evaluation-periods/",
        views.evaluation_periods_list,
        name="evaluation_periods_list",
    ),
    path(
        "evaluation-periods/add/",
        views.evaluation_period_add,
        name="evaluation_period_add",
    ),
    path(
        "evaluation-periods/<int:pk>/edit/",
        views.evaluation_period_edit,
        name="evaluation_period_edit",
    ),
    path(
        "evaluation-periods/<int:pk>/open/",
        views.evaluation_period_open,
        name="evaluation_period_open",
    ),
    path(
        "evaluation-periods/<int:pk>/close/",
        views.evaluation_period_close,
        name="evaluation_period_close",
    ),

    # --------------------------------------------------
    # ADMIN PASSWORD RESET
    # --------------------------------------------------
    path(
        'admin/forgot-password/',
        auth_views.PasswordResetView.as_view(
            template_name='admins/admin_forgot_password.html',
            email_template_name='admins/admin_password_reset_email.html',
            subject_template_name='admins/admin_password_reset_subject.txt',
            success_url='/admin/forgot-password/done/',
        ),
        name='admin_forgot_password',
    ),
    path(
        'admin/forgot-password/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='admins/admin_forgot_password_done.html',
        ),
        name='admin_forgot_password_done',
    ),
    path(
        'admin/reset-password/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='admins/admin_reset_password_confirm.html',
            success_url='/admin/reset-password/complete/',
        ),
        name='admin_reset_password_confirm',
    ),
    path(
        'admin/reset-password/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='admins/admin_reset_password_complete.html',
        ),
        name='admin_reset_password_complete',
    ),
]