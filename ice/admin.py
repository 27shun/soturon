from django.contrib import admin
from .models import IcebreakTopic, IcebreakSession, IcebreakAnswer, IcebreakPresentation
# Register your models here.
admin.site.register(IcebreakTopic)
admin.site.register(IcebreakSession)
admin.site.register(IcebreakAnswer)
admin.site.register(IcebreakPresentation)
