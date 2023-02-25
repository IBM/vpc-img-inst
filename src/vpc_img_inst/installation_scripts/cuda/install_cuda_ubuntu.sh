#!/bin/bash
# if running on ubuntu22 config the needrestart to restart services automatically instead of interactive mode
[[ -f /etc/needrestart/needrestart.conf ]] && sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
sudo apt-get install linux-headers-$(uname -r) gcc -y 
sudo apt-key del 7fa2af80
# extract ubuntu release version and parse the required format of: <OS><VERSION_ID_DIGITS_ONLY>, e.g. 'ubuntu2204'. 
export distro="ubuntu$(awk -F'=' '/^VERSION_ID/ {print $2}' /etc/os-release | tr -d '[".]')"
export arch="x86_64"
wget https://developer.download.nvidia.com/compute/cuda/repos/$distro/$arch/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update 
sudo apt-get install cuda -y
sudo apt-get install cuda-drivers-520 -y
sudo systemctl enable nvidia-persistenced

file="/etc/profile.d/cuda-exports.sh"
sudo sh -c "cat<<EOF > $file
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
export CUDA_HOME=/usr/local/cuda
EOF"