from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
from users.models import UserGoogleCredential

def get_upcoming_google_events(user):
    try:
        # ユーザーの認証情報を取得
        cred_obj = UserGoogleCredential.objects.get(user=user)
        creds = Credentials.from_authorized_user_info(info=cred_obj.token_data)

        # Google Calendar APIを使って予定取得
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z'
        max_time = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=max_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])

    except UserGoogleCredential.DoesNotExist:
        return []
    except Exception as e:
        print("Google予定取得エラー:", e)
        return []
