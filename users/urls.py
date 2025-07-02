from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # 新規登録・削除用ビュー

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('', views.home, name='home'),  

    path('tasks/', views.personal_task_list, name='personal_task_list'),
    path('tasks/create/', views.personal_task_create, name='personal_task_create'),
    path('tasks/<int:pk>/', views.personal_task_detail, name='personal_task_detail'),
    path('tasks/<int:pk>/update/', views.personal_task_update, name='personal_task_update'),
    path('tasks/<int:pk>/delete/', views.personal_task_delete, name='personal_task_delete'),
    path('tasks/<int:pk>/toggle-complete/', views.personal_task_toggle_complete, name='personal_task_toggle_complete'),
]
