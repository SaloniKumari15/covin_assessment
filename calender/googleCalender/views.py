import json
from django.shortcuts import redirect
from django.views import View
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient import discovery
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class GoogleCalendarInitView(APIView):
    def get(self, request):
        flow = Flow.from_client_secrets_file(
            settings.CLIENT_SECRETS_FILE,
            scopes=settings.SCOPES,
            redirect_uri=settings.REDIRECT_URL
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        request.session['state'] = state

        return Response({"authorization_url": authorization_url})

class GoogleCalendarRedirectView(APIView):
    def get(self, request):
        state = request.session['state']
        flow = Flow.from_client_secrets_file(
            settings.CLIENT_SECRETS_FILE,
            scopes=settings.SCOPES,
            state=state,
            redirect_uri=settings.REDIRECT_URL
        )
        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials
        request.session['credentials'] = credentials_to_dict(credentials)

        if 'credentials' not in request.session:
            return redirect('v1/calendar/init')

        credentials = Credentials(**request.session['credentials'])

        service = discovery.build(
            settings.API_SERVICE_NAME,
            settings.API_VERSION,
            credentials=credentials
        )

        calendar_list = service.calendarList().list().execute()
        calendar_id = calendar_list['items'][0]['id']

        events = service.events().list(calendarId=calendar_id).execute()

        events_list_append = []
        if not events['items']:
            return Response({"message": "No data found or user credentials invalid."})
        else:
            for events_list in events['items']:
                events_list_append.append(events_list)

            return Response({"events": events_list_append})

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
