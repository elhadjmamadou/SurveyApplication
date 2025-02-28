import pytest
from django.test import TestCase
from django.forms import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from survey.models import Survey, Question, Choice, Response, Answer
from users.models import User


@pytest.mark.django_db
class TestModels(TestCase):
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            email='test@example.com', first_name='Test', last_name='User',
            password='testpassword', is_active=True
        )
        
        # Créer un sondage
        self.survey = Survey.objects.create(
            title='Test Survey', description='Test Description',
            start_date=date.today(), end_date=date.today() + timedelta(days=7),
            creator=self.user
        )
        
        # Créer une question texte
        self.text_question = Question.objects.create(
            text='Text Question', question_type=Question.TEXT, survey=self.survey
        )
        
        # Créer une question à choix unique
        self.choice_question = Question.objects.create(
            text='Choice Question', question_type=Question.SINGLE_CHOICE, survey=self.survey
        )
        
        # Créer des choix pour la question à choix
        self.choice1 = Choice.objects.create(question=self.choice_question, text='Choice 1')
        self.choice2 = Choice.objects.create(question=self.choice_question, text='Choice 2')
        
        # Créer une réponse
        self.response = Response.objects.create(user=self.user, survey=self.survey)
    
    def test_models(self):
        # Test Survey
        self.assertEqual(str(self.survey), 'Test Survey')
        self.assertTrue(self.survey.is_active())
        
        # Test Question
        self.assertEqual(str(self.text_question), 'Text Question')
        self.assertEqual(self.survey.questions.count(), 2)
        
        # Test Choice
        self.assertEqual(str(self.choice1), 'Choice 1')
        self.assertEqual(self.choice_question.choices.count(), 2)
        
        # Test Response
        self.assertEqual(str(self.response), f"Response by {self.user} for {self.survey}")
        
        # Test Answer
        text_answer = Answer.objects.create(
            response=self.response, question=self.text_question, text_answer='Text response'
        )
        choice_answer = Answer.objects.create(
            response=self.response, question=self.choice_question, choice=self.choice1
        )
        
        self.assertEqual(str(text_answer), f"Answer to {self.text_question}")
        self.assertEqual(str(choice_answer), f"Answer to {self.choice_question}")
