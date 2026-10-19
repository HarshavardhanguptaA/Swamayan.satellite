"""Unit tests for Earth Engine authentication (service account and local OAuth)."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from gee.auth import (
    _get_service_account_info,
    _get_streamlit_secret,
    _sanitize_auth_error,
    get_configured_project_id,
    initialize_earth_engine,
)


class MockSecrets(dict):
    """Mock for streamlit.secrets dictionary."""
    pass


def test_get_configured_project_id_precedence(monkeypatch):
    """Test resolution priority: explicit -> st.secrets -> env var -> service account."""
    # 1. Explicit argument has highest priority
    with patch("gee.auth._get_streamlit_secret", return_value="secret-proj"):
        monkeypatch.setenv("EE_PROJECT_ID", "env-proj")
        assert get_configured_project_id("explicit-proj") == "explicit-proj"

    # 2. st.secrets has priority over env var
    with patch("gee.auth._get_streamlit_secret", return_value="secret-proj"):
        monkeypatch.setenv("EE_PROJECT_ID", "env-proj")
        assert get_configured_project_id(None) == "secret-proj"

    # 3. env var used when st.secrets absent
    with patch("gee.auth._get_streamlit_secret", return_value=None):
        monkeypatch.setenv("EE_PROJECT_ID", "env-proj")
        assert get_configured_project_id(None) == "env-proj"

    # 4. Service account project_id used when env var absent
    monkeypatch.delenv("EE_PROJECT_ID", raising=False)
    with patch("gee.auth._get_streamlit_secret", return_value=None):
        with patch("gee.auth._get_service_account_info", return_value={"project_id": "sa-proj"}):
            with patch("gee.auth.GEE_PROJECT_ID", ""):
                assert get_configured_project_id(None) == "sa-proj"


def test_service_account_dict_initialization():
    """Verify initialization when service account is configured as a Streamlit TOML table/dict."""
    sa_dict = {
        "type": "service_account",
        "project_id": "ee-cloud-project",
        "client_email": "swayamyan-sa@ee-cloud-project.iam.gserviceaccount.com",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIB...\n-----END PRIVATE KEY-----",
    }

    mock_creds = MagicMock()
    with patch("gee.auth._get_streamlit_secret", side_effect=lambda k, default=None: sa_dict if k == "EARTH_ENGINE_SERVICE_ACCOUNT" else default):
        with patch("ee.ServiceAccountCredentials", return_value=mock_creds) as mock_sa_ctor:
            with patch("ee.Initialize") as mock_init:
                res = initialize_earth_engine()
                assert res is not None
                mock_sa_ctor.assert_called_once()
                call_kwargs = mock_sa_ctor.call_args[1]
                assert call_kwargs["email"] == sa_dict["client_email"]
                assert json.loads(call_kwargs["key_data"])["client_email"] == sa_dict["client_email"]
                mock_init.assert_called_once_with(credentials=mock_creds, project="ee-cloud-project")


def test_service_account_json_string_initialization():
    """Verify initialization when service account is provided as a JSON string."""
    sa_dict = {
        "type": "service_account",
        "project_id": "ee-json-project",
        "client_email": "json-sa@ee-json-project.iam.gserviceaccount.com",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIB...\n-----END PRIVATE KEY-----",
    }
    json_str = json.dumps(sa_dict)

    mock_creds = MagicMock()
    with patch("gee.auth._get_streamlit_secret", side_effect=lambda k, default=None: json_str if k == "EE_SERVICE_ACCOUNT_JSON" else default):
        with patch("ee.ServiceAccountCredentials", return_value=mock_creds):
            with patch("ee.Initialize") as mock_init:
                res = initialize_earth_engine()
                assert res is not None
                mock_init.assert_called_once_with(credentials=mock_creds, project="ee-json-project")


def test_local_oauth_fallback_when_service_account_absent(monkeypatch):
    """When no service account secret is present, fall back to local OAuth credentials."""
    monkeypatch.setenv("EE_PROJECT_ID", "local-dev-project")
    with patch("gee.auth._get_service_account_info", return_value=None):
        with patch("ee.Initialize") as mock_init:
            res = initialize_earth_engine()
            assert res is not None
            # Called with project but without service account credentials
            mock_init.assert_called_once_with(project="local-dev-project")


def test_missing_required_service_account_fields():
    """Service account without client_email or private_key raises actionable RuntimeError."""
    incomplete_sa = {"project_id": "proj", "type": "service_account"}
    with patch("gee.auth._get_service_account_info", return_value=incomplete_sa):
        with pytest.raises(RuntimeError, match="missing required 'client_email' or 'private_key'"):
            initialize_earth_engine()


def test_invalid_credentials_redacts_private_key():
    """Ensure sensitive private key material is never leaked in exception messages."""
    secret_key_material = "SECRET_PRIVATE_KEY_PAYLOAD_ABC123"
    sa_dict = {
        "client_email": "test@example.com",
        "private_key": f"-----BEGIN PRIVATE KEY-----\n{secret_key_material}\n-----END PRIVATE KEY-----",
    }

    def faulty_sa_ctor(*args, **kwargs):
        raise ValueError(f"Invalid key data containing {secret_key_material} and {kwargs.get('key_data')}")

    with patch("gee.auth._get_service_account_info", return_value=sa_dict):
        with patch("ee.ServiceAccountCredentials", side_effect=faulty_sa_ctor):
            with pytest.raises(RuntimeError) as exc_info:
                initialize_earth_engine()
            err_msg = str(exc_info.value)
            assert secret_key_material not in err_msg
            assert "BEGIN PRIVATE KEY" not in err_msg


def test_missing_configuration_error_message(monkeypatch):
    """When neither service account nor local OAuth is available, error provides clear instructions."""
    monkeypatch.delenv("EE_PROJECT_ID", raising=False)
    with patch("gee.auth._get_service_account_info", return_value=None):
        with patch("gee.auth.GEE_PROJECT_ID", ""):
            with patch("ee.Initialize", side_effect=Exception("No persistent credentials")):
                with pytest.raises(RuntimeError) as exc_info:
                    initialize_earth_engine()
                err_text = str(exc_info.value)
                assert "earthengine authenticate" in err_text
                assert "EARTH_ENGINE_SERVICE_ACCOUNT" in err_text
                assert "Streamlit Community Cloud" in err_text
