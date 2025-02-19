from django.db import models
from users.models import User
from django.forms import ValidationError


class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveys')
    
    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("la date de creation doit etre inferieur a la date de d'expiration")
        return super().clean()

    def __str__(self):
        return self.title

    def is_active(self):
        from datetime import date
        return self.start_date <= date.today() <= self.end_date


class Question(models.Model):
    TEXT = 'text'
    SINGLE_CHOICE = 'single_choice'
    MULTIPLE_CHOICE = 'multiple_choice'

    QUESTION_TYPES = [
        (TEXT, 'Réponse texte'),
        (SINGLE_CHOICE, 'Réponse unique (choix multiple)'),
        (MULTIPLE_CHOICE, 'Réponse multiple (cases à cocher)')
    ]

    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return self.text

class Choice(models.Model): 
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text



class Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responses')
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Response by {self.user} for {self.survey}"

    class Meta:
        unique_together = ('user', 'survey')

class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True) 
    text_answer = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Answer to {self.question}"

    def save(self, *args, **kwargs):
        if self.question.question_type == Question.TEXT and self.text_answer == "":
            raise ValueError("Une réponse texte est nécessaire pour cette question.")
        elif self.question.question_type != Question.TEXT and not self.choice:
            raise ValueError("Un choix doit être sélectionné pour cette question.")
        super().save(*args, **kwargs)
