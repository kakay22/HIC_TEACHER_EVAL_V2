from django import forms
from .models import EvaluationPeriod, Section, Question, Course, EvaluationItem, TeacherEvaluation, Subject, Teacher


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['prefix', 'title']
        widgets = {
            'prefix': forms.TextInput(attrs={'class': 'border p-2 w-full', 'placeholder': 'Section Prefix'}),
            'title': forms.TextInput(attrs={'class': 'border p-2 w-full', 'placeholder': 'Section Title'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'border p-2 w-full', 'placeholder': 'Question Text'}),
            'order': forms.NumberInput(attrs={'class': 'border p-2 w-full', 'placeholder': 'Order'}),
            'section': forms.HiddenInput(),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'code': forms.TextInput(attrs={'class': 'w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }


class EvaluationPeriodForm(forms.ModelForm):
    class Meta:
        model = EvaluationPeriod
        fields = [
            "education_level",
            "academic_year",
            "semester",
            "start_date",
            "end_date",
        ]
        widgets = {
            "education_level": forms.Select(attrs={
                "class": "w-full border p-2 rounded",
            }),
            "academic_year": forms.TextInput(attrs={
                "class": "w-full border p-2 rounded",
                "placeholder": "2026-2027",
            }),
            "semester": forms.Select(attrs={
                "class": "w-full border p-2 rounded",
            }),
            "start_date": forms.DateInput(attrs={
                "class": "w-full border p-2 rounded",
                "type": "date",
            }),
            "end_date": forms.DateInput(attrs={
                "class": "w-full border p-2 rounded",
                "type": "date",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "The end date cannot be before the start date.",
            )

        return cleaned_data