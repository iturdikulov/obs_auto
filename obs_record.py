#!/bin/sh
# Use interpreter relative to the script path, https://stackoverflow.com/a/57567228
"true" '''\'
exec "$(dirname "$(readlink -f "$0")")"/.venv/bin/python "$0" "$@"
'''  # fmt: skip

import argparse
import os
import subprocess
import logging
import configparser
import sys
from time import sleep, time
from tkinter.font import Font
import psutil

import obsws_python as obs
import tkinter as tk  # <-- Tkinter import


def process_running(name: str) -> bool:
    """Check if a process with the given name is already running."""
    for proc in psutil.process_iter(["name"]):
        if name == proc.info["name"].lower():
            return True
    return False


def ensure_process_running(cmd: str) -> None:
    """Start a process if it isn’t already running."""
    process_name = os.path.basename(cmd)
    if process_running(process_name):
        return
    subprocess.Popen(cmd, shell=True)


def load_config(config_file: str = "config.ini") -> configparser.ConfigParser:
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    # Validate config
    required = {
        "DEFAULT": ["ObsPath"],
        "connection": ["host", "port", "password", "timeout"],
    }

    for section, keys in required.items():
        if section not in config:
            raise ValueError(f"Missing section in config file: [{section}]")
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing key '{key}' in section [{section}]")

    return config


class ObsRecord:
    def __init__(self, config: configparser.RawConfigParser):
        """
        Initialize OBS recording class
        """
        ensure_process_running(config["DEFAULT"]["ObsPath"])
        self.CONNECTION = config["connection"]
        self.TIMEOUT = float(self.CONNECTION["timeout"])
        self.client = self.get_client()

    def get_client(self):
        # In some reason timeout not working correctly if OBS isn't running
        # so let's implement it manually
        start = time()
        while time() - start < self.TIMEOUT:
            try:
                return obs.ReqClient(
                    host=self.CONNECTION["host"],
                    port=self.CONNECTION["port"],
                    password=self.CONNECTION["password"],
                    timeout=self.TIMEOUT,
                )
            except ConnectionRefusedError:
                sleep(0.5)
                continue

        raise Exception(
            f"OBS client is not initialized in timeout: {self.TIMEOUT}"
        )

    def record(self, filename: str):
        """
        Start recording with provided filename
        """

        self.client.set_profile_parameter(
            "Output", "FilenameFormatting", filename
        )
        self.client.start_record()


# ---------------------------------------------------------------------------


class ParametresForm:
    """
    Simple Tkinter form that asks for a filename and starts recording.
    """

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.root = tk.Tk()
        self.root.title("Get Filename")
        font = Font(size=int(config["DEFAULT"]["FontSize"]))

        # Label
        self.label = tk.Label(
            self.root,
            text="Enter filename or browse (press Enter to confirm):",
            font=font,
        )
        self.label.pack(padx=10, pady=(10, 5))

        # Entry field
        self.input = tk.Entry(self.root, width=50, font=font)
        self.input.pack(padx=10, pady=(0, 10))
        self.input.bind("<Return>", self._on_enter)

        # Make the entry field the active widget
        self.input.focus_set()

        # Create OBS client
        self.obs = ObsRecord(self.config)

    def _on_enter(self, event=None):
        """Called when the user presses <Return> in the entry field."""
        filename = self.input.get().strip()
        if filename:
            self.obs.record(filename)
            self.root.destroy()

    def mainloop(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = load_config()

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="record")
    args = parser.parse_args()

    if args.mode == "stop":
        OBS_PATH = config["DEFAULT"]["ObsPath"]
        PLAYER = config["DEFAULT"]["PlayerPath"]
        CONNECTION = config["connection"]
        TIMEOUT = float(CONNECTION["timeout"])
        PLAY_DELAY = float(config["DEFAULT"]["PlayDelay"])

        try:
            client = obs.ReqClient(
                host=CONNECTION["host"],
                port=CONNECTION["port"],
                password=CONNECTION["password"],
                timeout=TIMEOUT,
            )
            record_status = client.get_record_status()
            if record_status.output_active:
                response = client.stop_record()
                if response.output_path:
                    sleep(PLAY_DELAY)  # give time for file to save properly
                    subprocess.Popen(
                        f"{PLAYER} {response.output_path}", shell=True
                    )
                    logger.info(f"{PLAYER} {response.output_path}")
        except ConnectionRefusedError:
            sys.exit()
    else:
        form = ParametresForm(config)
        form.mainloop()
        sys.exit(0)
