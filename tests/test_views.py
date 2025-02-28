import pytest
from django.test import TestCase, Client
from django.urls import reverse
from survey.models import Survey
from users.models import User
from datetime import date, timedelta


@pytest.mark.django_db
class TestViews(TestCase):
    def setUp(self):
        # Créer un client et un utilisateur
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com', first_name='Test', last_name='User',
            password='testpassword', is_active=True
        )
        
        # Connecter l'utilisateur
        self.client.login(email='test@example.com', password='testpassword')
        
        # Créer un sondage
        self.survey = Survey.objects.create(
            title='Test Survey', description='Test Description',
            start_date=date.today(), end_date=date.today() + timedelta(days=7),
            creator=self.user
        )
        
        # URLs
        self.list_url = reverse('liste')
        self.detail_url = reverse('survey_detail', args=[self.survey.pk])
    
    def test_list_view(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'survey/liste.html')
        self.assertIn(self.survey, response.context['surveys'])
    
    def test_unauthorized_access(self):
        # Déconnecter l'utilisateur
        self.client.logout()
        
        # Tester l'accès à la liste (devrait être accessible sans authentification)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        
        # Tester l'accès à la vue détaillée (devrait rediriger vers la page de connexion)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)  # Redirection vers la page de connexion
