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
    is_cloud_run,
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
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("K_REVISION", raising=False)
    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    monkeypatch.delenv("USE_GCP_ADC", raising=False)
    with patch("gee.auth._get_service_account_info", return_value=None):
        with patch("gee.auth.GEE_PROJECT_ID", ""):
            with patch("ee.Initialize", side_effect=Exception("No persistent credentials")):
                with pytest.raises(RuntimeError) as exc_info:
                    initialize_earth_engine()
                err_text = str(exc_info.value)
                assert "earthengine authenticate" in err_text
                assert "EARTH_ENGINE_SERVICE_ACCOUNT" in err_text
                assert "Cloud Run" in err_text
                assert "Streamlit Community Cloud" in err_text


def test_is_cloud_run_detection(monkeypatch):
    """Verify is_cloud_run returns True when Cloud Run environment variables are present."""
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("K_REVISION", raising=False)
    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    assert not is_cloud_run()

    monkeypatch.setenv("K_SERVICE", "swayamyan-service")
    assert is_cloud_run()

    monkeypatch.delenv("K_SERVICE")
    monkeypatch.setenv("K_REVISION", "swayamyan-rev-001")
    assert is_cloud_run()

    monkeypatch.delenv("K_REVISION")
    monkeypatch.setenv("CLOUD_RUN_JOB", "swayamyan-job")
    assert is_cloud_run()


def test_get_configured_project_id_cloud_run(monkeypatch):
    """Verify project ID resolution from GOOGLE_CLOUD_PROJECT and GCP_PROJECT."""
    monkeypatch.delenv("EE_PROJECT_ID", raising=False)
    with patch("gee.auth._get_streamlit_secret", return_value=None):
        with patch("gee.auth._get_service_account_info", return_value=None):
            with patch("gee.auth.GEE_PROJECT_ID", ""):
                monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "cloud-run-project-123")
                assert get_configured_project_id() == "cloud-run-project-123"

                monkeypatch.delenv("GOOGLE_CLOUD_PROJECT")
                monkeypatch.setenv("GCP_PROJECT", "fallback-gcp-project")
                assert get_configured_project_id() == "fallback-gcp-project"


def test_cloud_run_adc_initialization(monkeypatch):
    """Verify keyless ADC initialization on Cloud Run with project and credentials."""
    monkeypatch.setenv("K_SERVICE", "swayamyan-app")
    monkeypatch.setenv("EE_PROJECT_ID", "cloud-run-ee-proj")

    mock_adc_creds = MagicMock(name="MockADCCredentials")
    with patch("gee.auth._get_service_account_info", return_value=None):
        with patch("google.auth.default", return_value=(mock_adc_creds, "default-adc-proj")) as mock_auth_default:
            with patch("ee.Initialize") as mock_init:
                res = initialize_earth_engine()
                assert res is not None
                mock_auth_default.assert_called_once()
                mock_init.assert_called_once_with(credentials=mock_adc_creds, project="cloud-run-ee-proj")


def test_cloud_run_adc_fallback_project(monkeypatch):
    """Verify Cloud Run ADC falls back to default_project from google.auth.default when EE_PROJECT_ID is unset."""
    monkeypatch.setenv("K_SERVICE", "swayamyan-app")
    monkeypatch.delenv("EE_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GCP_PROJECT", raising=False)

    mock_adc_creds = MagicMock(name="MockADCCredentials")
    with patch("gee.auth._get_streamlit_secret", return_value=None):
        with patch("gee.auth._get_service_account_info", return_value=None):
            with patch("gee.auth.GEE_PROJECT_ID", ""):
                with patch("google.auth.default", return_value=(mock_adc_creds, "adc-discovered-proj")):
                    with patch("ee.Initialize") as mock_init:
                        res = initialize_earth_engine()
                        assert res is not None
                        mock_init.assert_called_once_with(credentials=mock_adc_creds, project="adc-discovered-proj")


def test_cloud_run_adc_failure_raises_clear_error(monkeypatch):
    """Verify descriptive error when ADC initialization fails on Cloud Run."""
    monkeypatch.setenv("K_SERVICE", "swayamyan-app")
    monkeypatch.setenv("EE_PROJECT_ID", "cloud-run-ee-proj")

    with patch("gee.auth._get_service_account_info", return_value=None):
        with patch("google.auth.default", side_effect=Exception("Metadata server unavailable")):
            with pytest.raises(RuntimeError) as exc_info:
                initialize_earth_engine()
            err_msg = str(exc_info.value)
            assert "Application Default Credentials (ADC) initialization failed on Cloud Run" in err_msg
            assert "Earth Engine Resource User" in err_msg
            assert "Metadata server unavailable" in err_msg


def test_local_oauth_fallback_to_adc(monkeypatch):
    """When local OAuth credentials are not found, falls back to local ADC if available."""
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("K_REVISION", raising=False)
    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    monkeypatch.delenv("USE_GCP_ADC", raising=False)
    monkeypatch.setenv("EE_PROJECT_ID", "dev-project")

    mock_adc_creds = MagicMock(name="LocalADCCreds")

    call_count = 0
    def mock_ee_init(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call without credentials (local OAuth) fails
            raise Exception("Please authorize access to Earth Engine")
        # Second call with ADC credentials succeeds
        return None

    with patch("gee.auth._get_service_account_info", return_value=None):
        with patch("google.auth.default", return_value=(mock_adc_creds, "dev-project")):
            with patch("ee.Initialize", side_effect=mock_ee_init) as mock_init:
                res = initialize_earth_engine()
                assert res is not None
                assert mock_init.call_count == 2
                assert mock_init.call_args[1] == {"credentials": mock_adc_creds, "project": "dev-project"}

