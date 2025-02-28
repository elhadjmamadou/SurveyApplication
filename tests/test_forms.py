import pytest
from django.test import TestCase
from django.forms import ValidationError
from datetime import date, timedelta
from survey.forms import SurveyForm, QuestionForm
from survey.models import Survey, Question
from users.models import User


@pytest.mark.django_db
class TestForms(TestCase):
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            email='test@example.com', first_name='Test', last_name='User',
            password='testpassword', is_active=True
        )
        
        # Dates valides pour les tests
        self.today = date.today()
        self.future_date = self.today + timedelta(days=7)
    
    def test_survey_form_valid_data(self):
        # Tester le formulaire avec des données valides
        form_data = {
            'title': 'Test Survey',
            'description': 'Test Description',
            'start_date': self.today,
            'end_date': self.future_date,
            'creator': self.user.id
        }
        form = SurveyForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_survey_form_invalid_dates(self):
        # Tester le formulaire avec une date de fin antérieure à la date de début
        form_data = {
            'title': 'Test Survey',
            'description': 'Test Description',
            'start_date': self.future_date,  # Date future
            'end_date': self.today,  # Date d'aujourd'hui (antérieure à la date de début)
            'creator': self.user.id
        }
        form = SurveyForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_survey_form_missing_data(self):
        # Tester le formulaire avec des données manquantes
        form_data = {
            'title': '',  # Titre manquant
            'description': 'Test Description',
            'start_date': self.today,
            'end_date': self.future_date,
            'creator': self.user.id
        }
        form = SurveyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_question_form_valid_data(self):
        # Tester le formulaire de question avec des données valides
        form_data = {
            'text': 'Test Question',
            'question_type': Question.TEXT
        }
        form = QuestionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_question_form_missing_data(self):
        # Tester le formulaire de question avec des données manquantes
        form_data = {
            'text': '',  # Texte manquant
            'question_type': Question.TEXT
        }
        form = QuestionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)
