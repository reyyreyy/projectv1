from django import forms

class ExerciseRequestForm(forms.Form):
    topic = forms.CharField(label="Chemistry Topic", max_length=100)
