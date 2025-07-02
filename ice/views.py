# myapp/ice/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from .models import IcebreakSession, IcebreakTopic, IcebreakAnswer, IcebreakPresentation, Group
import random

@login_required
def session_start(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    today = timezone.now().date()
    
    session = IcebreakSession.objects.filter(group=group, date=today).first()
    
    current_topic = None

    if request.method == 'POST' and request.POST.get('reset_session'):
        if session: 
            IcebreakAnswer.objects.filter(session=session).delete()
            IcebreakPresentation.objects.filter(session=session).delete()
            session.status = 'pending'
            session.topic = None
            session.timer_minutes = 3 
            session.start_time = None
            session.presentation_start_time = None 
            session.save()
            messages.info(request, "既存のセッションがリセットされました。新しいアイスブレイクを開始します。")
        else: 
            session = IcebreakSession.objects.create(group=group, date=today, status='pending')
            messages.info(request, "新しいアイスブレイクを開始します。")
        
        if IcebreakTopic.objects.count() == 0:
            messages.error(request, "お題が登録されていません。管理者に連絡してください。")
            current_topic = None
        else:
            recent_topics_ids = IcebreakSession.objects.filter(group=group).order_by('-date').values_list('topic_id', flat=True)[:5]
            available_topics = IcebreakTopic.objects.exclude(id__in=recent_topics_ids)
            if available_topics.exists():
                current_topic = random.choice(list(available_topics))
            else:
                current_topic = random.choice(list(IcebreakTopic.objects.all()))
            session.topic = current_topic
            session.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'セッションをリセットしました', 'session_status': session.status, 'topic_content': current_topic.content if current_topic else 'N/A'})
        
        return redirect('session_start', group_id=group_id)

    if not session:
        session = IcebreakSession.objects.create(group=group, date=today, status='pending')

    if not session.topic:
        if IcebreakTopic.objects.count() == 0:
            messages.error(request, "お題が登録されていません。管理者に連絡してください。")
            current_topic = None
        else:
            recent_topics_ids = IcebreakSession.objects.filter(group=group).order_by('-date').values_list('topic_id', flat=True)[:5]
            available_topics = IcebreakTopic.objects.exclude(id__in=recent_topics_ids)
            if available_topics.exists():
                current_topic = random.choice(list(available_topics))
            else:
                current_topic = random.choice(list(IcebreakTopic.objects.all()))
            session.topic = current_topic
            session.save()
    else:
        current_topic = session.topic

    if session.status == 'active':
        return redirect('answer', session_id=session.id)
    elif session.status == 'presenting':
        return redirect('present', session_id=session.id)
    elif session.status == 'finished':
        pass 

    if request.method == 'POST':
        timer = int(request.POST.get('timer', 3))
        session.timer_minutes = timer
        session.status = 'active'
        session.start_time = timezone.now()
        session.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'セッションを開始しました', 'session_status': session.status, 'redirect_to': str(redirect('answer', session_id=session.id).url)})
        
        return redirect('answer', session_id=session.id)
    
    return render(request, 'ice/session_start.html', {
        'group': group,
        'session': session,
        'topic': current_topic, 
    })

@login_required
def answer(request, session_id):
    session = get_object_or_404(IcebreakSession, id=session_id)
    user = request.user

    answer, created = IcebreakAnswer.objects.get_or_create(session=session, user=user)
    if request.method == 'POST':
        answer.choice = request.POST.get('choice', '')
        answer.text = request.POST.get('text', '')
        answer.save()
        
        group_members = session.group.members.all()
        answered_users_ids = IcebreakAnswer.objects.filter(
            session=session
        ).filter(
            Q(choice__isnull=False) | Q(text__isnull=False)
        ).exclude(
            Q(choice='') & Q(text='') 
        ).values_list('user__id', flat=True).distinct()
        
        all_answered = set(answered_users_ids) == set(group_members.values_list('id', flat=True))

        if all_answered and session.status != 'presenting':
            session.status = 'presenting'
            session.presentation_start_time = timezone.now() 
            session.save()
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success', 
                'message': '回答を送信しました', 
                'user_answered': True,
                'session_status': session.status, 
                'all_answered': all_answered, 
            })
        
        return redirect('wait', session_id=session.id) 


    return render(request, 'ice/answer.html', {
        'session': session,
        'topic': session.topic,
        'answer': answer,
    })

@login_required
def wait(request, session_id):
    session = get_object_or_404(IcebreakSession, id=session_id)
    group_members = session.group.members.all()
    
    answered_users_ids = IcebreakAnswer.objects.filter(
        session=session
    ).filter(
        Q(choice__isnull=False) | Q(text__isnull=False)
    ).exclude(
        Q(choice='') & Q(text='') 
    ).values_list('user__id', flat=True).distinct()

    all_answered = set(answered_users_ids) == set(group_members.values_list('id', flat=True))

    if all_answered and session.status != 'presenting':
        session.status = 'presenting'
        session.presentation_start_time = timezone.now() 
        session.save()

    return render(request, 'ice/wait.html', {
        'session': session,
        'answered_users': answered_users_ids, 
        'group_members': group_members,
    })

@login_required
def present(request, session_id):
    session = get_object_or_404(IcebreakSession, id=session_id)
    user = request.user
    presentation, created = IcebreakPresentation.objects.get_or_create(session=session, user=user)

    if request.method == 'POST':
        presentation.presented = True
        presentation.presented_at = timezone.now()
        presentation.save()

        # ここで all_presented と session_status を再計算し、JSONレスポンスに含める
        presented_users = session.presentations.filter(presented=True).values_list('user', flat=True)
        group_members = session.group.members.all()
        all_presented = set(presented_users) == set(group_members.values_list('id', flat=True))

        if all_presented and session.status != 'finished':
            session.status = 'finished'
            session.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success', 
                'message': '発表を完了しました', 
                'user_presented': True,
                'session_status': session.status, # ★追加: 更新されたセッションステータス
                'all_presented': all_presented,   # ★追加: 更新された全発表済みフラグ
            })
        
        return redirect('group_detail', group_id=session.group.id)


    presented_users = session.presentations.filter(presented=True).values_list('user', flat=True)
    group_members = session.group.members.all()
    all_presented = set(presented_users) == set(group_members.values_list('id', flat=True))

    if all_presented and session.status != 'finished':
        session.status = 'finished'
        session.save()

    return render(request, 'ice/present.html', {
        'session': session,
        'presented_users': presented_users,
        'group_members': group_members,
    })

@login_required
def get_session_status(request, session_id):
    session = get_object_or_404(IcebreakSession, id=session_id)
    group_members = session.group.members.all()

    # 回答状況
    answered_users_data = []
    for member in group_members:
        answer = IcebreakAnswer.objects.filter(session=session, user=member).first()
        answered = False
        choice_content = ''
        text_content = ''
        if answer and (answer.choice or answer.text): 
            answered = True
            choice_content = answer.choice if answer.choice else ''
            text_content = answer.text if answer.text else ''
        answered_users_data.append({
            'id': member.id,
            'username': member.username,
            'answered': answered,
            'choice': choice_content, 
            'text': text_content,     
        })
    
    answered_users_ids = [data['id'] for data in answered_users_data if data['answered']]
    all_answered = len(answered_users_ids) == len(group_members)


    # 発表状況
    presented_users_data = []
    for member in group_members:
        presentation = IcebreakPresentation.objects.filter(session=session, user=member).first()
        presented = presentation.presented if presentation else False
        
        answer = IcebreakAnswer.objects.filter(session=session, user=member).first()
        choice_content = answer.choice if answer and answer.choice else ''
        text_content = answer.text if answer and answer.text else ''

        presented_users_data.append({
            'id': member.id,
            'username': member.username,
            'presented': presented,
            'choice': choice_content, 
            'text': text_content,     
        })
    
    presented_users_ids = [data['id'] for data in presented_users_data if data['presented']]
    all_presented = len(presented_users_ids) == len(group_members)


    remaining_time_seconds = -1 
    if session.status == 'active' and session.start_time:
        elapsed_time = (timezone.now() - session.start_time).total_seconds()
        total_session_duration = session.timer_minutes * 60 
        remaining_time_seconds = max(0, total_session_duration - elapsed_time)

    remaining_presentation_time_seconds = -1 
    if session.status == 'presenting' and session.presentation_start_time:
        elapsed_presentation_time = (timezone.now() - session.presentation_start_time).total_seconds()
        total_presentation_phase_duration = session.timer_minutes * 60 * len(group_members) 
        remaining_presentation_time_seconds = max(0, total_presentation_phase_duration - elapsed_presentation_time)


    data = {
        'session_id': session.id,
        'group_id': session.group.id,
        'status': session.status,
        'topic_content': session.topic.content if session.topic else 'N/A',
        'timer_minutes': session.timer_minutes, 
        'remaining_time_seconds': int(remaining_time_seconds), 
        'remaining_presentation_time_seconds': int(remaining_presentation_time_seconds), 
        'answered_status': answered_users_data, 
        'all_answered': all_answered,
        'presentation_status': presented_users_data, 
        'all_presented': all_presented,
        'current_user_id': request.user.id,
    }
    return JsonResponse(data)