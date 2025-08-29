import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from icalendar import Calendar


def log(message):
    """Affiche un message avec l'heure pour le débogage."""
    print(f"{datetime.now()}: {message}")


# --- Gestion du fichier ICS ---
def download_ics_file(url):
    """
    Télécharge le fichier ICS depuis une URL donnée.

    Args:
        url (str): URL du fichier ICS à télécharger.

    Returns:
        bytes: Contenu brut du fichier ICS.

    Raises:
        Exception: En cas d'erreur de téléchargement.
    """
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
    """
    Parse le contenu ICS et convertit les événements en format compatible avec Google Calendar.

    Args:
        ics_content (bytes): Contenu brut du fichier ICS.

    Returns:
        list[dict]: Liste des événements au format Google Calendar.

    Raises:
        Exception: En cas d'erreur de parsing.
    """
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
                            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Paris'},
                            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Paris'},
                        }
                    else:
                        event = {
                            'summary': summary,
                            'description': description,
                            'location': location,
                            'start': {'date': start_dt.strftime('%Y-%m-%d')},
                            'end': {'date': end_dt.strftime('%Y-%m-%d')},
                        }
                    events.append(event)
        log(f"Parsing terminé : {len(events)} événements extraits.")
        return events
    except Exception as e:
        log(f"Erreur lors du parsing ICS : {e}")
        raise


# --- Gestion de Google Calendar ---
def clear_google_calendar(service, calendar_id):
    """
    Supprime tous les événements d'un agenda Google.

    Args:
        service: Objet de service Google Calendar authentifié.
        calendar_id (str): ID de l'agenda à vider.

    Returns:
        None
    """
    log(f"Suppression de tous les événements de l'agenda {calendar_id}...")
    deleted_count = 0
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


# --- Envoi d'email ---
def send_email(subject, body, to_email):
    """
    Envoie un email via SMTP.

    Args:
        subject (str): Sujet de l'email.
        body (str): Corps de l'email.
        to_email (str): Adresse email du destinataire.

    Returns:
        None
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        if not smtp_user or not smtp_password:
            log("SMTP_USER ou SMTP_PASSWORD non défini.")
            return
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        log(f"Email envoyé à {to_email}")
    except Exception as e:
        log(f"Erreur lors de l'envoi de l'email : {e}")


# --- Mise à jour du calendrier ---
def update_google_calendar(ics_content, calendar_id):
    """
    Met à jour un agenda Google avec les événements d'un fichier ICS.

    Args:
        ics_content (bytes): Contenu brut du fichier ICS.
        calendar_id (str): ID de l'agenda Google à mettre à jour.

    Returns:
        None

    Raises:
        Exception: En cas d'erreur lors de la mise à jour.
    """
    try:
        google_credentials = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
        creds = Credentials.from_service_account_info(
            google_credentials,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=creds)

        clear_google_calendar(service, calendar_id)
        parsed_events = parse_ics_to_events(ics_content)

        imported_count = 0
        for event_data in parsed_events:
            try:
                service.events().insert(calendarId=calendar_id, body=event_data).execute()
                imported_count += 1
            except Exception as e:
                log(f"Erreur lors de l'ajout d'un événement : {e}")

        log(f"Agenda {calendar_id} mis à jour avec succès ! {imported_count} événements importés.")

        # Envoi du mail de notification
        to_email = os.getenv('NOTIFY_EMAIL')
        if to_email:
            send_email(
                subject="EDT 3A MSP",
                body="L'EDT a été mis à jour !",
                to_email=to_email
            )
    except Exception as e:
        log(f"Erreur lors de la mise à jour : {e}")
        to_email = os.getenv('NOTIFY_EMAIL')
        if to_email:
            send_email(
                subject=f"Échec de la mise à jour de l'agenda {calendar_id}",
                body=str(e),
                to_email=to_email
            )
        raise


# --- Fonction principale ---
def main():
    """
    Fonction principale : télécharge le fichier ICS et met à jour l'agenda Google.
    """
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
