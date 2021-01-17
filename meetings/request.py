import datetime
from googleapiclient.discovery import build


def calendar_service(creds):
    return build('calendar', 'v3', credentials=creds)


def get_events(service):
    # Call the Calendar API
    now = datetime.datetime.utcnow()
    initial_datetime = (now - datetime.timedelta(weeks=52 * 5)).isoformat() + "Z"
    latest_datetime = now.isoformat() + "Z"
    print(f'Getting events since {initial_datetime} and {now}')

    counter = 0
    token = None
    events = []

    while True:
        print(f'request {counter} : #events {len(events)}')
        event_results = _get_event_results(service, initial_datetime, latest_datetime=latest_datetime, token=token)
        events.extend(event_results['items'])
        if 'nextPageToken' in event_results:
            token = event_results['nextPageToken']
            print(f'{event_results["items"][0]["start"]}')
            counter += 1
        else:
            break
    return events


def _get_event_results(service, initial_datetime, latest_datetime, token):
    return service.events()\
        .list(
            pageToken=token,
            calendarId='primary',
            timeMin=initial_datetime,
            timeMax=latest_datetime,
            singleEvents=True,
            orderBy='startTime'
        )\
        .execute()
