#!/bin/bash
apt update && apt install python3.8 -y && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.8 get-pip.py
test -d ~/.venv || (pip install virtualenv && virtualenv -p /usr/bin/python3.8 ~/.venv && echo source ~/.venv/bin/activate >> ~/.bashrc &&  echo "source ~/.venv/bin/activate" | cat - ~/.bashrc | tee ~/.bashrc)
source ~/.venv/bin/activate
pip install ibm-vpc ibm_platform_services ibm_cloud_sdk_core 
pip install -U ibm-vpc-ray-connector
apt install libgl1-mesa-glx -y && pip install pandas tabulate gym tensorboardX dm_tree opencv-python transformers torch
echo alias python=\'python3\'>>~/.bash_aliases
pip install "ray[default]" "ray[serve]"