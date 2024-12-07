# Zero-scaling Project Guide

## Overview
Implementation of a zero-scaling system leveraging Knative and Kubernetes.

## References
| Resource | Link |
|----------|------|
| Implementation Base | [Spright Project](https://github.com/ucr-serverless/spright/tree/next/sigcomm-experiment) |
| Video Guide | [YouTube Tutorial](https://www.youtube.com/watch?v=o6bxo0Oeg6o) |

## Prerequisites

### System Requirements
| Component | Version/Specification |
|-----------|---------------------|
| OS | Ubuntu 22.04 |
| Access | Root/sudo privileges |
| Runtime | Python 3.x |
| Containers | Docker |
| Orchestration | Kubernetes |
| Serverless | Knative |

## Installation Steps

### 1. Repository Setup
```bash
git clone https://github.com/JamesChen-us/zero-scaling.git
```

### 2. Azure Functions Trace Data
```bash
# Install requirements
sudo apt-get update
sudo apt-get install unrar

# Download and extract trace data
curl -L -o zero-scaling/AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar \
    https://github.com/Azure/AzurePublicDataset/raw/master/data/AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar

unrar e zero-scaling/AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar zero-scaling/
mv zero-scaling/AzureFunctionsInvocationTraceForTwoWeeksJan2021.txt \
    zero-scaling/AzureFunctionsInvocationTrace.txt
```

### 3. Cluster Configuration
Complete these setups before proceeding:
- [Master Node Setup](docs/control_node_setup.md)
- [Worker Node Setup](docs/worker_node_setup.md)

### 4. Python Dependencies
```bash
# System packages
sudo apt install python3-pip python3-locust

# Python packages
pip install locust --upgrade
pip install jinja2
pip install pandas matplotlib seaborn
```

### 5. Service Configuration

#### Cluster Information Gathering
```bash
# Get control node's internal IP
kubectl get nodes -o wide

# Retrieve Kourier's HTTP2 port
PORT=$(kubectl get svc kourier -n kourier-system \
    -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
```

#### Configuration Updates
1. Edit configuration files:
   - `zero-scaling/configuration.yaml`
   - `zero-scaling/locustfile.py`
2. Update `IP:PORT` values
3. Deploy configuration:
```bash
kubectl apply -f zero-scaling/configuration.yaml
```

### 6. System Verification

#### Service Health Check
```bash
# Verify service status
kubectl get ksvc
```

Expected output: All services should show `Ready: True`

#### Frontend Accessibility
```bash
# Test frontend access
curl -H "Host: kn-frontend.default.127.0.0.1.sslip.io" \
    http://128.110.96.97:31882 -v
```

#### Metrics Server Setup
```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Edit deployment if needed
kubectl -n kube-system edit deploy metrics-server

# Verify metrics collection
kubectl top pod
```

### 7. Visualization and Testing
```bash
# Generate histograms
python zero-scaling/histogram.py

# Run load test
locust -H kn-frontend.default.127.0.0.1.sslip.io \
    -f zero-scaling/locustfile.py --processes -1
```

## Important Notes

### Configuration Checklist
- [ ] Services properly configured
- [ ] IP and PORT values verified
- [ ] Kourier Ingress setup complete
- [ ] Regular service status monitoring

### Troubleshooting Guide

| Issue | Resolution Steps |
|-------|-----------------|
| Service Status | Run `kubectl get ksvc` |
| Kourier Config | Check `kubectl get svc -n kourier-system` |
| Connectivity | Verify service-to-service communication |
| IP/PORT | Confirm values in configuration files |