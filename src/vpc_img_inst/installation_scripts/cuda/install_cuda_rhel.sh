#!/bin/bash
#RHEL8 CUDA 
sudo dnf install kernel-devel-$(uname -r) kernel-headers-$(uname -r) -y

sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm

sudo subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
sudo subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
sudo subscription-manager repos --enable=codeready-builder-for-rhel-8-x86_64-rpms 

sudo rpm --erase gpg-pubkey-7fa2af80*

export distro="rhel8"
export arch="x86_64"
sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/$distro/$arch/cuda-$distro.repo
sudo dnf clean expire-cache

sudo dnf module install nvidia-driver:latest-dkms -y
sudo dnf install cuda -y
sudo systemctl enable nvidia-persistenced

file="/etc/profile.d/cuda-exports.sh"
sudo sh -c "cat<<EOF > $file
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
export CUDA_HOME=/usr/local/cuda
EOF"