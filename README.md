### Sky Packets Portal (OpenWISP Captive Portal Manager)

This repository wraps OpenWISP captive portal components with Sky Packets branding, adds vendor connectors (Ruckus vSZ, Cambium cnMaestro), and provides AWS/Ubuntu deployment scripts.

Quickstart (Docker)
- Copy `.env.example` to `.env` and adjust values
- Build and run:
  - `docker compose build`
  - `docker compose up -d`
- Access the portal: `http://localhost:8000`

Local dev without Docker
- Create a venv and install requirements: `python3 -m venv .venv && . .venv/bin/activate && pip install -r web/requirements.txt`
- Set env vars (or copy `.env.example` to `.env` and export as needed)
- Run server: `cd web && python manage.py runserver 0.0.0.0:8000`

Components
- Django app with OpenWISP-compatible hooks (WiFi login pages, RADIUS-ready)
- Connectors: Ruckus vSZ and Cambium cnMaestro
- Branding: Sky Packets theme (templates, CSS)
- Deployment: Ubuntu installer and AWS user-data

Directories
- `web`: Django project and Docker image
- `web/connectors`: Vendor API clients
- `bin`: CLI utilities for vendors (use `python -m` from repo root)
- `deploy`: Ubuntu and AWS scripts
- `web/branding/sky_packets`: Branding overrides

Notes
This is a scaffold. Configure your RADIUS and vendor controller details to enable full captive portal flows. The connectors provide API utilities to sync guest accounts/vouchers with Ruckus and Cambium.

CLI examples
- Ruckus: `python -m bin.ruckus_cli create demo demo123 --minutes 120`
- Cambium: `python -m bin.cambium_cli create demo demo123 --minutes 120`
