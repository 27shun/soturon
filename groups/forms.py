# myapp/groups/forms.py

from django import forms
from .models import Group, GroupMemberRole, Role, FinalGoal, WeeklyGoal, GroupTask, PersonalEvent, WeeklyMemoSettings
from .models import GroupMemo
from django.utils import timezone 

class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description']
        labels = {
            'name': 'グループ名',
            'description': 'グループの説明',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AssignRolesForm(forms.ModelForm): 
    class Meta:
        model = GroupMemberRole
        fields = ['role'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'role' in self.fields:
            self.fields['role'].empty_label = '（役割なし）' 
            self.fields['role'].required = False 

class FinalGoalForm(forms.ModelForm):
    class Meta:
        model = FinalGoal
        fields = ['title', 'description'] 
        labels = {
            'title': '最終目標タイトル',
            'description': '最終目標の内容',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class WeeklyGoalForm(forms.ModelForm):
    class Meta:
        model = WeeklyGoal
        fields = ['title',]
        labels = {
            'title': '週間目標タイトル',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }

class GroupGoalForm(forms.Form):
    # FinalGoalの項目
    final_goal_title = forms.CharField(
        label="最終目標",
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # WeeklyGoalの項目
    target_date_for_weekly_goal = forms.DateField(
        label="目標を設定する週の日付",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.localdate
    )
    weekly_goal_title = forms.CharField(
        label="週間目標",
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )

class GroupMemoForm(forms.ModelForm):
    class Meta:
        model = GroupMemo
        fields = [
            'weekly_goal', 
            'talking_points', 
            'reasons_background', 
            'examples_episodes'
        ] 
        labels = {
            'weekly_goal': '関連する週間目標',
            'talking_points': '話すポイント(結論)',
            'reasons_background': '理由・背景',
            'examples_episodes': '具体例・エピソード',
        }
        widgets = {
            'weekly_goal': forms.Select(attrs={'class': 'form-select'}), # クラス指定済み
            'talking_points': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), # クラス指定済み
            'reasons_background': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}), # クラス指定済み
            'examples_episodes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}), # クラス指定済み
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['weekly_goal'].label_from_instance = self._weekly_goal_label_from_instance
        self.fields['weekly_goal'].empty_label = '（週間目標を選択しない）'
        self.fields['weekly_goal'].required = False

    def _weekly_goal_label_from_instance(self, obj):
        return f"{obj.title} ({obj.week_start_date.strftime('%Y/%m/%d')}〜) - {obj.description[:50]}..."
    
class WeeklyMemoSettingsForm(forms.ModelForm):
    class Meta:
        model = WeeklyMemoSettings
        fields = ['is_required_this_week'] # groupとweek_start_dateはビューで設定
        labels = {
            'is_required_this_week': '今週のメモを必須にする',
        }
        widgets = {
            'is_required_this_week': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GroupTaskForm(forms.ModelForm):
    class Meta:
        model = GroupTask
        fields = ['title', 'description', 'assigned_to', 'due_date', 'completed']
        labels = {
            'title': 'タスク名',
            'description': 'タスクの詳細',
            'assigned_to': '担当者',
            'due_date': '期限',
            'completed': '完了済み',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None) 
        super().__init__(*args, **kwargs)
        if group:
            # 担当者の選択肢をそのグループのメンバーに限定
            self.fields['assigned_to'].queryset = group.members.all().order_by('username')
            # 担当者がいない場合も考慮し、空の選択肢を追加
            self.fields['assigned_to'].empty_label = "担当者なし"
            self.fields['assigned_to'].required = False 

class PersonalEventForm(forms.ModelForm):
    class Meta:
        model = PersonalEvent
        fields = ['title', 'description', 'start_time', 'end_time', 'is_all_day']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'is_all_day': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        is_all_day = cleaned_data.get('is_all_day')

        if not is_all_day and start_time and end_time and end_time < start_time:
            self.add_error('end_time', '終了日時は開始日時より後に設定してください。')

        return cleaned_data
