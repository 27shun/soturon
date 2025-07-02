from django.db import models
from django.contrib.auth.models import User
from groups.models import Group


class IcebreakTopic(models.Model):
    content = models.CharField(max_length=255)

    def __str__(self):
        return self.content

class IcebreakSession(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='icebreak_sessions')
    date = models.DateField()
    topic = models.ForeignKey(IcebreakTopic, on_delete=models.SET_NULL, null=True, blank=True)
    timer_minutes = models.IntegerField(default=3) # 回答時間など、タイマー設定（分）
    status = models.CharField(max_length=20, default='pending') # pending, active, presenting, finished
    start_time = models.DateTimeField(null=True, blank=True) 
    presentation_start_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('group', 'date') # 1グループにつき1日1セッション

    def __str__(self):
        return f"{self.group.name} - {self.date} - {self.status}"

class IcebreakAnswer(models.Model):
    session = models.ForeignKey(IcebreakSession, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    choice = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.session}"

class IcebreakPresentation(models.Model):
    session = models.ForeignKey(IcebreakSession, on_delete=models.CASCADE, related_name='presentations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    presented = models.BooleanField(default=False)
    presented_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('session', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.session} - 発表済み: {self.presented}"
