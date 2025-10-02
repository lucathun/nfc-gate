#!/bin/bash
set -e  # Script bei Fehler sofort abbrechen

# System-Pakete
sudo apt update
sudo apt install -y \
    python3-venv python3-pip \
    libpcsclite1 pcscd pcsc-tools \
    libgles2-mesa libgles2-mesa-dev libdrm-dev libgbm-dev \
    xserver-xorg xinit

# Python-Umgebung
python3 -m venv .venv
source .venv/bin/activate

# pip auf neuesten Stand bringen
pip install --upgrade pip setuptools wheel

# Python-Dependencies installieren
pip install -r requirements.txt
