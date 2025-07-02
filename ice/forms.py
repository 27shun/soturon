from django import forms
from .models import IcebreakAnswer

class SessionStartForm(forms.Form):
    timer = forms.ChoiceField(
        choices=[(i, f"{i}分") for i in range(1, 6)],
        label="タイマー（分）",
        initial=3
    )

class IcebreakAnswerForm(forms.ModelForm):
    class Meta:
        model = IcebreakAnswer
        fields = ['choice', 'text']
        widgets = {
            'choice': forms.TextInput(attrs={'placeholder': '選択肢を入力'}),
            'text': forms.Textarea(attrs={'placeholder': '自由記述'}),
        }
        labels = {
            'choice': '選択肢',
            'text': '自由記述',
        }