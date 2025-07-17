from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PersonalTask, PersonalEvent

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class PersonalTaskForm(forms.ModelForm):
    class Meta:
        model = PersonalTask
        fields = ['title', 'description', 'due_date', 'completed']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}), # HTML5 date input
        }

class PersonalEventForm(forms.ModelForm):
    """ユーザー個人の予定フォーム"""
    class Meta:
        model  = PersonalEvent
        fields = ['title', 'description', 'start_time', 'end_time', 'is_all_day']
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_time':  forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time':    forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'is_all_day':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title':       '予定名',
            'description': '詳細',
            'start_time':  '開始日時',
            'end_time':    '終了日時',
            'is_all_day':  '終日',
        }

    def clean(self):
        """終日チェック時のバリデーション"""
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end   = cleaned.get('end_time')
        all_day = cleaned.get('is_all_day')

        if not all_day:
            # 通常予定 → 終了時刻は開始より後
            if start and end and end < start:
                self.add_error('end_time', '終了日時は開始日時より後にしてください。')
        else:
            # 終日予定 → 終了時刻を空欄にする運用
            cleaned['end_time'] = None
        return cleaned