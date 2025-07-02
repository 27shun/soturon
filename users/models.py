from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    profile_icon = models.ImageField(upload_to='profile_icons/', blank=True, null=True)
    faculty_department = models.CharField(max_length=100, blank=True, null=True, verbose_name="所属学部・学科")
    current_seminar = models.CharField(max_length=100, blank=True, null=True, verbose_name="所属ゼミ")

    def __str__(self):
        return self.user.username

class PersonalTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        return f"{self.user.username}'s Task: {self.title}"