#!/bin/bash
# if running on ubuntu22 config the needrestart to restart services automatically instead of interactive mode 
[[ -f /etc/needrestart/needrestart.conf ]] && sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
sudo apt update && sudo apt install python3-pip -y
test -d ~/.venv || (pip install virtualenv && virtualenv -p /usr/bin/python3 ~/.venv && echo source ~/.venv/bin/activate >> ~/.bashrc &&  echo "source ~/.venv/bin/activate" | cat - ~/.bashrc | tee ~/.bashrc)
source ~/.venv/bin/activate
pip install ibm-vpc ibm_platform_services ibm_cloud_sdk_core 
pip install -U ibm-vpc-ray-connector
sudo apt install libgl1-mesa-glx -y && pip install pandas tabulate gym tensorboardX dm_tree opencv-python transformers torch
echo alias python=\'python3\'>>~/.bash_aliases
pip install "ray[default]" "ray[serve]"