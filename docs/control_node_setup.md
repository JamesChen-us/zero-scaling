# Kubernetes Cluster Setup with Knative (Master Node)

## Overview
This guide provides detailed instructions for setting up a Kubernetes master node with Knative integration, including Docker, Kubernetes, Calico networking, and Knative components.

## Prerequisites

### System Requirements
- Ubuntu 22.04 (or compatible Ubuntu-based system)
- Root or sudo access
- x86_64 architecture

### Component Architecture
| Component | Purpose |
|-----------|---------|
| Docker | Container runtime |
| cri-dockerd | CRI interface for Docker-Kubernetes communication |
| Kubernetes | Container orchestration platform |
| Calico | Container networking interface (CNI) |
| Knative | Serverless platform |
| Kourier | Kubernetes ingress controller |

## Installation Steps

### 1. Docker Installation
**Reference**: [Docker Installation Guide](https://docs.docker.com/engine/install/ubuntu/)

```bash
# System Updates
sudo apt-get update
sudo apt-get install ca-certificates curl

# Docker GPG Key and Repository Setup
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. CRI-Docker Installation
**Reference**: [CRI-Docker Guide](https://mirantis.github.io/cri-dockerd/usage/install/)

```bash
wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.15/cri-dockerd_0.3.15.3-0.ubuntu-focal_amd64.deb
sudo dpkg -i cri-dockerd_0.3.15.3-0.ubuntu-focal_amd64.deb
sudo apt-get install -f
```

### 3. System Configuration
**Reference**: [Kubernetes Container Runtime Setup](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)

```bash
# IP Forwarding Configuration
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
sysctl net.ipv4.ip_forward

# Disable Swap
sudo swapoff -a
```

### 4. Kubernetes Installation
**Reference**: [Kubeadm Installation Guide](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)

```bash
# Install Dependencies
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes Repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install Kubernetes Components
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### 5. Cluster Initialization
**Reference**: [Cluster Creation Guide](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)

```bash
# Initialize Master Node
sudo kubeadm init \
  --apiserver-advertise-address=10.10.1.1 \
  --pod-network-cidr=192.168.0.0/16 \
  --cri-socket=unix:///var/run/cri-dockerd.sock

# Configure kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 6. Calico Network Plugin Installation
**Reference**: [Calico Installation Guide](https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises#install-calico)

```bash
curl https://raw.githubusercontent.com/projectcalico/calico/v3.29.1/manifests/calico.yaml -O
kubectl apply -f calico.yaml
```

### 7. Knative Setup
**Reference**: [Knative CLI Installation](https://knative.dev/docs/client/install-kn/#install-the-knative-cli)

```bash
# Install Knative CLI
curl -LO https://github.com/knative/client/releases/download/knative-v1.16.0/kn-linux-amd64
mv kn-linux-amd64 kn
chmod +x kn
sudo mv kn /usr/local/bin

# Setup kubectl Autocompletion
kubectl completion bash | sudo tee /etc/bash_completion.d/kubectl > /dev/null
sudo chmod a+r /etc/bash_completion.d/kubectl
source ~/.bashrc

# Install Knative Components
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-crds.yaml
kubectl apply -f zero-scaling/configuration.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-core.yaml
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.16.0/kourier.yaml

# Configure Kourier
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Configure Domain
kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"127.0.0.1.sslip.io":""}}'
```

## Network Architecture
| Component | Function |
|-----------|----------|
| Docker | Container runtime environment |
| cri-dockerd | Kubernetes-Docker CRI interface |
| Calico | Pod networking (192.168.0.0/16 CIDR) |
| Kourier | Knative ingress gateway |
| API Server | Advertised on 10.10.1.1 |

## Important Notes
- This setup is specific to the master node
- Worker nodes require separate configuration (10 nodes recommended)
- Required ports:
  - 6443
  - 2379-2380
  - 10250-10252
- Worker node setup should be completed before Knative configuration
- See [Worker Node Setup Guide](docs/worker_node_setup.md) for additional nodes

## Verification Steps
```bash
# Check node status
kubectl get nodes

# Check system pods
kubectl get pods -A
```

Expected result: Master node should show "Ready" status and system pods should be running in kube-system namespace.