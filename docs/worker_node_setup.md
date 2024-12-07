# Kubernetes Worker Node Setup Guide

## Overview
This guide details the setup process for Kubernetes worker nodes that will run application workloads in the cluster.

## Prerequisites

### System Requirements
| Requirement | Specification |
|------------|---------------|
| OS | Ubuntu 22.04 |
| Access | Root/sudo privileges |
| Network | Connectivity to master node |
| Cluster | Running master node |

### Component Architecture
| Component | Purpose |
|-----------|----------|
| Docker | Container runtime |
| cri-dockerd | Docker-Kubernetes CRI interface |
| kubelet | Node agent for pod management |
| kubeadm | Cluster joining utility |

## Installation Steps

### 1. Docker Setup
```bash
# System preparation
sudo apt-get update
sudo apt-get install ca-certificates curl

# GPG key and repository setup
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Configure repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. CRI-Docker Integration
```bash
# Download and install CRI-Docker
wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.15/cri-dockerd_0.3.15.3-0.ubuntu-focal_amd64.deb
sudo dpkg -i cri-dockerd_0.3.15.3-0.ubuntu-focal_amd64.deb
sudo apt-get install -f
```

### 3. System Configuration
```bash
# Configure IP forwarding
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
sysctl net.ipv4.ip_forward

# Disable swap
sudo swapoff -a
```

### 4. Kubernetes Components
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | \
sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | \
sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install Kubernetes tools
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### 5. Cluster Integration
```bash
# Join the cluster (replace <token> and <hash> with values from master node)
sudo kubeadm join 10.10.1.1:6443 \
    --token <token> \
    --discovery-token-ca-cert-hash <hash> \
    --cri-socket=unix:///var/run/cri-dockerd.sock
```

## Worker vs Master Node Differences

| Feature | Worker Node | Master Node |
|---------|------------|-------------|
| Knative | Not required | Required |
| Network Plugin | Auto-configured | Requires setup |
| Control Plane | None | Full installation |
| Cluster Role | Joins existing | Creates new |
| kubectl config | Not needed | Required |

## Network Architecture
| Component | Configuration |
|-----------|---------------|
| Master Communication | Port 6443 |
| Container Runtime | CRI-Docker |
| Network Solution | Inherits Calico from master |

## Important Notes
- Join command requires sudo privileges
- Token and hash values are obtained from master node
- CRI socket path must match master configuration
- Knative components managed by master node

## Verification Process

### On Master Node
```bash
# Check node status
kubectl get nodes

# Expected output should show new worker node
```

### Verification Checklist
- [ ] Node appears in cluster node list
- [ ] Node status shows as "Ready"
- [ ] Node can receive workload assignments