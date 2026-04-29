# AIPresence — Local Add-on Installation

## Prerequisites

- A running Home Assistant instance (HA OS, HA Supervised, or HA Container)
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
