# AIPresence — Local Add-on Installation

## Prerequisites

- A running Home Assistant instance (**HA OS** or **HA Supervised** only —
  local add-ons are not supported on HA Container)
- SSH or file-system access to the HA host
- The **Samba share** or **SSH** add-on installed (for copying files)

## Installation

### 1. Copy the repository to your HA instance

Clone or copy this entire repository into the HA local add-ons directory:

```bash
# SSH into your HA host, then:
cd /addons
git clone https://github.com/MHentschke/aipresence.git aipresence
```

Alternatively, download the repository as a ZIP, extract it, and copy the
contents into `/addons/aipresence/` using the Samba share.

The resulting directory should look like:

```
/addons/aipresence/
├── config.yaml
├── Dockerfile
├── run.sh
├── backend/
├── client/
└── ...
```

### 2. Install the add-on

1. Open your Home Assistant UI.
2. Go to **Settings → Add-ons**.
3. Click the **Add-on Store** button (bottom right).
4. In the top-right overflow menu (⋮), select **Check for updates** to make
   the Supervisor rescan local add-ons.
5. Scroll down to the **Local add-ons** section. You should see
   **AIPresence** listed.
6. Click **AIPresence**, then click **Install**. The Supervisor will build the
   Docker image — this takes a few minutes on the first run.
7. After installation, click **Start**.

The AIPresence UI will appear in the HA sidebar under **AIPresence**.

## Configuration Options

After installing, go to the add-on's **Configuration** tab to adjust settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `sample_rate` | float | `2.0` | How often (in seconds) the data gatherer samples BLE signals during training and prediction. |
| `minimum_training_samples` | int | `200` | Minimum number of recorded samples required before a device model can be trained. |
| `log_level` | enum | `INFO` | Logging verbosity. One of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |

Changes take effect after restarting the add-on.

## Updating

To update to a newer version, pull the latest code and rebuild:

```bash
cd /addons/aipresence
git pull
```

Then go to **Settings → Add-ons → AIPresence** and click **Rebuild**.

## Data Persistence

The add-on stores its data (SQLite database, trained models, training CSVs) in
`/data` inside the container, which the Supervisor maps to persistent storage.
Your data survives add-on restarts and rebuilds.

## Troubleshooting

### Add-on not showing in the store

If AIPresence doesn't appear under **Local add-ons** after copying the files:

1. **Check your HA installation type.** Go to **Settings → System → Repairs →
   ⋮ → System Information**. Local add-ons only work on **Home Assistant OS**
   and **Home Assistant Supervised**. If you're running **HA Container**, you
   need to add a custom repository URL instead.

2. **Verify the directory structure.** SSH into the host and run:
   ```bash
   ls /addons/aipresence/config.yaml
   ```
   That file must exist at exactly that path. A common mistake when cloning is
   ending up with a nested directory like `/addons/aipresence/aipresence/` —
   make sure `config.yaml` is directly inside `/addons/aipresence/`.

3. **Force a rescan.** In the Add-on Store, open the overflow menu (⋮) in the
   top-right corner and select **Check for updates**. Alternatively, restart
   the Supervisor: **Settings → System → ⋮ → Restart Supervisor**.

4. **Check Supervisor logs.** Go to **Settings → System → Logs**, select
   **Supervisor** from the dropdown, and look for errors related to add-on
   discovery or `config.yaml` parsing.

---

# AIPresence — HA Integration Installation

The AIPresence **integration** exposes prediction results as native HA entities
(`device_tracker.*`, room sensors, confidence sensors) and provides a BLE proxy
scanner for ESP32 Bluetooth proxies. It is separate from the add-on above —
the add-on runs the backend, the integration connects HA to it.

## Option A: Install via HACS (recommended)

1. Open HACS in your Home Assistant UI.
2. Go to **Integrations**.
3. Click the overflow menu (⋮) in the top-right and select
   **Custom repositories**.
4. Enter the repository URL:
   ```
   https://github.com/MHentschke/aipresence
   ```
   Select **Integration** as the category, then click **Add**.
5. Search for **AIPresence** in the HACS integration list and click
   **Download**.
6. Restart Home Assistant.
7. Go to **Settings → Devices & Services → Add Integration**, search for
   **AIPresence**, and follow the config flow.

## Option B: Manual installation

1. Download or clone this repository.
2. Copy the `custom_components/aipresence/` directory into your Home Assistant
   `config/custom_components/` folder:
   ```
   <ha-config>/
   └── custom_components/
       └── aipresence/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── device_tracker.py
           ├── sensor.py
           ├── scanner.py
           ├── strings.json
           └── translations/
               └── en.json
   ```
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration**, search for
   **AIPresence**, and follow the config flow.
