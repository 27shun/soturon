from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, PersonalTaskForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import PersonalTask
from django.contrib.auth.decorators import login_required
from groups.models import Group
import json


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 登録後ログイン
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def home(request):
    user = request.user
    joined_groups = Group.objects.filter(members=user)  # 参加中のグループ一覧

    # 参加していないグループ一覧（任意で）
    available_groups = Group.objects.exclude(id__in=joined_groups.values_list('id', flat=True))

    return render(request, 'home.html', {
        'joined_groups': joined_groups,
        'available_groups': available_groups,
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        return redirect('login')
    return render(request, 'users/delete_account.html')

@login_required
def personal_task_list(request):
    tasks = request.user.personal_tasks.all().order_by('completed', 'due_date', 'created_at')
    
    total_tasks_count = tasks.count()
    completed_tasks_count = tasks.filter(completed=True).count()
    
    completed_percentage = 0
    if total_tasks_count > 0:
        completed_percentage = int((completed_tasks_count / total_tasks_count) * 100)

    context = {
        'tasks': tasks,
        'total_tasks_count': total_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'completed_percentage': completed_percentage,
    }
    return render(request, 'users/personal_task_list.html', context)

@login_required
def personal_task_create(request):
    if request.method == 'POST':
        form = PersonalTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, "新しいタスクを作成しました。")
            return redirect('personal_task_list')
    else:
        form = PersonalTaskForm()
    return render(request, 'users/personal_task_form.html', {'form': form, 'form_type': 'create'})

@login_required
def personal_task_detail(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, user=request.user)
    return render(request, 'users/personal_task_detail.html', {'task': task})

@login_required
def personal_task_update(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PersonalTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "タスクを更新しました。")
            return redirect('personal_task_list')
    else:
        form = PersonalTaskForm(instance=task)
    return render(request, 'users/personal_task_form.html', {'form': form, 'form_type': 'update'})

@login_required
@require_POST
def personal_task_delete(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, user=request.user)
    task.delete()
    messages.success(request, "タスクを削除しました。")
    return redirect('personal_task_list')

@login_required
@require_POST
def personal_task_toggle_complete(request, pk):
    task = get_object_or_404(PersonalTask, pk=pk, user=request.user)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            # クライアントから送られたcompletedの値でタスクの状態を設定
            task.completed = data.get('completed', not task.completed) 
        except json.JSONDecodeError:
            # JSONパースエラーの場合、元のロジック（トグル）をフォールバック
            task.completed = not task.completed
            messages.error(request, "リクエストデータの解析に失敗しました。")
    else:
        # Ajaxでない場合は元のロジック（トグル）
        task.completed = not task.completed

    task.save()
    messages.success(request, "タスクの完了ステータスを更新しました。")
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'completed': task.completed})
    return redirect('personal_task_list')