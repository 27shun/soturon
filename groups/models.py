from django.db import models
from django.conf import settings 
from django.utils import timezone 
from django.contrib.auth.models import User

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User


class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='joined_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Role(models.Model):
    name = models.CharField(max_length=50) 
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class GroupMemberRole(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user') 

    def __str__(self):
        return f"{self.user.username} - {self.role.name} in {self.group.name}"

class FinalGoal(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='final_goal')
    title = models.CharField(max_length=200) 
    description = models.TextField(blank=True) 

    def __str__(self):
        return f"{self.group.name} の最終目標: {self.title}"

# ★ここが最終的な WeeklyGoal モデルの定義です。week_end は削除されます。
class WeeklyGoal(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='weekly_goals')
    week_start_date = models.DateField(default=timezone.localdate) # 週の開始日のみ
    title = models.CharField(max_length=200) 
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('group', 'week_start_date')
        ordering = ['-week_start_date']

    def __str__(self):
        # ★__str__ メソッドも week_start_date のみを使うように修正
        return f"{self.group.name} {self.week_start_date}週の目標: {self.title}"


class GroupMemo(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_memos')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_group_memos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # メモが紐づく週の開始日（週次メモであることを示す）
    week_start_date = models.DateField(verbose_name='対象週の開始日') 
    
    # 関連する週間目標（OptionalなForeignKey）
    weekly_goal = models.ForeignKey(WeeklyGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name='memos', verbose_name='関連する週間目標') # ★このフィールドを確認

    # グループワーク前の思考整理項目（ユーザー要望に合わせて再定義）
    talking_points = models.TextField(verbose_name='話すポイント(結論)', help_text='グループワークで伝えたい、一番重要な結論や要点', default='')
    reasons_background = models.TextField(verbose_name='理由・背景', help_text='その結論に至った理由や、背景にある情報、データなど', blank=True)
    examples_episodes = models.TextField(verbose_name='具体例・エピソード', help_text='話を裏付ける具体的な例や体験談', blank=True)

    class Meta:
        unique_together = ('group', 'created_by', 'week_start_date') 
        ordering = ['-week_start_date', 'created_by__username'] 

    def __str__(self):
        if self.weekly_goal:
            return f"メモ ({self.group.name} / {self.weekly_goal.title}): {self.talking_points[:30]}..."
        return f"メモ ({self.group.name}): {self.talking_points[:30]}..." 


# WeeklyMemoSettingsモデルの定義（既存）
class WeeklyMemoSettings(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='weekly_memo_settings')
    week_start_date = models.DateField(verbose_name='週の開始日')
    is_required_this_week = models.BooleanField(default=True, verbose_name='今週のメモは必須か？')

    class Meta:
        unique_together = ('group', 'week_start_date')
        ordering = ['-week_start_date']
        verbose_name = '週次メモ設定'
        verbose_name_plural = '週次メモ設定'

    def __str__(self):
        status = "必須" if self.is_required_this_week else "任意"
        return f"{self.group.name} - {self.week_start_date}週のメモ: {status}"
    

class GroupTask(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_tasks')
    title = models.CharField(max_length=255, verbose_name='タスク名')
    description = models.TextField(blank=True, verbose_name='詳細', help_text='タスクの具体的な内容や手順')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_group_tasks', verbose_name='担当者')
    due_date = models.DateField(null=True, blank=True, verbose_name='期限')
    completed = models.BooleanField(default=False, verbose_name='完了済み')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_group_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['completed', 'due_date', '-created_at'] # 未完了優先、期限が近い順、新しい順

    def __str__(self):
        return f"[{'完了' if self.completed else '未完了'}] {self.title} ({self.group.name})"
    
class PersonalEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='予定名')
    description = models.TextField(blank=True, verbose_name='詳細')
    start_time = models.DateTimeField(verbose_name='開始日時')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='終了日時', help_text='終日の予定の場合は空欄にしてください')
    is_all_day = models.BooleanField(default=False, verbose_name='終日')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = '個人予定'
        verbose_name_plural = '個人予定'

    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        # 終日設定の場合、開始時刻と終了時刻を日付のみにする（任意）
        if self.is_all_day:
            self.start_time = timezone.make_aware(timezone.datetime(self.start_time.year, self.start_time.month, self.start_time.day))
            self.end_time = None # 終日の場合は終了時刻をクリア
        super().save(*args, **kwargs)