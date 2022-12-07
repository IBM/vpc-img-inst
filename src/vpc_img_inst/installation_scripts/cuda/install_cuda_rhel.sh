#!/bin/bash
#RHEL8 CUDA 
dnf install kernel-devel-$(uname -r) kernel-headers-$(uname -r) -y

dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm

subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
subscription-manager repos --enable=codeready-builder-for-rhel-8-x86_64-rpms 

rpm --erase gpg-pubkey-7fa2af80*

export distro="rhel8"
export arch="x86_64"
dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/$distro/$arch/cuda-$distro.repo
dnf clean expire-cache

dnf module install nvidia-driver:latest-dkms -y
dnf install cuda -y
systemctl enable nvidia-persistenced

file="/etc/profile.d/cuda-exports.sh"
cat<<EOF > $file
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
export CUDA_HOME=/usr/local/cuda
EOF




