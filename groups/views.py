from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages # messagesをインポート
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone 
import json
from .models import Group, Role, GroupMemberRole, FinalGoal, WeeklyGoal, GroupMemo, GroupTask, PersonalEvent, WeeklyMemoSettings
from .forms import GroupCreateForm, AssignRolesForm,FinalGoalForm,WeeklyGoalForm, GroupGoalForm, GroupMemoForm, GroupTaskForm, PersonalEventForm, WeeklyMemoSettingsForm
from django.forms import modelformset_factory 


def is_group_member(user, group):
    """ユーザーがグループのメンバーであるかを確認するヘルパー関数"""
    return user in group.members.all()


@login_required
def group_list(request):
    query = request.GET.get('q')
    user_groups = request.user.joined_groups.all()

    if query:
        joined_groups_filtered = user_groups.filter(Q(name__icontains=query) | Q(description__icontains=query)).distinct()
        available_groups_filtered = Group.objects.exclude(members=request.user).filter(Q(name__icontains=query) | Q(description__icontains=query)).distinct()
    else:
        joined_groups_filtered = user_groups
        available_groups_filtered = Group.objects.exclude(members=request.user)

    context = {
        'joined_groups': joined_groups_filtered,
        'available_groups': available_groups_filtered,
        'query': query,
    }
    return render(request, 'groups/group_list.html', context)

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not is_group_member(request.user, group):
        messages.error(request, 'このグループには参加していません。') 
        return redirect('group_list')

    # 今週の月曜日を取得 (メモの割り当て判定用)
    today = timezone.localdate()
    this_monday = today - timezone.timedelta(days=today.weekday())

    members_with_roles = []
    for member in group.members.all():
        membership = GroupMemberRole.objects.filter(user=member, group=group).first()
        role_name = membership.role.name if membership and membership.role else '役職なし' 
        
        # 各メンバーのタスク進捗を計算 (既存機能)
        member_tasks = GroupTask.objects.filter(group=group, assigned_to=member)
        total_member_tasks = member_tasks.count()
        completed_member_tasks = member_tasks.filter(completed=True).count()
        
        member_task_progress_percentage = 0
        if total_member_tasks > 0:
            member_task_progress_percentage = int((completed_member_tasks / total_member_tasks) * 100)

        # 各メンバーの今週のグループメモ完了状況 (GroupMemoの存在で判定)
        is_memo_completed_this_week = GroupMemo.objects.filter(
            group=group,
            created_by=member, # そのメンバーが作成したメモ
            week_start_date=this_monday # 今週のメモ
        ).exists()

        members_with_roles.append({
            'user': member,
            'username': member.username,
            'role': role_name,
            'total_tasks': total_member_tasks, 
            'completed_tasks': completed_member_tasks, 
            'progress_percentage': member_task_progress_percentage, 
            'is_memo_completed_this_week': is_memo_completed_this_week, 
        })

    final_goal = FinalGoal.objects.filter(group=group).first()
    weekly_goals = WeeklyGoal.objects.filter(group=group).order_by('-week_start_date') 

    group_memos = GroupMemo.objects.filter(group=group).order_by('-created_at')
    group_tasks = GroupTask.objects.filter(group=group).order_by('completed', 'due_date', '-created_at') 

    # ★ここが重要: 現在のユーザーの今週のメモに関する情報を取得
    current_user_memo_this_week = GroupMemo.objects.filter(
        group=group,
        created_by=request.user,
        week_start_date=this_monday
    ).first()

    context = {
        'group': group,
        'members_with_roles': members_with_roles,
        'final_goal': final_goal,
        'weekly_goals': weekly_goals,
        'group_memos': group_memos, # これは全メモ一覧用
        'group_tasks': group_tasks, 
        'current_user_memo_this_week': current_user_memo_this_week, # ★テンプレートに渡す
        'this_monday': this_monday, # テンプレートで週の開始日を表示するため
    }
    return render(request, 'groups/group_detail.html', context)

@login_required
def group_create(request):
    if request.method == 'POST':
        form = GroupCreateForm(request.POST) 
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            group.members.add(request.user)
            messages.success(request, f'グループ "{group.name}" を作成しました。') 
            return redirect('group_detail', group_id=group.id)
        else:
            messages.error(request, f'グループ作成に失敗しました。入力内容を確認してください。') 
    else:
        form = GroupCreateForm() 
    return render(request, 'groups/group_form.html', {'form': form, 'form_type': 'create'})

@login_required
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all(): 
        group.members.add(request.user)
        messages.success(request, f'グループ "{group.name}" に参加しました。') 
    else:
        messages.info(request, f'あなたは既にグループ "{group.name}" に参加しています。') 
    return redirect('group_detail', group_id=group.id)

@login_required
def leave_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user in group.members.all():
        group.members.remove(request.user)
        messages.success(request, f'グループ "{group.name}" を脱退しました。')
    else:
        messages.info(request, f'あなたはグループ "{group.name}" に参加していません。') 
    return redirect('group_list')

@login_required
def assign_roles(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user != group.created_by:
        messages.error(request, f'役職を割り当てる権限がありません。') 
        return redirect('group_detail', group_id=group.id)

    from django.forms import modelformset_factory 

    AssignRolesFormSet = modelformset_factory(
        GroupMemberRole,
        form=AssignRolesForm, 
        fields=('role',), 
        extra=0,
        can_delete=False
    )
    
    for member in group.members.all():
        GroupMemberRole.objects.get_or_create(group=group, user=member) 

    if request.method == 'POST':
        formset = AssignRolesFormSet(request.POST, queryset=GroupMemberRole.objects.filter(group=group))
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                original = GroupMemberRole.objects.get(id=instance.id)
                instance.user = original.user
                instance.group = original.group
                instance.save()
            messages.success(request, '役職の割り当てを更新しました。')
            return redirect('group_detail', group_id=group.id)
        else:
            print("フォームセット（非フォーム）エラー:", formset.non_form_errors())
            print("フォームセットのエラー:", formset.errors)
            messages.error(request, '役職の割り当てに失敗しました。')
    else:
        formset = AssignRolesFormSet(queryset=GroupMemberRole.objects.filter(group=group))

    context = {
        'group': group,
        'formset': formset,
        'roles': Role.objects.all(), 
        'group_members': group.members.all(), 
    }
    return render(request, 'groups/assign_roles.html', context)

@login_required
def edit_group_goals(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループの目標を編集する権限がありません。') 
        return redirect('group_list')

    final_goal, created_fg = FinalGoal.objects.get_or_create(group=group)
    
    today = timezone.localdate()
    this_monday = today - timezone.timedelta(days=today.weekday())

    # 今週の週間目標インスタンスをGET時とPOST時両方で初期データのために取得
    current_week_goal_instance, _ = WeeklyGoal.objects.get_or_create(
        group=group, 
        week_start_date=this_monday # 今週の目標を基準として取得
    )


    if request.method == 'POST':
        form = GroupGoalForm(request.POST) # GroupGoalFormはFinalGoalとWeeklyGoalの項目を統合したフォーム

        if form.is_valid():
            # 最終目標の保存
            final_goal.title = form.cleaned_data['final_goal_title'] 
            final_goal.description = form.cleaned_data['final_goal_description']
            final_goal.save()

            # 週間目標の保存
            target_date = form.cleaned_data['target_date_for_weekly_goal'] # フォームからユーザーが入力した日付を取得
            # その日付を含む週の月曜日を計算
            target_week_start_date = target_date - timezone.timedelta(days=target_date.weekday())
            
            # 計算された週の週間目標を取得または作成
            weekly_goal_to_save, created_wg = WeeklyGoal.objects.get_or_create(
                group=group,
                week_start_date=target_week_start_date 
            )
            
            # そのインスタンスのタイトルと内容をフォームデータで更新
            weekly_goal_to_save.title = form.cleaned_data['weekly_goal_title'] 
            weekly_goal_to_save.description = form.cleaned_data['weekly_goal_description']
            weekly_goal_to_save.save()

            messages.success(request, f'グループ目標を更新しました。')
            return redirect('group_detail', group_id=group.id)
        else:
            messages.error(request, f'グループ目標の更新に失敗しました。入力内容を確認してください。')
    else:
        # GETリクエスト時、フォームの初期データを設定
        form = GroupGoalForm(initial={ 
            'final_goal_title': final_goal.title, 
            'final_goal_description': final_goal.description,
            'weekly_goal_title': current_week_goal_instance.title, 
            'weekly_goal_description': current_week_goal_instance.description, 
            'target_date_for_weekly_goal': timezone.localdate() # デフォルトで今日の日付をセット
        })

    # 過去の週間目標を取得 (これはUI表示用)
    weekly_goals_past = WeeklyGoal.objects.filter(group=group).order_by('-week_start_date') 

    context = {
        'group': group,
        'form': form, # 統合フォーム
        'final_goal': final_goal, # テンプレートの表示用
        'weekly_goals': weekly_goals_past, # 過去の週間目標リスト
        'current_weekly_goal_instance': current_week_goal_instance, # 今週の目標インスタンスをテンプレートに渡す
    }
    return render(request, 'groups/group_goals_edit.html', context)

@login_required
def group_memo_list(request, group_id): # group_id を直接引数で受け取る
    group = get_object_or_404(Group, id=group_id) 
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのメモを閲覧する権限がありません。') 
        return redirect('group_list')

    memos_by_current_user = GroupMemo.objects.filter(
        group=group,
        created_by=request.user # 現在のユーザーが作成したメモのみに絞る
    ).order_by('-week_start_date', '-created_at') # 週の開始日と作成日時で並び替え
    
    context = {
        'group': group,
        'memos': memos_by_current_user, # コンテキスト変数名をmemosに変更
    }
    return render(request, 'groups/group_memo_list.html', context)

@login_required
def group_memo_create(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループにメモを作成する権限がありません。') 
        return redirect('group_list')

    today = timezone.localdate()
    this_monday = today - timezone.timedelta(days=today.weekday())
    
    # 今週すでにメモを作成しているかチェック
    existing_memo_this_week = GroupMemo.objects.filter(
        group=group,
        created_by=request.user,
        week_start_date=this_monday
    ).first()

    if existing_memo_this_week:
        # 既に今週のメモを作成済みであれば、編集画面にリダイレクト
        messages.info(request, "今週のメモは既に作成済みです。編集画面に移動します。")
        return redirect('group_memo_update', group_id=group.id, pk=existing_memo_this_week.pk)

    if request.method == 'POST':
        form = GroupMemoForm(request.POST)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.group = group
            memo.created_by = request.user
            memo.week_start_date = this_monday # 週の開始日を自動設定
            memo.save()
            messages.success(request, f'新しいメモを作成しました。') 
            return redirect('group_memo_list', group_id=group.id)
        else:
            messages.error(request, f'メモ作成に失敗しました。入力内容を確認してください。') 
    else:
        form = GroupMemoForm() 
    
    current_weekly_goal = WeeklyGoal.objects.filter(group=group, week_start_date=this_monday).first()

    context = {
        'group': group,
        'form': form, 
        'form_type': 'create',
        'current_weekly_goal': current_weekly_goal, # テンプレートに表示するため
    }
    return render(request, 'groups/group_memo_form.html', context)


@login_required
def group_memo_detail(request, group_id, pk):
    group = get_object_or_404(Group, id=group_id)
    memo = get_object_or_404(GroupMemo, pk=pk, group=group)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのメモを閲覧する権限がありません。') 
        return redirect('group_list')

    context = {
        'group': group,
        'memo': memo,
    }
    return render(request, 'groups/group_memo_detail.html', context)


@login_required
def group_memo_update(request, group_id, pk):
    group = get_object_or_404(Group, id=group_id)
    memo = get_object_or_404(GroupMemo, pk=pk, group=group)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのメモを編集する権限がありません。')
        return redirect('group_list')
    if request.user != memo.created_by: 
        messages.error(request, f'このメモを編集する権限がありません。') 
        return redirect('group_memo_detail', group_id=group.id, pk=memo.id)

    today = timezone.localdate()
    this_monday = today - timezone.timedelta(days=today.weekday())
    current_weekly_goal, created_goal = WeeklyGoal.objects.get_or_create(
        group=group,
        week_start_date=this_monday
    )

    if request.method == 'POST':
        form = GroupMemoForm(request.POST, instance=memo)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.week_start_date = this_monday # 週の開始日を自動設定
            memo.save()
            messages.success(request, f'メモを更新しました。') 
            return redirect('group_memo_list', group_id=group.id)
        else:
            messages.error(request, f'メモ更新に失敗しました。入力内容を確認してください。') 
    else:
        form = GroupMemoForm(instance=memo)
    
    current_weekly_goal = WeeklyGoal.objects.filter(group=group, week_start_date=this_monday).first() # テンプレート表示用

    context = {
        'group': group,
        'form': form, 
        'form_type': 'update',
        'current_weekly_goal': current_weekly_goal, # テンプレートに表示するため
    }
    return render(request, 'groups/group_memo_form.html', context)


@login_required
@require_POST
def group_memo_delete(request, group_id, pk):
    group = get_object_or_404(Group, id=group_id)
    memo = get_object_or_404(GroupMemo, pk=pk, group=group)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのメモを削除する権限がありません。') 
        return redirect('group_list')
    if request.user != memo.created_by: 
        messages.error(request, f'このメモを削除する権限がありません。') 
        return redirect('group_memo_detail', group_id=group.id, pk=memo.id)
    
    memo.delete()
    messages.success(request, f'メモを削除しました。') 
    return redirect('group_memo_list', group_id=group.id)


@login_required
@require_POST
def weekly_memo_settings_edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user != group.created_by:
        messages.error(request, "この設定を変更する権限がありません。")
        return redirect('group_detail', group_id=group.id)

    today = timezone.localdate()
    this_monday = today - timezone.timedelta(days=today.weekday())

    settings_instance, created = WeeklyMemoSettings.objects.get_or_create(
        group=group,
        week_start_date=this_monday,
        defaults={'is_required_this_week': True} 
    )

    if request.method == 'POST':
        form = WeeklyMemoSettingsForm(request.POST, instance=settings_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{this_monday}週のメモ設定を更新しました。")
            return redirect('group_detail', group_id=group.id)
        else:
            messages.error(request, "メモ設定の更新に失敗しました。入力内容を確認してください。")
    else:
        form = WeeklyMemoSettingsForm(instance=settings_instance)
    
    context = {
        'group': group,
        'form': form,
        'current_week_start_date': this_monday,
    }
    return render(request, 'groups/weekly_memo_settings_form.html', context)

@login_required
def group_task_list(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not is_group_member(request.user, group):
        messages.error(f'このグループのタスクを閲覧する権限がありません。')
        return redirect('group_list')

    tasks = GroupTask.objects.filter(group=group).order_by('completed', 'due_date', '-created_at')

    total_tasks_count = tasks.count()
    completed_tasks_count = tasks.filter(completed=True).count()
    
    completed_percentage = 0
    if total_tasks_count > 0:
        completed_percentage = int((completed_tasks_count / total_tasks_count) * 100)

    context = {
        'group': group,
        'tasks': tasks,
        'total_tasks_count': total_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'completed_percentage': completed_percentage,
    }
    return render(request, 'groups/group_task_list.html', context)


@login_required
def group_task_list(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのタスクを閲覧する権限がありません。')
        return redirect('group_list')

    tasks = GroupTask.objects.filter(group=group).order_by('completed', 'due_date', '-created_at')

    total_tasks_count = tasks.count()
    completed_tasks_count = tasks.filter(completed=True).count()
    
    completed_percentage = 0
    if total_tasks_count > 0:
        completed_percentage = int((completed_tasks_count / total_tasks_count) * 100)

    context = {
        'group': group,
        'tasks': tasks,
        'total_tasks_count': total_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'completed_percentage': completed_percentage,
    }
    return render(request, 'groups/group_task_list.html', context)


@login_required
def group_task_create(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループにタスクを作成する権限がありません。') 
        return redirect('group_list')

    if request.method == 'POST':
        form = GroupTaskForm(request.POST, group=group) # groupオブジェクトをフォームに渡す
        if form.is_valid():
            task = form.save(commit=False)
            task.group = group
            task.created_by = request.user
            task.save()
            messages.success(request, f'新しいタスク "{task.title}" を作成しました。')
            return redirect('group_task_list', group_id=group.id)
        else:
            messages.error(request, f'タスク作成に失敗しました。入力内容を確認してください。') 
    else:
        form = GroupTaskForm(group=group) # groupオブジェクトをフォームに渡す
    
    return render(request, 'groups/group_task_form.html', {'group': group, 'form': form, 'form_type': 'create'})

@login_required
def group_task_detail(request, group_id, pk):
    group = get_object_or_404(Group, id=group_id)
    task = get_object_or_404(GroupTask, pk=pk, group=group)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのタスクを閲覧する権限がありません。') 
        return redirect('group_list')
    
    return render(request, 'groups/group_task_detail.html', {'group': group, 'task': task})

@login_required
def group_task_update(request, group_id, pk):
    group = get_object_or_404(Group, id=group_id)
    task = get_object_or_404(GroupTask, pk=pk, group=group)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのタスクを編集する権限がありません。') 
        return redirect('group_list')
    # タスク作成者のみが編集可能とする例（必要に応じて権限ロジックを変更）
    if request.user != task.created_by: 
        messages.error(request, f'このタスクを編集する権限がありません。') 
        return redirect('group_task_detail', group_id=group.id, pk=task.id)

    if request.method == 'POST':
        form = GroupTaskForm(request.POST, instance=task, group=group) # groupオブジェクトをフォームに渡す
        if form.is_valid():
            form.save()
            messages.success(request, f'タスク "{task.title}" を更新しました。')
            return redirect('group_task_list', group_id=group.id)
        else:
            messages.error(request, f'タスク更新に失敗しました。入力内容を確認してください。') 
    else:
        form = GroupTaskForm(instance=task, group=group) # groupオブジェクトをフォームに渡す
    
    return render(request, 'groups/group_task_form.html', {'group': group, 'form': form, 'form_type': 'update'})

@login_required
@require_POST
def group_task_delete(request, group_id, pk):
    group = get_object_or_404(Group, id=group_id)
    task = get_object_or_404(GroupTask, pk=pk, group=group)
    if not is_group_member(request.user, group):
        messages.error(request, f'このグループのタスクを削除する権限がありません。')
        return redirect('group_list')
    # タスク作成者のみが削除可能とする例
    if request.user != task.created_by: 
        messages.error(request, f'このタスクを削除する権限がありません。')
        return redirect('group_task_detail', group_id=group.id, pk=task.id)
    
    task.delete()
    messages.success(request, f'タスクを削除しました。') 
    return redirect('group_task_list', group_id=group.id)

@login_required
@require_POST
def group_task_toggle_complete(request, group_id, pk):
    group = get_object_or_404(Group, id=group_id)
    task = get_object_or_404(GroupTask, pk=pk, group=group)
    if not is_group_member(request.user, group):
        return JsonResponse({'status': 'error', 'message': 'グループメンバーではありません。'}, status=403)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            task.completed = data.get('completed', not task.completed) 
        except json.JSONDecodeError:
            task.completed = not task.completed
    else:
        task.completed = not task.completed

    task.save()
    messages.success(request, f'タスク "{task.title}" の完了ステータスを更新しました。')
    
    return JsonResponse({'status': 'success', 'completed': task.completed})

@login_required
def calendar_data(request):
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')

    events = []

    try:
        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date format for start or end parameters.'}, status=400)

    # 1. 個人のタスク
    personal_tasks = request.user.personal_tasks.filter(
        due_date__gte=start_date, 
        due_date__lte=end_date
    ).order_by('due_date')

    for task in personal_tasks:
        events.append({
            'id': f'pt-{task.id}',
            'title': f'[個人]{task.title}',
            'start': task.due_date.isoformat(),
            'end': task.due_date.isoformat(),
            'allDay': True,
            'color': '#28a745' if task.completed else '#007bff', 
            'textColor': 'white',
            'extendedProps': {
                'type': 'personal_task',
                'completed': task.completed,
                'description': task.description,
                'url': f'/users/tasks/{task.id}/', 
            }
        })

    # 2. ユーザーが参加しているグループのタスク
    user_groups = request.user.joined_groups.all()

    for group in user_groups:
        group_tasks = GroupTask.objects.filter(
            group=group,
            due_date__gte=start_date, 
            due_date__lte=end_date
        ).order_by('due_date')

        for task in group_tasks:
            events.append({
                'id': f'gt-{task.id}',
                'title': f'[G:{group.name}]{task.title}',
                'start': task.due_date.isoformat(),
                'end': task.due_date.isoformat(),
                'allDay': True,
                'color': '#fd7e14' if task.completed else '#ffc107', 
                'textColor': 'white',
                'extendedProps': {
                    'type': 'group_task',
                    'completed': task.completed,
                    'group_id': group.id,
                    'description': task.description,
                    'assigned_to': task.assigned_to.username if task.assigned_to else '未割り当て',
                    'url': f'/groups/{group.id}/tasks/{task.id}/', 
                }
            })
    # ★ここからPersonalEventのデータ取得を追加
    personal_events = request.user.personal_events.filter(
        Q(start_time__date__gte=start_date) & Q(start_time__date__lte=end_date) |
        Q(end_time__date__gte=start_date) & Q(end_time__date__lte=end_date) |
        Q(start_time__date__lte=start_date) & Q(end_time__date__gte=end_date) # 期間をまたぐイベント
    ).order_by('start_time')

    for event in personal_events:
        events.append({
            'id': f'pe-{event.id}',
            'title': f'[予定]{event.title}',
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat() if event.end_time else None, # 終日の場合はnull
            'allDay': event.is_all_day,
            'color': '#6f42c1', # 紫色
            'textColor': 'white',
            'extendedProps': {
                'type': 'personal_event',
                'description': event.description,
                'url': f'/users/events/{event.id}/', # 詳細ページへのURL（後で定義）
            }
        })


    return JsonResponse(events, safe=False) 