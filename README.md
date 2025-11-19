# OBS Auto Recorder

A Python script to automate OBS Studio recording, allowing for quick,
hotkey-driven screen recordings. This tool is designed for users who frequently
record short clips and want to streamline their workflow.

## Why this tool is required

This script simplifies the process of settings filenames per recording.

## Features

- **Hotkey-driven recording:** Start and stop recordings with global hotkeys.
- **Customizable filenames:** Prompt for a human-readable filename before
  recording.
- **Automatic playback:** Instantly opens the recorded video after stopping.
- **OBS Studio integration:** Uses `obs-websocket` for seamless control.
- **Configurable:** Configurable paths for OBS and media player, and
  `obs-websocket` connection details via `config.ini`.

## Quickstart

### Prerequisites

- Python 3.12 or newer.
- OBS Studio installed and running.
- [obs-websocket](https://github.com/obsproject/obs-websocket) plugin installed
  for OBS Studio, you need to install it before using this script.
- `uv` is recommended for dependency management and project environments. If not
  installed, you can install it using `pip install uv`.
- The script is tested in Linux environment, in other OS it may require additional
  setup.

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/iturdikulov/obs_auto
cd obs_auto
```

2. **Install dependencies using `uv`:**

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Alternatively, if you do not use `uv`, you can attempt to use `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Configuration

Edit the `config.ini` file in the project, adjust values as per your setup:

**Important:** Make sure to enable the `obs-websocket` server in OBS Studio
(`Tools` -> `Websocket Server Settings`). If you use a password, configure one
in `config.ini`.

### Usage

The script is designed to be triggered by global hotkeys.

#### 1. Start Recording (and prompt for filename)

Run the script in its default mode:

```bash
./obs_record.py
# You can run it alternatively, useful for non-unix environment
PATH_TO_PROJECT/.venv/bin/python obs_record.py
```

This will ensure OBS is running, open a small window to ask for a filename, and
then start recording in OBS with the specified name.

#### 2. Stop Recording (and play video)

Run the script with the `--mode stop` argument:

```bash
python obs_record.py --mode stop
```

This will stop the current recording in OBS, save the file, and then open it
with your configured media player.

### Example Hotkey Setup (Linux - XFCE/KDE/Gnome)

You can bind these commands to global hotkeys in your desktop environment's
settings.

**Example for "Start Recording":** `cd PATH_TO_PROJECT && ./obs_record.py`, hotkey: `Meta + R`

**Example for "Stop Recording":** `cd PATH_TO_PROJECT && ./obs_record.py --mode=stop`, hotkey: `Meta + Shift + R`
