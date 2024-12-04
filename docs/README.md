# Zero-scaling Project

This repository contains the implementation of a zero-scaling system using Knative and Kubernetes.

## Prerequisites
- Ubuntu-based system (22.04 recommended)
- Root or sudo access
- Python 3.x
- Docker
- Kubernetes
- Knative

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/JamesChen-us/zero-scaling.git
```

### 2. Cluster Setup
Before proceeding, you need to set up your Kubernetes cluster:
- [Master Node Setup Guide](docs/control_node_setup.md)
- [Worker Node Setup Guide](docs/worker_node_setup.md)

### 3. Install Required Libraries
```bash
# Install Python dependencies
sudo apt install python3-pip
sudo apt install python3-locust

# Install Locust and other requirements
pip install locust
pip install --upgrade locust jinja2
pip install pandas
```

### 4. Configure Service Communication

#### Get Cluster Information
```bash
# Get the node's internal IP address
export IP=$(kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}')

# Get Kourier's HTTP2 nodePort
export PORT=$(kubectl get svc kourier -n kourier-system -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
```

#### Update Configuration
1. Open `zero-scaling/configuration.yaml`
2. Replace all instances of `IP:PORT` with the values obtained above
3. Apply the configuration:
```bash
kubectl apply -f zero-scaling/configuration.yaml
```

### 5. Verify Setup

#### Check Service Status
```bash
kubectl get ksvc
```
All services should show `Ready: True`

#### Validate Frontend Access
```bash
curl -H "Host: kn-frontend.default.127.0.0.1.sslip.io" http://$IP:$PORT -v
```

## Project Structure
```
zero-scaling/
├── configuration.yaml    # Knative service configurations
├── docs/
│   ├── master-setup.md  # Master node setup instructions
│   └── worker-setup.md  # Worker node setup instructions
|   └── README.md           
```

## Notes
- Ensure all services are properly configured before running experiments
- The IP and PORT values are crucial for service-to-service communication
- Kourier Ingress must be properly configured for external access
- Check service status regularly using `kubectl get ksvc`

## Troubleshooting
If you encounter issues:
1. Verify all services are running (`kubectl get ksvc`)
2. Check Kourier configuration (`kubectl get svc -n kourier-system`)
3. Ensure correct IP and PORT values
4. Verify network connectivity between services


# Commit
sudo apt install git-lfs
git lfs install
git lfs track "*.txt"