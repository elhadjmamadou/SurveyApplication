from django.urls import path
from .views import (
    ListView, EditSurveyView, DeleteSurveyView, CreateSurvey, DetailSurvey, 
    QuestionCreateView, SurveyResponseView, 
    SurveyResponsesListView, SurveyResponseDetailView
    )

urlpatterns = [
    path('', ListView.as_view(), name='liste'),
    path('survey/create/', CreateSurvey.as_view(), name='create_survey'),
    path('survey/<int:pk>/', DetailSurvey.as_view(), name='detail'),
    path('survey/<int:pk>/edit/', EditSurveyView.as_view(), name='edit_survey'),
    path('survey/<int:pk>/delete/', DeleteSurveyView.as_view(), name='delete_survey'),
    path('survey/<int:survey_id>/question/create/', QuestionCreateView.as_view(), name='create_question'),
    path('survey/<int:survey_id>/respond/', SurveyResponseView.as_view(), name='survey_respond'),
    path('survey/<int:survey_id>/responses/', SurveyResponsesListView.as_view(), name='survey_responses'),
    path('response/<int:pk>/', SurveyResponseDetailView.as_view(), name='response_detail'),
]
