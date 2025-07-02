from django.contrib import admin
from .models import Group,Role, GroupMemberRole,FinalGoal, WeeklyGoal

admin.site.register(Group)
admin.site.register(Role)
admin.site.register(GroupMemberRole)
admin.site.register(FinalGoal)
admin.site.register(WeeklyGoal)

# Register your models here.
