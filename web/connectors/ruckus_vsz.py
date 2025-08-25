from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class RuckusVSZError(Exception):
    """Raised when the vSZ API returns an error."""


@dataclass
class RuckusCredentials:
    base_url: str
    username: str
    password: str
    verify_ssl: bool = True


class RuckusVSZClient:
    """Minimal Ruckus vSZ public API client.

    Note: vSZ public API versions vary by release (v5.x, v6.x, v9.x).
    The default endpoints here use v6_1, but you should override with env
    RUCKUS_VSZ_API_PREFIX if needed, e.g. "/api/public/v9_0".
    """

    def __init__(self, creds: Optional[RuckusCredentials] = None):
        if creds is None:
            creds = RuckusCredentials(
                base_url=os.environ.get("RUCKUS_VSZ_URL", ""),
                username=os.environ.get("RUCKUS_VSZ_USERNAME", ""),
                password=os.environ.get("RUCKUS_VSZ_PASSWORD", ""),
                verify_ssl=os.environ.get("RUCKUS_VSZ_VERIFY_SSL", "true").lower() in ("1", "true", "yes", "on"),
            )
        self.creds = creds
        self._session = requests.Session()
        self._jsessionid: Optional[str] = None
        self.api_prefix = os.environ.get("RUCKUS_VSZ_API_PREFIX", "/api/public/v6_1")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._jsessionid:
            headers["Cookie"] = f"JSESSIONID={self._jsessionid}"
        return headers

    def login(self) -> None:
        url = f"{self.creds.base_url.rstrip('/')}{self.api_prefix}/session"
        resp = self._session.post(url, json={"username": self.creds.username, "password": self.creds.password}, verify=self.creds.verify_ssl)
        if resp.status_code != 200:
            raise RuckusVSZError(f"Login failed: {resp.status_code} {resp.text}")
        self._jsessionid = resp.cookies.get("JSESSIONID")
        if not self._jsessionid:
            raise RuckusVSZError("Missing JSESSIONID in login response")

    def logout(self) -> None:
        if not self._jsessionid:
            return
        url = f"{self.creds.base_url.rstrip('/')}{self.api_prefix}/session"
        self._session.delete(url, headers=self._headers(), verify=self.creds.verify_ssl)
        self._jsessionid = None

    def ensure_login(self) -> None:
        if not self._jsessionid:
            self.login()

    def create_guest_user(self, username: str, password: str, validity_minutes: int = 60) -> Dict[str, Any]:
        """Create a guest user on vSZ. Requires Guest Access configured.

        Endpoint may differ by version. Adjust RUCKUS_VSZ_API_PREFIX accordingly.
        """
        self.ensure_login()
        url = f"{self.creds.base_url.rstrip('/')}{self.api_prefix}/guests/accounts"
        payload = {
            "name": username,
            "password": password,
            "validity": {"duration": validity_minutes, "timeUnit": "MINUTE"},
            "enabled": True,
        }
        resp = self._session.post(url, json=payload, headers=self._headers(), verify=self.creds.verify_ssl)
        if resp.status_code not in (200, 201):
            raise RuckusVSZError(f"Create guest failed: {resp.status_code} {resp.text}")
        return resp.json() if resp.text else {"status": "ok"}

    def delete_guest_user(self, account_id: str) -> None:
        self.ensure_login()
        url = f"{self.creds.base_url.rstrip('/')}{self.api_prefix}/guests/accounts/{account_id}"
        resp = self._session.delete(url, headers=self._headers(), verify=self.creds.verify_ssl)
        if resp.status_code not in (200, 204):
            raise RuckusVSZError(f"Delete guest failed: {resp.status_code} {resp.text}")

