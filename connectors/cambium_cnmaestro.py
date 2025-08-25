from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class CambiumError(Exception):
    """Raised when the cnMaestro API returns an error."""


@dataclass
class CambiumCredentials:
    base_url: str
    api_token: str
    verify_ssl: bool = True


class CambiumClient:
    """Minimal Cambium cnMaestro API client.

    cnMaestro APIs differ between cloud and on-prem editions. Provide the
    base URL and API token via env or constructor.
    """

    def __init__(self, creds: Optional[CambiumCredentials] = None):
        if creds is None:
            creds = CambiumCredentials(
                base_url=os.environ.get("CAMBIUM_URL", ""),
                api_token=os.environ.get("CAMBIUM_API_TOKEN", ""),
                verify_ssl=os.environ.get("CAMBIUM_VERIFY_SSL", "true").lower() in ("1", "true", "yes", "on"),
            )
        self.creds = creds
        self._session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.creds.api_token}",
        }

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.creds.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = self._session.get(url, headers=self._headers(), params=params, verify=self.creds.verify_ssl)
        if resp.status_code >= 400:
            raise CambiumError(f"GET {url} failed: {resp.status_code} {resp.text}")
        return resp

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.creds.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = self._session.post(url, headers=self._headers(), json=json, verify=self.creds.verify_ssl)
        if resp.status_code >= 400:
            raise CambiumError(f"POST {url} failed: {resp.status_code} {resp.text}")
        return resp

    # Placeholder methods. Replace 'guests/create' with your cnMaestro endpoint.
    def create_guest_user(self, username: str, password: str, validity_minutes: int = 60) -> Dict[str, Any]:
        payload = {
            "name": username,
            "password": password,
            "validity": validity_minutes,
        }
        resp = self.post("guests/create", json=payload)
        return resp.json() if resp.text else {"status": "ok"}

    def delete_guest_user(self, account_id: str) -> None:
        self.post("guests/delete", json={"id": account_id})

