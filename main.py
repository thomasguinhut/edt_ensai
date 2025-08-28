import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime


def log(message):
    print(f"{datetime.now()}: {message}")


def list_calendars():
    google_credentials = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = Credentials.from_service_account_info(google_credentials, scopes=['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)
    calendars = service.calendarList().list().execute()
    log("Liste des agendas disponibles :")
    for calendar in calendars.get('items', []):
        log(f"ID: {calendar['id']}, Nom: {calendar['summary']}")


def update_google_calendar(ics_content, calendar_id):
    try:
        google_credentials = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
        creds = Credentials.from_service_account_info(google_credentials, scopes=['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)

        # Supprime les anciens événements (optionnel)
        events = service.events().list(calendarId=calendar_id).execute()
        for event in events.get('items', []):
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()

        # Import du fichier ICS
        media = MediaIoBaseUpload(io.BytesIO(ics_content), mimetype='text/calendar')
        service.events().import_(
            calendarId=calendar_id,
            body={},
            media_body=media
        ).execute()
        log(f"Calendrier {calendar_id} mis à jour avec succès !")
    except Exception as e:
        log(f"Erreur : {e}")
        raise


def main():
    try:
        ics_url = os.getenv('ICS_URL')
        calendar_id = os.getenv('CALENDAR_ID', 'primary')  # Utilise 'primary' si CALENDAR_ID n'est pas défini
        log(f"Utilisation de l'agenda : {calendar_id}")
        ics_content = download_ics_file(ics_url)
        update_google_calendar(ics_content, calendar_id)
    except Exception as e:
        log(f"Échec : {e}")
        exit(1)


if __name__ == '__main__':
    list_calendars()  # Affiche la liste des agendas (optionnel)
    main()
