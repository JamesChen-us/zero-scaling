# Kubernetes Cluster Setup with Knative (Master Node)

## Overview
This documentation covers the setup process for a Kubernetes master node with Knative integration. The setup includes Docker, Kubernetes, Calico networking, and Knative serving/eventing components.

## System Requirements
- Ubuntu-based system (tested on Ubuntu 22.04)
- Root or sudo access
- x86_64 architecture

## Component Architecture
- **Docker**: Container runtime
- **cri-dockerd**: CRI interface between Kubernetes and Docker
- **Kubernetes**: Container orchestration platform
- **Calico**: Container networking interface (CNI)
- **Knative**: Serverless platform built on Kubernetes
- **Kourier**: Kubernetes ingress controller for Knative

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
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes GPG key and repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install Kubernetes components
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### 5. Initialize Kubernetes Cluster
```bash
# Initialize the master node
sudo kubeadm init --apiserver-advertise-address=10.10.1.1 --pod-network-cidr=192.168.0.0/16 --cri-socket=unix:///var/run/cri-dockerd.sock

# Configure kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 6. Install Calico Network Plugin
```bash
curl https://raw.githubusercontent.com/projectcalico/calico/v3.29.1/manifests/calico.yaml -O
kubectl apply -f calico.yaml
```

### 7. Installing Knative Components
```bash
# Install Knative CLI
curl -LO https://github.com/knative/client/releases/download/knative-v1.16.0/kn-linux-amd64
mv kn-linux-amd64 kn
chmod +x kn
sudo mv kn /usr/local/bin

# Setup kubectl autocompletion
kubectl completion bash | sudo tee /etc/bash_completion.d/kubectl > /dev/null
sudo chmod a+r /etc/bash_completion.d/kubectl
source ~/.bashrc

# Install Knative Serving CRDs
# https://knative.dev/docs/install/yaml-install/serving/install-serving-with-yaml/#verifying-image-signatures
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-crds.yaml

kubectl apply -f zero-scaling/configuration.yaml

# Install Knative Serving core
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.16.0/serving-core.yaml

# Install Kourier controller
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.16.0/kourier.yaml

# Configure Kourier
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Configure Domain Configuration
kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"127.0.0.1.sslip.io":""}}'
```

## Network Architecture
- Docker provides the container runtime
- cri-dockerd enables Docker to work with Kubernetes CRI
- Calico provides pod networking (192.168.0.0/16 CIDR)
- Kourier serves as the ingress gateway for Knative
- Master node API server advertised on 10.10.1.1

## Notes
- This setup is for the master node only
- Worker nodes need separate configuration
- Ensure all ports required by Kubernetes are open (6443, 2379-2380, 10250-10252)
- The Knative installation includes both Serving and Eventing components
- Kourier is configured as the default networking layer for Knative

## Verification
After installation, you can verify the setup using:
```bash
kubectl get nodes
kubectl get pods -A
```

The master node should be showing as Ready, and system pods should be running in the kube-system namespace.