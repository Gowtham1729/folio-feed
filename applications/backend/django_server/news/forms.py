from django import forms


class InputForm(forms.Form):
    user_input = forms.CharField(label="Enter your text", max_length=100)
