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
    template_name = 'survey/edit_survey.html'
    context_object_name = 'survey'
    form_class = SurveyForm 
    success_url = reverse_lazy('liste') 
    


class DeleteSurveyView(LoginRequiredMixin, DeleteView):
    model = Survey
    template_name = 'survey/delete_survey.html'
    context_object_name = 'survey'
    success_url = reverse_lazy('liste')


class CreateSurvey(LoginRequiredMixin,CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = "survey/survey_create.html"
    success_url = reverse_lazy('liste')


class DetailSurvey(LoginRequiredMixin, DetailView):
    model = Survey
    template_name = "survey/survey_detail.html"
    context_object_name = 'survey'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        return context

#
class QuestionCreateView(LoginRequiredMixin, View):
    template_name = 'survey/question_create.html'

    def get(self, request, *args, **kwargs):
        survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        QuestionFormSet = modelformset_factory(Question, form=QuestionForm, extra=2)
        formset = QuestionFormSet(queryset=Question.objects.none())
        return render(request, self.template_name, {
            'formset': formset,
            'survey': survey
        })

    def post(self, request, *args, **kwargs):
        survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        QuestionFormSet = modelformset_factory(Question, form=QuestionForm, extra=2)
        formset = QuestionFormSet(request.POST)

        if formset.is_valid():
            questions = formset.save(commit=False)
            
            # Parcourir toutes les données POST pour trouver les choix
            for i, question in enumerate(questions):
                question.survey = survey
                question.save()
                
                # Si la question est à choix unique ou multiple, sauvegarder les choix
                if question.question_type in [Question.SINGLE_CHOICE, Question.MULTIPLE_CHOICE]:
                    choice_index = 0
                    while True:
                        choice_key = f'form-{i}-choice-{choice_index}'
                        if choice_key not in request.POST:
                            break
                        
                        choice_text = request.POST[choice_key].strip()
                        if choice_text:  # Ne créer le choix que si le texte n'est pas vide
                            Choice.objects.create(
                                question=question,
                                text=choice_text
                            )
                        choice_index += 1

            return redirect(reverse_lazy('survey_detail', kwargs={'pk': survey.id}))
            
        return render(request, self.template_name, {
            'formset': formset,
            'survey': survey
        })


class SurveyResponseView(LoginRequiredMixin, View):
    template_name = 'survey/survey_response.html'

    def get(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        
        # Vérifier si le sondage est actif
        if not survey.is_active():
            messages.error(request, "Ce sondage n'est pas actif actuellement.")
            return redirect('liste')
        
        # Vérifier si l'utilisateur a déjà répondu
        existing_response = Response.objects.filter(
            user=request.user,
            survey=survey
        ).first()
        
        if existing_response:
            messages.info(request, "Vous avez déjà répondu à ce sondage.")
            return redirect('liste')

        context = {
            'survey': survey,
            'questions': survey.questions.all().prefetch_related('choices')
        }
        return render(request, self.template_name, context)

    def post(self, request, survey_id):
        survey = get_object_or_404(Survey, pk=survey_id)
        
        # Vérifications de sécurité
        if not survey.is_active():
            messages.error(request, "Ce sondage n'est pas actif actuellement.")
            return redirect('liste')
            
        if Response.objects.filter(user=request.user, survey=survey).exists():
            messages.error(request, "Vous avez déjà répondu à ce sondage.")
            return redirect('liste')

        try:
            # Créer une nouvelle réponse
            response = Response.objects.create(
                user=request.user,
                survey=survey
            )

            # Traiter chaque question
            for question in survey.questions.all():
                if question.question_type == 'text':
                    answer_text = request.POST.get(f'question_{question.id}')
                    if not answer_text:
                        raise ValueError(f"La question '{question.text}' nécessite une réponse.")
                    
                    Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=answer_text
                    )
                
                elif question.question_type == 'single_choice':
                    choice_id = request.POST.get(f'question_{question.id}')
                    if not choice_id:
                        raise ValueError(f"La question '{question.text}' nécessite une réponse.")
                    
                    choice = Choice.objects.get(pk=choice_id, question=question)
                    Answer.objects.create(
                        response=response,
                        question=question,
                        choice=choice
                    )
                
                elif question.question_type == 'multiple_choice':
                    choice_ids = request.POST.getlist(f'question_{question.id}')
                    if not choice_ids:
                        raise ValueError(f"La question '{question.text}' nécessite au moins une réponse.")
                    
                    for choice_id in choice_ids:
                        choice = Choice.objects.get(pk=choice_id, question=question)
                        Answer.objects.create(
                            response=response,
                            question=question,
                            choice=choice
                        )

            messages.success(request, "Merci d'avoir répondu au sondage!")
            return redirect('liste')

        except (ValueError, Choice.DoesNotExist) as e:
            # En cas d'erreur, supprimer la réponse et afficher l'erreur
            if 'response' in locals():
                response.delete()
            messages.error(request, str(e))
            return render(request, self.template_name, {
                'survey': survey,
                'questions': survey.questions.all().prefetch_related('choices')
            })


class SurveyResponsesListView(LoginRequiredMixin, ListView):
    model = Response
    template_name = 'survey/responses_list.html'
    context_object_name = 'responses'
    

    def get_queryset(self):
        self.survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        return Response.objects.filter(survey=self.survey).select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        # Calculer quelques statistiques
        context['total_responses'] = self.get_queryset().count()
        context['questions'] = self.survey.questions.all()
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