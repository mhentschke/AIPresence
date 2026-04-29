# AIPresence

Room-level presence detection for Home Assistant using BLE signal classification.

AIPresence tracks devices (phones, tablets, BLE beacons) across rooms by collecting Bluetooth Low Energy signal data from Home Assistant, training a per-device machine learning model, and predicting which room each device is currently in.

## Features

- **Per-device ML models** — each tracked device gets its own RandomForestClassifier trained on BLE signal patterns specific to that device
- **Flexible device types** — devices can be BLE monitors (phones/tablets running a beacon scanner), BLE beacons (tags, wearables), or both simultaneously
- **Multiple monitor sources** — supports Android/iOS Companion App beacon monitors, fixed tablets, and ESPHome BLE proxies (via the companion HA integration)
- **Binary sensor features** — incorporate door/motion sensor states as additional ML features
- **Real-time predictions** — continuous room prediction with confidence scores after training
- **Web management UI** — React-based dashboard for managing rooms, monitors, devices, and training workflows
- **Home Assistant integration** — exposes `device_tracker` and sensor entities natively in HA
- **HA Add-on packaging** — runs as a supervised add-on with ingress UI access from the HA sidebar

## Installation

### Home Assistant Add-on

1. Add this repository as a custom add-on repository in Home Assistant:
   - Go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
   - Add: `https://github.com/MHentschke/aipresence`
2. Install the **AIPresence** add-on from the store
3. Start the add-on — the UI is accessible from the HA sidebar via ingress

The add-on automatically discovers the HA API URL and authentication token via the Supervisor.

### Home Assistant Integration (HACS)

The companion integration creates native HA entities for predictions and auto-discovers BLE proxy scanners.

1. Install [HACS](https://hacs.xyz/) if you haven't already
2. Add this repository as a custom repository in HACS (category: Integration)
3. Install **AIPresence** from HACS
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration → AIPresence**
6. The integration auto-discovers the add-on if running, or you can enter the backend URL manually

### Standalone / Development

See the [Contributing](#contributing) section below for running the backend and frontend locally.

## Usage

### 1. Set Up Rooms

Open the AIPresence UI and go to the **Rooms** tab. Add each room you want to track (e.g., Kitchen, Office, Bedroom). Assign a color to each room for visual identification.

### 2. Add Monitors

Go to the **Monitors** tab and add your fixed BLE scanning stations. These are HA sensor entities that report beacon distances as attributes — typically phones or tablets running the HA Companion App with beacon monitoring enabled (e.g., `sensor.tablet_beacon_monitor`).

If using the HA integration with ESPHome BLE proxies, scanner monitors are registered automatically.

### 3. Add Devices

Go to the **Devices** tab and add the devices you want to locate. Each device can have:
- An **Entity ID** — if the device is a BLE monitor (e.g., a phone running a beacon scanner)
- A **Beacon ID** — if the device advertises as a BLE beacon (iBeacon UUID/major/minor)
- Both — a phone can be both a monitor and a beacon simultaneously

### 4. Train

Click **Start Training** on a device. Select a room, then physically go to that room with the device. The system records BLE signal snapshots at ~2 Hz. Switch rooms as needed, then click **Done** to train the model.

The more rooms and samples you provide, the more accurate the predictions. The minimum is 200 samples per room by default (configurable).

### 5. View Predictions

After training, the device's predicted room and confidence score appear in the **Devices** table, updating in real time. If the HA integration is installed, predictions are also exposed as `device_tracker` and sensor entities.

## Project Structure

```
├── backend/                  # Python/FastAPI REST API
│   ├── main.py               # App entry point, lifespan, app-level routes
│   ├── classes.py            # Domain models (Device, Room, Model, etc.)
│   ├── schemas.py            # Pydantic request/response models
│   ├── config.py             # Settings (DATA_PATH, SAMPLE_RATE, etc.)
│   ├── datasource.py         # HA / Standalone data source abstraction
│   ├── dependencies.py       # FastAPI dependency injection
│   ├── routes/               # API route modules (devices, rooms, sensors, monitors)
│   ├── db/                   # SQLite persistence layer
│   └── tests/                # Backend test suite (pytest)
│
├── client/                   # React 18 SPA (Vite)
│   ├── src/
│   │   ├── App.jsx           # Root component
│   │   ├── Backend.js        # API client (static methods)
│   │   └── components/       # UI components (tables, modals, pickers)
│   └── package.json
│
├── custom_components/        # Home Assistant integration
│   └── aipresence/
│       ├── __init__.py       # Integration setup
│       ├── config_flow.py    # Config flow for HA UI setup
│       ├── coordinator.py    # Data update coordinator
│       ├── scanner.py        # BLE proxy scanner manager
│       ├── sensor.py         # Scanner sensor entities
│       ├── device_tracker.py # Device tracker entities
│       └── tests/            # Integration test suite
│
├── config.yaml               # HA Add-on manifest
├── Dockerfile                # Multi-stage build (frontend + backend)
├── run.sh                    # Add-on entrypoint script
└── hacs.json                 # HACS metadata
```

## Contributing

### Development Environment

Requirements:
- Python 3.13+
- Node.js 20+
- A running Home Assistant instance (optional — the backend can run in standalone mode)

### Running the Backend

```bash
# Create and activate a virtual environment
python -m venv backend/.venv
source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy the env template and fill in your HA details (optional)
cp backend/.env.example backend/.env
# Edit backend/.env with your HA_URL and HA_TOKEN, or leave them blank for standalone mode

# Run the backend
uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload
```

The API is available at `http://127.0.0.1:5000`.

### Running the Frontend

```bash
cd client
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies API calls to the backend at `127.0.0.1:5000`.

### Running Tests

Backend tests (pytest):

```bash
source backend/.venv/bin/activate
pytest
```

Frontend tests (vitest):

```bash
cd client
npm test
```

Integration tests:

```bash
pytest custom_components/aipresence/tests/
```

### Linting

```bash
# Python (ruff)
ruff check backend/ custom_components/

# Frontend (if eslint is configured)
cd client && npx eslint src/
```

## License

See [LICENSE](LICENSE) for details.
