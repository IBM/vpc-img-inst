#!/bin/bash
#Ubuntu 20.04 CUDA 
sudo apt-get install linux-headers-$(uname -r) gcc -y 
sudo apt-key del 7fa2af80
export distro="ubuntu2004"
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