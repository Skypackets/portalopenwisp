from __future__ import annotations

import dataclasses
import hashlib
import hmac
import time
from typing import Any, Dict, Optional

import requests
from django.conf import settings


@dataclasses.dataclass
class AuthResult:
    ok: bool
    message: str = ""
    session_ms: int = 0
    bytes_limit: Optional[int] = None


class BaseControllerClient:
    def __init__(self, base_url: str, api_key: str = "", api_secret: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.metadata = metadata or {}

    def _test_mode(self) -> bool:
        return bool(getattr(settings, "CONTROLLERS_TEST_MODE", True))

    def authorize_mac(self, ssid_name: str, mac: str, session_ms: int) -> AuthResult:
        raise NotImplementedError

    def disconnect_mac(self, ssid_name: str, mac: str, message: str = "") -> bool:
        raise NotImplementedError


class RuckusSmartZoneClient(BaseControllerClient):
    def authorize_mac(self, ssid_name: str, mac: str, session_ms: int) -> AuthResult:
        if self._test_mode():
            return AuthResult(ok=True, message="authorized(test)", session_ms=session_ms)
        # Example placeholder: normally call SmartZone AAA/RADIUS or hotspot API
        try:
            # Pseudo-endpoint; replace with actual API specifics
            resp = requests.post(
                f"{self.base_url}/portal/authorize",
                json={"ssid": ssid_name, "mac": mac, "session_ms": session_ms},
                timeout=5,
            )
            ok = resp.status_code in (200, 204)
            return AuthResult(ok=ok, message=resp.text, session_ms=session_ms)
        except Exception as exc:
            return AuthResult(ok=False, message=str(exc))

    def disconnect_mac(self, ssid_name: str, mac: str, message: str = "") -> bool:
        if self._test_mode():
            return True
        try:
            resp = requests.post(
                f"{self.base_url}/portal/coa",
                json={"ssid": ssid_name, "mac": mac, "message": message},
                timeout=5,
            )
            return resp.status_code in (200, 204)
        except Exception:
            return False


class CambiumCnMaestroClient(BaseControllerClient):
    def authorize_mac(self, ssid_name: str, mac: str, session_ms: int) -> AuthResult:
        if self._test_mode():
            return AuthResult(ok=True, message="authorized(test)", session_ms=session_ms)
        try:
            # Placeholder for cnMaestro API
            ts = int(time.time())
            signature = hmac.new(self.api_secret.encode(), f"{mac}:{ts}".encode(), hashlib.sha256).hexdigest()
            resp = requests.post(
                f"{self.base_url}/guest/authorize",
                json={
                    "ssid": ssid_name,
                    "mac": mac,
                    "session_ms": session_ms,
                    "api_key": self.api_key,
                    "ts": ts,
                    "sig": signature,
                },
                timeout=5,
            )
            ok = resp.status_code in (200, 204)
            return AuthResult(ok=ok, message=resp.text, session_ms=session_ms)
        except Exception as exc:
            return AuthResult(ok=False, message=str(exc))

    def disconnect_mac(self, ssid_name: str, mac: str, message: str = "") -> bool:
        if self._test_mode():
            return True
        try:
            resp = requests.post(
                f"{self.base_url}/guest/coa",
                json={"ssid": ssid_name, "mac": mac, "message": message},
                timeout=5,
            )
            return resp.status_code in (200, 204)
        except Exception:
            return False


def get_client(controller_type: str, base_url: str, api_key: str, api_secret: str, metadata: Optional[Dict[str, Any]] = None) -> BaseControllerClient:
    if controller_type == "ruckus_sz":
        return RuckusSmartZoneClient(base_url, api_key, api_secret, metadata)
    if controller_type == "cambium_cnmaestro":
        return CambiumCnMaestroClient(base_url, api_key, api_secret, metadata)
    raise ValueError(f"Unsupported controller type: {controller_type}")
