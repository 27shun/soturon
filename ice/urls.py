from django.urls import path
from . import views

urlpatterns = [
    path('session_start/<int:group_id>/', views.session_start, name='session_start'),
    path('answer/<int:session_id>/', views.answer, name='answer'),
    path('wait/<int:session_id>/', views.wait, name='wait'),
    path('present/<int:session_id>/', views.present, name='present'),
    path('status/<int:session_id>/', views.get_session_status, name='get_session_status'),
]