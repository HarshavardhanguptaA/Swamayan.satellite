"""Earth Engine initialization supporting both local OAuth and hosted service accounts."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import ee

from config.constants import GEE_PROJECT_ID


def _get_streamlit_secret(key: str, default: Any = None) -> Any:
    """Safely retrieve a secret from Streamlit secrets without throwing if absent."""
    try:
        import streamlit as st
        # Accessing st.secrets may raise StreamlitSecretNotFoundError or FileNotFoundError
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def _get_service_account_info() -> dict[str, Any] | None:
    """Extract and parse service account credentials from Streamlit secrets."""
    candidate_keys = [
        "EARTH_ENGINE_SERVICE_ACCOUNT",
        "EE_SERVICE_ACCOUNT_JSON",
        "EE_SERVICE_ACCOUNT",
        "gcp_service_account",
    ]
    raw_secret = None
    for key in candidate_keys:
        val = _get_streamlit_secret(key)
        if val is not None:
            raw_secret = val
            break

    if raw_secret is None:
        return None

    # Handle Streamlit TOML table / dict mapping
    if isinstance(raw_secret, dict) or hasattr(raw_secret, "items"):
        return dict(raw_secret)

    # Handle JSON string representation
    if isinstance(raw_secret, str) and raw_secret.strip():
        try:
            parsed = json.loads(raw_secret)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            raise ValueError(
                "Failed to parse Earth Engine service account credentials from secrets: invalid JSON format."
            ) from None

    return None


def get_configured_project_id(explicit_project: str | None = None) -> str:
    """Resolve project ID in priority order: explicit arg -> st.secrets -> env var -> constants -> service account."""
    if explicit_project and explicit_project.strip():
        return explicit_project.strip()

    secret_project = _get_streamlit_secret("EE_PROJECT_ID")
    if secret_project and str(secret_project).strip():
        return str(secret_project).strip()

    env_project = os.getenv("EE_PROJECT_ID", "").strip()
    if env_project:
        return env_project

    if GEE_PROJECT_ID and GEE_PROJECT_ID.strip():
        return GEE_PROJECT_ID.strip()

    try:
        sa_info = _get_service_account_info()
        if sa_info and isinstance(sa_info, dict) and sa_info.get("project_id"):
            return str(sa_info["project_id"]).strip()
    except Exception:
        pass

    return ""


def _sanitize_auth_error(exc: Exception, sa_info: dict[str, Any] | None = None) -> str:
    """Redact any sensitive credential data, private keys, or tokens from error messages."""
    msg = str(exc)
    if sa_info and isinstance(sa_info, dict):
        pk = sa_info.get("private_key")
        if pk and isinstance(pk, str):
            msg = msg.replace(pk, "[REDACTED_PRIVATE_KEY]")
            inner_lines = [line.strip() for line in pk.splitlines() if line.strip() and not line.strip().startswith("-----")]
            for line in inner_lines:
                if len(line) >= 8:
                    msg = msg.replace(line, "[REDACTED_PRIVATE_KEY]")
    # Redact any PEM private key blocks
    msg = re.sub(r"-----BEGIN [A-Z ]+-----[^-]+-----END [A-Z ]+-----", "[REDACTED_PRIVATE_KEY]", msg)
    # Redact inline private key JSON/dict entries
    msg = re.sub(r"('private_key'|\"private_key\")\s*:\s*('[^']+'|\"[^\"]+\")", r"\1: '[REDACTED]'", msg)
    if "could not be converted to bytes" in msg:
        return "The private key in service account credentials is malformed or invalid."
    return msg


def initialize_earth_engine(project_id: str | None = None) -> Any:
    """Initialize Earth Engine using hosted service-account credentials or local OAuth.

    Supports:
    1. Streamlit Community Cloud: Authenticates using service-account credentials
       defined in ``st.secrets['EARTH_ENGINE_SERVICE_ACCOUNT']`` or ``st.secrets['EE_SERVICE_ACCOUNT_JSON']``.
    2. Local Development: Retains persistent local OAuth credentials (``~/.config/earthengine``).
    """
    project = get_configured_project_id(project_id)

    try:
        sa_info = _get_service_account_info()
    except Exception as exc:
        raise RuntimeError(
            f"Invalid Earth Engine service account configuration in secrets: {_sanitize_auth_error(exc)}"
        ) from None

    # 1. Hosted Service Account Flow
    if sa_info is not None:
        client_email = sa_info.get("client_email")
        private_key = sa_info.get("private_key")
        if not client_email or not private_key:
            raise RuntimeError(
                "Earth Engine service account secret is missing required 'client_email' or 'private_key' field."
            )
        try:
            credentials = ee.ServiceAccountCredentials(
                email=client_email,
                key_data=json.dumps(sa_info),
            )
            if project:
                ee.Initialize(credentials=credentials, project=project)
            else:
                ee.Initialize(credentials=credentials)
            return ee
        except Exception as exc:
            sanitized = _sanitize_auth_error(exc, sa_info=sa_info)
            raise RuntimeError(
                "Google Earth Engine service account authentication failed. "
                "Ensure the service account has Earth Engine API permissions and the "
                f"credentials in secrets are valid. Error: {sanitized}"
            ) from None

    # 2. Local OAuth Flow (or default ADC)
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
        return ee
    except Exception as exc:
        sanitized = _sanitize_auth_error(exc)
        raise RuntimeError(
            "Google Earth Engine could not be initialized. "
            "For local development, run `earthengine authenticate` in your terminal and set EE_PROJECT_ID. "
            "For Streamlit Community Cloud, configure EARTH_ENGINE_SERVICE_ACCOUNT and EE_PROJECT_ID in app Secrets. "
            f"Original error: {sanitized}"
        ) from None
