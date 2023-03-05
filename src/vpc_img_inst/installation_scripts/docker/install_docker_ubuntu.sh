#!/bin/bash
# Ubuntu22: config the needrestart to restart services automatically instead of in interactive mode.
# disable the unattended-upgrades process to avoid interruption by automatic upgrades. 
# kills the process holding the lock on the dpkg frontend, if such process exists.
[[ -f /etc/needrestart/needrestart.conf ]] && sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
sudo systemctl stop unattended-upgrades || true;
sudo systemctl disable unattended-upgrades || true;
sudo sed -i 's/Unattended-Upgrade "1"/Unattended-Upgrade "0"/g' /etc/apt/apt.conf.d/20auto-upgrades || true;
sudo kill -9 `sudo lsof /var/lib/dpkg/lock-frontend | awk '{print $2}'| tail -n 1` 2>/dev/null || true;

sudo apt-get update
sudo apt-get -y install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin