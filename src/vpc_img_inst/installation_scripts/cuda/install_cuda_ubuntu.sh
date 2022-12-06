#!/bin/bash
#Ubuntu 20.04 CUDA 
apt-get install linux-headers-$(uname -r) gcc -y 
apt-key del 7fa2af80
export distro="ubuntu2004"
export arch="x86_64"
wget https://developer.download.nvidia.com/compute/cuda/repos/$distro/$arch/cuda-keyring_1.0-1_all.deb
dpkg -i cuda-keyring_1.0-1_all.deb
apt-get update 
apt-get install cuda -y
apt-get install cuda-drivers-520
systemctl enable nvidia-persistenced
file="/etc/profile.d/cuda-exports.sh"
cat<<EOF > $file
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
export CUDA_HOME=/usr/local/cuda
EOF



