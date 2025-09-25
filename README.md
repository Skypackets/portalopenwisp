# Portal OpenWISP

A Django 5 project scaffold for a portal-style application.

## Quick start

1. Create and activate the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Run migrations and start the server

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

3. Visit the app at `http://localhost:8000`

## Development

- Home page view lives in `home/views.py` and template in `templates/home.html`.
- Project settings are in `portalopenwisp/settings.py`.

## License

This project is licensed under the MIT License. See `LICENSE` for details.