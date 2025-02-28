import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.mark.django_db
class TestUserModel(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpassword'
        }
    
    def test_create_user(self):
        # Tester la création d'un utilisateur normal
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertFalse(user.is_active)  # Par défaut, is_active est False
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.user_data['password']))
    
    def test_create_superuser(self):
        # Tester la création d'un superutilisateur
        superuser = User.objects.create_superuser(**self.user_data)
        
        self.assertEqual(superuser.email, self.user_data['email'])
        self.assertEqual(superuser.first_name, self.user_data['first_name'])
        self.assertEqual(superuser.last_name, self.user_data['last_name'])
        self.assertTrue(superuser.is_active)  # Pour les superusers, is_active est True
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.check_password(self.user_data['password']))
    
    def test_user_str_method(self):
        # Tester la méthode __str__ si elle existe
        user = User.objects.create_user(**self.user_data)
        
        # Vérifier si la méthode __str__ retourne l'email ou une autre représentation
        self.assertEqual(str(user), self.user_data['email'])
    
    def test_email_uniqueness(self):
        # Tester l'unicité de l'email
        User.objects.create_user(**self.user_data)
        
        # Tenter de créer un autre utilisateur avec le même email
        with self.assertRaises(Exception):
            User.objects.create_user(
                email=self.user_data['email'],
                first_name='Another',
                last_name='User',
                password='anotherpassword'
            )
    
    def test_date_joined_auto_set(self):
        # Tester que date_joined est automatiquement défini
        before_creation = timezone.now()
        user = User.objects.create_user(**self.user_data)
        after_creation = timezone.now()
        
        # Vérifier que date_joined est entre before_creation et after_creation
        self.assertTrue(before_creation <= user.date_joined <= after_creation)
