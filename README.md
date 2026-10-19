# SWAYAMYAN — Multi-Satellite Earth Observation Analytics

SWAYAMYAN is an operational Earth Observation (EO) analytics and **feature-level fusion** platform powered by Streamlit and Google Earth Engine. It enables reproducible multi-satellite time-series extraction, cross-sensor temporal lead/lag diagnostics, and transparent equal-weight composite generation over user-defined Areas of Interest (AOIs).

A core design principle of SWAYAMYAN is **scientific integrity**: the platform strictly queries real, cloud-filtered satellite observations directly from Google Earth Engine and preserves missing dates as `NaN`. It **never substitutes mock or synthetic values** when data is unavailable.

---

## Key Features & Workflow

The analytical workspace follows a guided 4-step scientific workflow:

1. **Step 01 — Configure Study & AOI**
   - Interactive bounding box selection with live map preview (supporting custom coordinates or presets such as New Delhi and Amazon Basin).
   - Date range selection (up to 3 years) with automatic exclusive end-date handling for Earth Engine filters.
   - Scene-level optical cloud cover thresholding for Sentinel-2.
   - **Sentinel-1 SAR Orbit Pass Selection:** Explicit choice of Descending (morning, recommended for consistent geometry), Ascending (evening), or Both, with automated fallback if scenes are absent.
   - Temporal aggregation options: **Monthly** calendar regularization or native acquisition cadence.

2. **Step 02 — Explore Observations & Sensor Coverage**
   - Summary telemetry: total time steps, usable features, sensors successfully ingested, and scenes queried.
   - Sensor coverage breakdown table detailing scenes ingested, valid observations, and status (`Active` vs. `Empty / No Data`).
   - Prominent warnings for any dataset returning zero valid regional observations.
   - Interactive Plotly time-series inspection per feature.
   - Live Sentinel-2 satellite true-color/RGB map visualization with tile layer integration.

3. **Step 03 — Cross-Sensor Lag Analysis**
   - Dynamic selection of driver feature ($X$) and response feature ($Y$).
   - Rigorous **calendar-month lag correlation** operating across an integer search window $[-k, +k]$ months.
   - Preserves missing calendar months as `NaN` to guarantee that lag $k$ strictly equals $k$ calendar months (not compressed sample indices).
   - Peak correlation detection with tie-breaking that favors the most parsimonious lag closest to zero.
   - Lead/lag direction reporting ($Y$ follows $X$ for positive lag, leads $X$ for negative lag, or is synchronous).

4. **Step 04 — Feature-Level Fusion & Composite Generation**
   - Evaluates multi-satellite fusion readiness using peak correlation, peak lag, and rolling-window correlation stability (coefficient of variation).
   - Automated scientist recommendation guidance based on statistical criteria.
   - Calendar-aligned feature-level fusion: shifts the candidate feature by the detected peak lag and normalizes both features to zero mean and unit variance ($z$-scores with population standard deviation).
   - Transparent, non-predictive equal-weight composite signal generation ($0.5 \cdot X_z + 0.5 \cdot Y_z$).
   - Export fused time-series observations to CSV.

---

## Supported Datasets & Collections

| Sensor / Mission | Collection ID | Extracted Features & Bands | Processing & Quality Filters | Native Resolution |
|---|---|---|---|---|
| **Sentinel-2 SR Harmonized** | `COPERNICUS/S2_SR_HARMONIZED` | NDVI, NDWI (Green-NIR), EVI | SCL cloud/shadow scene classification masking; scale factor $0.0001$ | 10–20 m |
| **Sentinel-1 GRD** | `COPERNICUS/S1_GRD` | S1_VV_dB, S1_VH_dB | Interferometric Wide (IW), dual-pol VV/VH, dB backscatter; orbit pass filtering (Descending/Ascending) | 10 m (extracted at 20 m) |
| **MODIS Terra LST** | `MODIS/061/MOD11A2` | Daytime LST (°C), Nighttime LST (°C) | 8-day composite, QC bitmask filtering, scale factor $0.02$, Kelvin to Celsius conversion | 1,000 m |
| **Landsat 8/9 C2 L2** | `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` | NDVI, NDWI, EVI, Surface Temp (°C) | Collection 2 Level-2 Surface Reflectance, QA_PIXEL cloud/shadow masking, ST_B10 thermal scaling | 30 m |
| **GPM IMERG V07** | `NASA/GPM_L3/IMERG_V07` | Precipitation (mm) | Daily/monthly precipitation accumulation (summed, preserving physical rainfall mass) | ~11.1 km (0.1°) |

---

## System Architecture & Repository Layout

```
swamayansatellite-main/
├── app.py                      # Application entry point, routing, and GEE query caching
├── requirements.txt            # Python package dependencies
├── runtime.txt                 # Target Python runtime specification (3.10 / 3.11)
├── .gitignore                  # Git exclusion rules for venv, secrets, and caches
├── .streamlit/
│   └── config.toml             # Streamlit server and theme configuration
├── analytics/                  # Core scientific computation engine
│   ├── fusion.py               # Feature-level lag alignment & z-score composite generation
│   ├── fusion_readiness.py     # Stability score, peak lag detection & scientist recommendation
│   ├── lag_analysis.py         # Lagged Pearson cross-correlation with sign conventions
│   ├── preprocessing.py        # Calendar-grid regularization & feature merging
│   └── timeseries.py           # Region-reduction & Earth Engine time-series extraction
├── config/                     # Application settings and default project constants
│   ├── constants.py            # Earth Engine collection IDs, scales, and palettes
│   └── settings.py             # Feature and band definitions
├── gee/                        # Earth Engine collection loaders and mask pipelines
│   ├── auth.py                 # Earth Engine initialization & actionable auth error handling
│   ├── datasets.py             # Sentinel-2 & GPM loader implementations
│   ├── indices.py              # Normalized difference and spectral index math
│   ├── landsat.py              # Landsat 8/9 Collection 2 QA bitmasking & scaling
│   ├── modis.py                # MODIS MOD11A2 QC bitmasking & temperature calibration
│   └── sentinel1.py            # Sentinel-1 SAR dual-pol filtering & orbit pass handling
├── ui/                         # Streamlit user interface components
│   ├── charts.py               # Plotly interactive time-series & correlation charts
│   ├── globe.py                # Interactive 3D Cesium/Three-style globe visualization
│   ├── landing.py              # Modern landing page & verified observation preview
│   ├── maps.py                 # Folium & Geemap AOI preview and live true-color layer
│   ├── styles.py               # Central CSS token design system (teal, dark, glassmorphism)
│   └── workspace.py            # 4-step analytical workspace views
├── scripts/                    # Standalone verification and diagnostic utilities
│   ├── check_earth_engine_auth.py
│   ├── check_earth_engine_datasets.py
│   └── check_earth_engine_map.py
└── tests/                      # Automated test suite
    ├── test_analytics.py       # Pure-Python unit tests for lag, calendar grid, & fusion
    └── test_earth_engine_integration.py # Live Earth Engine connectivity integration test
```

---

## Installation & Local Setup

### Prerequisites
* **Python 3.10+** (Python 3.11 recommended)
* A registered **Google Cloud Project** with the Earth Engine API enabled
* A Google account with Earth Engine access

### 1. Clone & Set Up Virtual Environment

**Windows PowerShell:**
```powershell
cd path\to\swamayansatellite-main
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
cd path/to/swamayansatellite-main
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Authenticate Earth Engine

Authenticate once on your workstation:
```bash
earthengine authenticate
```
This generates credentials saved to your local user profile (`~/.config/earthengine/credentials`).

### 3. Run the Application

Set your Google Cloud project ID and launch Streamlit:

**Windows PowerShell:**
```powershell
$env:EE_PROJECT_ID = "your-earth-engine-cloud-project-id"
python -m streamlit run app.py
```

**macOS / Linux:**
```bash
export EE_PROJECT_ID="your-earth-engine-cloud-project-id"
python -m streamlit run app.py
```

Access the UI at `http://localhost:8501`.

---

## Testing

The test suite contains both pure-Python unit tests (which run offline without credentials) and live Earth Engine integration tests.

### Running Offline Unit Tests
```bash
python -m pytest tests/test_analytics.py -v
```
Validates:
* Preservation of calendar-month semantics with missing data gaps (`np.nan`).
* Lead/lag sign conventions (positive: $Y$ follows $X$; negative: $Y$ leads $X$).
* Peak lag tie-breaking preferring zero lag.
* Standardized feature-level composite generation and variance checks.
* Precipitation summation vs. continuous feature averaging.

### Running Live Earth Engine Integration Tests
Set the environment variable `SWAYAMYAN_RUN_EE_INTEGRATION=1` after authenticating:

**Windows PowerShell:**
```powershell
$env:SWAYAMYAN_RUN_EE_INTEGRATION = "1"
python -m pytest tests/ -v
```

---

## Deployment Guidelines

### 1. Streamlit Community Cloud Deployment

SWAYAMYAN is configured for one-click deployment on **Streamlit Community Cloud**:

1. **Repository Settings:** Connect your GitHub repository (`main` branch) with `app.py` as the entry point.
2. **Configure App Secrets:** In the Streamlit Cloud dashboard, navigate to **App Settings -> Secrets** and paste your configuration following the template in [`.streamlit/secrets.example.toml`](file:///.streamlit/secrets.example.toml):

```toml
# Google Cloud Project registered for Earth Engine
EE_PROJECT_ID = "your-earth-engine-cloud-project-id"

# Dedicated Service Account Credentials
[EARTH_ENGINE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "your-earth-engine-cloud-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "swayamyan-ee-sa@your-project-id.iam.gserviceaccount.com"
client_id = "123456789012345678901"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/swayamyan-ee-sa%40your-project-id.iam.gserviceaccount.com"
```

> **Security Note:** Real service account keys and secrets must only be entered into Streamlit Cloud Secrets or local `.streamlit/secrets.toml`. Never commit real private keys to GitHub. `.streamlit/secrets.toml` is strictly ignored by `.gitignore`.

### 2. Google Cloud Run Deployment (Keyless via Application Default Credentials)

SWAYAMYAN supports **100% keyless deployment** on Google Cloud Run using Application Default Credentials (ADC). No service-account JSON private keys are required, complying with Google Cloud organization policies that restrict service-account key creation.

#### Steps to Deploy on Cloud Run:

1. **Create/Identify Runtime Service Account:**
   Create a dedicated service account for the Cloud Run service (or use an existing one):
   ```bash
   gcloud iam service-accounts create swayamyan-runner \
       --description="Cloud Run runtime identity for SWAYAMYAN" \
       --display-name="SWAYAMYAN Runner"
   ```

2. **Grant Earth Engine & Project Permissions:**
   Assign Earth Engine access and Project Viewer to the runtime service account:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:swayamyan-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/earthengine.reader"

   # Ensure the Google Earth Engine API is enabled
   gcloud services enable earthengine.googleapis.com
   ```

3. **Deploy from Source:**
   Build and deploy directly using Cloud Build and Cloud Run with the included production `Dockerfile`:
   ```bash
   gcloud run deploy swayamyan \
       --source . \
       --region us-central1 \
       --service-account swayamyan-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com \
       --set-env-vars EE_PROJECT_ID="YOUR_PROJECT_ID" \
       --allow-unauthenticated
   ```
   Cloud Run automatically provides the `PORT` environment variable (default 8080), which the container's entrypoint binds to `0.0.0.0`.

#### Running Locally with Docker:
```bash
# Build the container
docker build -t swayamyan:latest .

# Run locally with ADC mounted or local OAuth
docker run -p 8080:8080 \
    -e EE_PROJECT_ID="your-project-id" \
    -v ~/.config/gcloud:/home/appuser/.config/gcloud:ro \
    swayamyan:latest
```

