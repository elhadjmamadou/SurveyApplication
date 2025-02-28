from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.generic import ListView, UpdateView, DeleteView, CreateView, DetailView
from .models import *
from django.views.generic import View
from django.urls import reverse_lazy
from .forms import SurveyForm, QuestionForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.forms import modelformset_factory
from django.contrib import messages
from datetime import date


class ListView(ListView):
    model = Survey
    template_name = "survey/liste.html"
    context_object_name = "surveys"


class EditSurveyView(LoginRequiredMixin,UpdateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'survey/edit_survey.html'
    success_url = reverse_lazy('liste')


class DeleteSurveyView(LoginRequiredMixin,DeleteView):
    model = Survey
    template_name = 'survey/delete_survey.html'
    context_object_name = 'survey'
    success_url = reverse_lazy('liste')


class CreateSurvey(LoginRequiredMixin,CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = "survey/survey_create.html"
    success_url = reverse_lazy('liste')


class DetailSurvey(DetailView):
    model = Survey
    template_name = "survey/survey_detail.html"
    context_object_name = 'survey'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = Question.objects.filter(survey=self.object)
        return context


class QuestionCreateView(LoginRequiredMixin, View):
    template_name = 'survey/question_create.html'

    def get(self, request, *args, **kwargs):
        survey_id = kwargs.get('survey_id')
        survey = get_object_or_404(Survey, id=survey_id)
        
        # Vérifier si l'utilisateur est le créateur du sondage
        if survey.creator != request.user:
            messages.error(request, "Vous n'avez pas l'autorisation de modifier ce sondage.")
            return redirect('liste')
        
        form = QuestionForm()
        context = {
            'form': form,
            'survey': survey,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        survey_id = kwargs.get('survey_id')
        survey = get_object_or_404(Survey, id=survey_id)
        
        # Vérifier si l'utilisateur est le créateur du sondage
        if survey.creator != request.user:
            messages.error(request, "Vous n'avez pas l'autorisation de modifier ce sondage.")
            return redirect('liste')
        
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.survey = survey
            question.save()
            
            # Traiter les choix si c'est une question à choix
            if question.question_type in ['single_choice', 'multiple_choice']:
                choices_text = request.POST.getlist('choices')
                for choice_text in choices_text:
                    if choice_text.strip():  # Ne pas créer de choix vides
                        Choice.objects.create(question=question, text=choice_text.strip())
            
            messages.success(request, "Question ajoutée avec succès!")
            return redirect('detail', pk=survey_id)
        
        context = {
            'form': form,
            'survey': survey,
        }
        return render(request, self.template_name, context)


class SurveyResponseView(View):
    template_name = 'survey/survey_response.html'
    
    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        questions = Question.objects.filter(survey=survey).prefetch_related('choices')
        
        # Vérifier si le sondage a des questions
        if not questions.exists():
            messages.warning(request, "Ce sondage ne contient aucune question.")
        
        context = {
            'survey': survey,
            'questions': questions,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        questions = Question.objects.filter(survey=survey).prefetch_related('choices')
        
        # Créer une nouvelle réponse
        response = Response.objects.create(
            survey=survey,
            respondent=request.user if request.user.is_authenticated else None
        )
        
        # Traiter chaque question
        for question in questions:
            if question.question_type == 'text':
                # Traiter les réponses textuelles
                text_answer = request.POST.get(f'question_{question.id}', '').strip()
                if text_answer:
                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=text_answer
                    )
            
            elif question.question_type == 'single_choice':
                # Traiter les réponses à choix unique
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    try:
                        choice = Choice.objects.get(id=choice_id, question=question)
                        Answer.objects.create(
                            response=response,
                            question=question,
                            choice=choice
                        )
                    except Choice.DoesNotExist:
                        pass
            
            elif question.question_type == 'multiple_choice':
                # Traiter les réponses à choix multiples
                choice_ids = request.POST.getlist(f'question_{question.id}')
                for choice_id in choice_ids:
                    try:
                        choice = Choice.objects.get(id=choice_id, question=question)
                        Answer.objects.create(
                            response=response,
                            question=question,
                            choice=choice
                        )
                    except Choice.DoesNotExist:
                        pass
        
        messages.success(request, "Merci pour votre réponse au sondage!")
        return redirect('liste')


class SurveyResponsesListView(LoginRequiredMixin, ListView):
    model = Response
    template_name = 'survey/responses_list.html'
    context_object_name = 'responses'
    
    def get_queryset(self):
        survey_id = self.kwargs.get('survey_id')
        survey = get_object_or_404(Survey, pk=survey_id)
        
        # Vérifier que l'utilisateur est le créateur du sondage
        if survey.creator != self.request.user:
            return Response.objects.none()
        
        return Response.objects.filter(survey=survey).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey_id = self.kwargs.get('survey_id')
        context['survey'] = get_object_or_404(Survey, pk=survey_id)
        return context


class SurveyResponseDetailView(LoginRequiredMixin, DetailView):
    template_name = 'survey/response_detail.html'
    context_object_name = 'response'
    model = Response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Organiser les réponses par question
        answers = self.object.answers.select_related('question', 'choice')
        answers_by_question = {}
        
        for answer in answers:
            if answer.question not in answers_by_question:
                answers_by_question[answer.question] = []
            answers_by_question[answer.question].append(answer)

        context['answers_by_question'] = answers_by_question
        return context