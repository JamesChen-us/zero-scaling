# Kubernetes Worker Node Setup Documentation

## Overview
This documentation covers the setup process for Kubernetes worker nodes. Worker nodes are responsible for running application workloads in the cluster.

## Prerequisites
- Ubuntu-based system (tested on Ubuntu 22.04)
- Root or sudo access
- Master node already configured and running
- Network connectivity to the master node

## Component Architecture
- **Docker**: Container runtime used by Kubernetes
- **cri-dockerd**: Interface between Docker and Kubernetes CRI
- **kubelet**: Primary node agent that runs pods
- **kubeadm**: Tool for joining the Kubernetes cluster

## Setup Process

### 1. Docker Installation
```bash
# Update system and install prerequisites
sudo apt-get update
sudo apt-get install ca-certificates curl

# Add Docker's official GPG key and repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. CRI-Docker Installation
```bash
# Download and install cri-dockerd
wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.15/cri-dockerd_0.3.15.3-0.ubuntu-focal_amd64.deb
sudo dpkg -i cri-dockerd_0.3.15.3-0.ubuntu-focal_amd64.deb
sudo apt-get install -f
```

### 3. System Configuration
```bash
# Enable IP forwarding
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
sysctl net.ipv4.ip_forward

# Disable swap (required for Kubernetes)
sudo swapoff -a
```

### 4. Kubernetes Installation
```bash
# Install prerequisites
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes GPG key and repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install Kubernetes components
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### 5. Join the Cluster
```bash
# Join the cluster using the token provided by the master node
sudo kubeadm join 10.10.1.1:6443 --token <token> \
    --discovery-token-ca-cert-hash <hash> \
    --cri-socket=unix:///var/run/cri-dockerd.sock
```

## Key Differences from Master Node
1. No Knative installation required
2. No network plugin (Calico) installation needed
3. No initialization of control plane
4. Joins existing cluster instead of creating new one
5. No kubectl configuration required

## Notes
- The join command must be run with sudo privileges
- The token and hash values come from the master node's initialization
- The CRI socket path must match the master node's configuration
- Worker nodes don't need Knative components as they are controlled by the master

## Verification
After joining the cluster:
1. On the master node, run:
```bash
kubectl get nodes
```
The new worker node should appear in the list.

## Network Configuration
- Worker nodes communicate with the master node on port 6443
- CRI-Docker provides container runtime capabilities
- Worker nodes will automatically use the networking solution (Calico) configured on the master