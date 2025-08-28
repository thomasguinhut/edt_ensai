import os
import json
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from icalendar import Calendar


def log(message):
    """Affiche un message avec l'heure pour le débogage."""
    print(f"{datetime.now()}: {message}")


def download_ics_file(url):
    """Télécharge le fichier ICS depuis l'URL."""
    try:
        log(f"Téléchargement du fichier ICS depuis {url}...")
        response = requests.get(url)
        response.raise_for_status()
        log("Fichier ICS téléchargé avec succès.")
        return response.content
    except Exception as e:
        log(f"Erreur lors du téléchargement : {e}")
        raise


def parse_ics_to_events(ics_content):
    """Parse le contenu ICS et convertit en événements Google Calendar."""
    try:
        cal = Calendar.from_ical(ics_content)
        events = []

        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary', 'Sans titre'))
                description = str(component.get('description', ''))
                location = str(component.get('location', ''))

                dtstart = component.get('dtstart')
                dtend = component.get('dtend')

                if dtstart and dtend:
                    start_dt = dtstart.dt
                    end_dt = dtend.dt

                    if isinstance(start_dt, datetime):
                        event = {
                            'summary': summary,
                            'description': description,
                            'location': location,
                            'start': {
                                'dateTime': start_dt.isoformat(),
                                'timeZone': 'Europe/Paris',
                            },
                            'end': {
                                'dateTime': end_dt.isoformat(),
                                'timeZone': 'Europe/Paris',
                            },
                        }
                    else:
                        event = {
                            'summary': summary,
                            'description': description,
                            'location': location,
                            'start': {
                                'date': start_dt.strftime('%Y-%m-%d'),
                            },
                            'end': {
                                'date': end_dt.strftime('%Y-%m-%d'),
                            },
                        }
                    events.append(event)

        log(f"Parsing terminé : {len(events)} événements extraits.")
        return events
    except Exception as e:
        log(f"Erreur lors du parsing ICS : {e}")
        raise


def clear_google_calendar(service, calendar_id):
    """Supprime TOUS les événements d'un agenda Google."""
    log(f"Suppression de tous les événements de l'agenda {calendar_id}...")
    deleted_count = 0

    # Récupère les événements par pages
    events_result = service.events().list(calendarId=calendar_id, maxResults=250).execute()
    while True:
        events = events_result.get('items', [])
        for event in events:
            try:
                service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
                deleted_count += 1
            except Exception as e:
                log(f"Erreur lors de la suppression de l'événement {event['id']}: {e}")

        next_page_token = events_result.get('nextPageToken')
        if not next_page_token:
            break
        events_result = service.events().list(
            calendarId=calendar_id, maxResults=250, pageToken=next_page_token
        ).execute()

    log(f"Supprimé {deleted_count} événement(s) au total.")


def update_google_calendar(ics_content, calendar_id):
    """Met à jour Google Agenda avec le contenu ICS."""
    try:
        google_credentials = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
        creds = Credentials.from_service_account_info(
            google_credentials,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=creds)

        # Supprime tous les événements existants
        clear_google_calendar(service, calendar_id)

        # Parse et importe les nouveaux événements
        parsed_events = parse_ics_to_events(ics_content)
        log(f"Importation de {len(parsed_events)} événements...")

        imported_count = 0
        for event_data in parsed_events:
            try:
                service.events().insert(calendarId=calendar_id, body=event_data).execute()
                imported_count += 1
            except Exception as e:
                log(f"Erreur lors de l'ajout d'un événement : {e}")
                log(f"Données de l'événement : {event_data}")

        log(f"Agenda {calendar_id} mis à jour avec succès ! {imported_count} événements importés.")

    except Exception as e:
        log(f"Erreur lors de la mise à jour : {e}")
        raise


def main():
    try:
        ics_url = os.getenv('ICS_URL')
        calendar_id = os.getenv('CALENDAR_ID')

        if not ics_url:
            raise ValueError("L'URL du fichier ICS (ICS_URL) n'est pas définie.")
        if not calendar_id:
            raise ValueError("L'ID de l'agenda (CALENDAR_ID) n'est pas défini.")

        log(f"Utilisation de l'agenda : {calendar_id}")
        ics_content = download_ics_file(ics_url)
        update_google_calendar(ics_content, calendar_id)

    except Exception as e:
        log(f"Échec : {e}")
        exit(1)


if __name__ == '__main__':
    main()
