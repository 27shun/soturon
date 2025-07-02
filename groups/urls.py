from django.urls import path
from . import views

urlpatterns = [
    path('', views.group_list, name='group_list'),
    path('create/', views.group_create, name='group_create'),
    path('<int:group_id>/', views.group_detail, name='group_detail'),
    path('<int:group_id>/join/', views.join_group, name='join_group'),
    path('<int:group_id>/leave/', views.leave_group, name='leave_group'),
    path('<int:group_id>/assign_roles/', views.assign_roles, name='assign_roles'),
    path('<int:group_id>/edit_goals/', views.edit_group_goals, name='group_goals_edit'),

    path('<int:group_id>/memos/', views.group_memo_list, name='group_memo_list'),
    path('<int:group_id>/memos/create/', views.group_memo_create, name='group_memo_create'),
    path('<int:group_id>/memos/<int:pk>/', views.group_memo_detail, name='group_memo_detail'),
    path('<int:group_id>/memos/<int:pk>/update/', views.group_memo_update, name='group_memo_update'),
    path('<int:group_id>/memos/<int:pk>/delete/', views.group_memo_delete, name='group_memo_delete'),
    path('<int:group_id>/memo-settings/edit/', views.weekly_memo_settings_edit, name='weekly_memo_settings_edit'),


    path('<int:group_id>/tasks/', views.group_task_list, name='group_task_list'),
    path('<int:group_id>/tasks/create/', views.group_task_create, name='group_task_create'),
    path('<int:group_id>/tasks/<int:pk>/', views.group_task_detail, name='group_task_detail'),
    path('<int:group_id>/tasks/<int:pk>/update/', views.group_task_update, name='group_task_update'),
    path('<int:group_id>/tasks/<int:pk>/delete/', views.group_task_delete, name='group_task_delete'),
    path('<int:group_id>/tasks/<int:pk>/toggle-complete/', views.group_task_toggle_complete, name='group_task_toggle_complete'),

]
