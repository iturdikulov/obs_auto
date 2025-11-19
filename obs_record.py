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
import psutil

import obsws_python as obs

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QLabel,
)


def process_running(name: str):
    """
    Check if process with provided name is already running
    """
    for proc in psutil.process_iter(["name"]):
        if name == proc.info["name"].lower():
            return True
    return False

def ensure_process_running(cmd: str):
    """
    Ensure process is running, if not run
    """
    process_name = os.path.basename(cmd)
    if process_running(process_name):
        return

    subprocess.Popen(cmd, shell=True)


def load_config(config_file="config.ini"):
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    # Validate required sections and keys
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


class ParametresForm(QWidget):
    def __init__(self, config: configparser.ConfigParser):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel(
            "Enter filename or browse (press Enter to confirm):"
        )
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.save_and_close)

        layout.addWidget(self.label)
        layout.addWidget(self.input)

        self.setLayout(layout)
        self.setWindowTitle("Get Filename")
        self.show()

        # Run OBS
        self.obs = ObsRecord(self.config)
        self.activateWindow()

    def save_and_close(self):
        filename = self.input.text()
        self.obs.record(filename)
        self.close()


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
                    sleep(PLAY_DELAY) # give time for file to save properly
                    subprocess.Popen(f"{PLAYER} {response.output_path}", shell=True)
                    logger.info(f"{PLAYER} {response.output_path}")
        except ConnectionRefusedError:
            sys.exit()
    else:
        app = QApplication(sys.argv)
        form = ParametresForm(config)
        sys.exit(app.exec())
