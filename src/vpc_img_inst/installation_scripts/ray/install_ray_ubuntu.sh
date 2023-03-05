#!/bin/bash
# Ubuntu22: config the needrestart to restart services automatically instead of in interactive mode.
# disable the unattended-upgrades process to avoid interruption by automatic upgrades. 
# kills the process holding the lock on the dpkg frontend, if such process exists.
[[ -f /etc/needrestart/needrestart.conf ]] && sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf;
sudo systemctl stop unattended-upgrades || true;
sudo systemctl disable unattended-upgrades || true;
sudo sed -i 's/Unattended-Upgrade "1"/Unattended-Upgrade "0"/g' /etc/apt/apt.conf.d/20auto-upgrades || true;
sudo kill -9 `sudo lsof /var/lib/dpkg/lock-frontend | awk '{print $2}'| tail -n 1` 2>/dev/null || true;
sudo apt update && sudo apt install python3-pip -y
test -d ~/.venv || (pip install virtualenv && virtualenv -p /usr/bin/python3 ~/.venv && echo source ~/.venv/bin/activate >> ~/.bashrc &&  echo "source ~/.venv/bin/activate" | cat - ~/.bashrc | tee ~/.bashrc)
source ~/.venv/bin/activate
pip install ibm-vpc ibm_platform_services ibm_cloud_sdk_core 
pip install -U ibm-vpc-ray-connector
sudo apt install libgl1-mesa-glx -y && pip install pandas tabulate gym tensorboardX dm_tree opencv-python transformers torch
echo alias python=\'python3\'>>~/.bash_aliases
pip install "ray[default]" "ray[serve]"