import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from survey.models import Survey, Question, Choice, Response, Answer

User = get_user_model()

@pytest.fixture
def user_a(db):
    return User.objects.create_user(username='user_a', password='password123')

@pytest.fixture
def user_b(db):
    return User.objects.create_user(username='user_b', password='password123')

@pytest.fixture
def survey(user_a, db):
    survey_instance = Survey.objects.create(
        title="Test Survey",
        description="A survey for testing purposes",
        start_date="2025-01-01",
        end_date="2025-12-31",
        creator=user_a,
    )
    q1 = Question.objects.create(
        text="What is your favorite color?",
        question_type=Question.SINGLE_CHOICE,
        survey=survey_instance
    )
    Choice.objects.create(question=q1, text="Red")
    Choice.objects.create(question=q1, text="Blue")
    Choice.objects.create(question=q1, text="Green")
    q2 = Question.objects.create(
        text="Any additional comments?",
        question_type=Question.TEXT,
        survey=survey_instance
    )
    return survey_instance

def test_survey_creation(survey):
    assert survey.pk is not None
    assert survey.title == "Test Survey"
    assert Survey.objects.filter(title="Test Survey").exists()

def test_survey_response(client, user_b, survey):
    client.login(username=user_b.username, password='password123')
    url = reverse('survey_response', kwargs={'survey_id': survey.id})
    q1 = survey.questions.filter(question_type=Question.SINGLE_CHOICE).first()
    q1_choice = q1.choices.first()
    q2 = survey.questions.filter(question_type=Question.TEXT).first()
    data = {
        f'question_{q1.id}': str(q1_choice.id),
        f'question_{q2.id}': "No additional comments."
    }
    response = client.post(url, data)
    assert response.status_code == 302
    resp_obj = Response.objects.filter(user=user_b, survey=survey).first()
    assert resp_obj is not None
    answers = Answer.objects.filter(response=resp_obj)
    assert answers.count() == 2

def test_edit_survey_permission(client, user_a, user_b, survey):
    edit_url = reverse('edit_survey', kwargs={'pk': survey.id})
    client.login(username=user_b.username, password='password123')
    response = client.get(edit_url)
    assert response.status_code != 200
    client.logout()
    client.login(username=user_a.username, password='password123')
    response = client.get(edit_url)
    assert response.status_code == 200

def test_multiple_and_text_answers(client, user_b, survey):
    client.login(username=user_b.username, password='password123')
    url = reverse('survey_response', kwargs={'survey_id': survey.id})
    q1 = survey.questions.filter(question_type=Question.SINGLE_CHOICE).first()
    q1_choice = q1.choices.all()[1]
    q2 = survey.questions.filter(question_type=Question.TEXT).first()
    data = {
        f'question_{q1.id}': str(q1_choice.id),
        f'question_{q2.id}': "This is my text answer."
    }
    response = client.post(url, data)
    assert response.status_code == 302
    resp_obj = Response.objects.get(user=user_b, survey=survey)
    answer_text = Answer.objects.get(response=resp_obj, question=q2)
    assert answer_text.text_answer == "This is my text answer."
