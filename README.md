# Event Registration System (Django + DRF)

A REST API for browsing events, registering for them, and managing registrations,
with token authentication and a Django admin panel for organizers.

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # admin / organizer account
python manage.py runserver
```

- API root: http://127.0.0.1:8000/api/
- Admin panel: http://127.0.0.1:8000/admin/
- Run tests: `python manage.py test`

## Using PostgreSQL (optional)

`pip install psycopg2-binary`, then replace `DATABASES` in `config/settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "eventdb", "USER": "postgres",
        "PASSWORD": "yourpassword", "HOST": "localhost", "PORT": "5432",
    }
}
```

## Data model

- **Event**: title, description, location, start_time, end_time, capacity, organizer (User)
- **Registration**: user (User), event (Event), full_name, email, phone, status (confirmed/cancelled), timestamps
  - A user can hold only one *confirmed* registration per event (DB constraint).
  - Cancelling keeps the record (status = cancelled) and frees the seat.

## Endpoints

| Method | URL | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/signup/` | none | Create account |
| POST | `/api/auth/login/` | none | Get token (`username`, `password`) |
| GET | `/api/events/` | none | List events (`?upcoming=true`, `?search=term`, `?page=2`) |
| POST | `/api/events/` | token | Create event (you become organizer) |
| GET | `/api/events/<id>/` | none | Event details + `seats_left` |
| PUT/PATCH/DELETE | `/api/events/<id>/` | organizer | Edit / delete event |
| GET | `/api/events/<id>/registrations/` | organizer | Attendee list |
| POST | `/api/registrations/` | token | Register for an event |
| GET | `/api/registrations/mine/` | token | My registrations |
| GET | `/api/registrations/<id>/` | token | One of my registrations |
| POST | `/api/registrations/<id>/cancel/` | token | Cancel my registration |

Send the token as: `Authorization: Token <your_token>`

## Quick try with curl

```bash
# sign up and log in
curl -X POST localhost:8000/api/auth/signup/ -d "username=alice&password=secret123&email=a@x.com"
curl -X POST localhost:8000/api/auth/login/  -d "username=alice&password=secret123"

# create an event (use the token from login)
curl -X POST localhost:8000/api/events/ -H "Authorization: Token TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hack Night","location":"Coimbatore","start_time":"2026-12-01T18:00:00Z","end_time":"2026-12-01T21:00:00Z","capacity":30}'

# register for event 1
curl -X POST localhost:8000/api/registrations/ -H "Authorization: Token TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event":1,"full_name":"Alice","email":"a@x.com","phone":"9999999999"}'

# view / cancel
curl localhost:8000/api/registrations/mine/ -H "Authorization: Token TOKEN"
curl -X POST localhost:8000/api/registrations/1/cancel/ -H "Authorization: Token TOKEN"
```

## Project layout

```
config/            settings, root urls
events/models.py   Event, Registration
events/serializers.py  validation (capacity, duplicates, dates)
events/views.py    API views + permissions
events/urls.py     routes
events/admin.py    organizer admin panel
events/tests.py    9 tests
```
