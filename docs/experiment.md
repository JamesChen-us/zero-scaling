# Knative Autoscaling Testing Guide

## Overview
Process for testing Knative autoscaling configurations using different workload patterns and metrics.

## Prerequisites
- Configured Kubernetes cluster with Knative installed
- Locust load testing tool
- kubectl CLI tool

## Configuration Steps

### 1. Modify Autoscaling Parameters
Update your Knative service configuration with desired autoscaling settings:
```yaml
annotations:
    autoscaling.knative.dev/minScale: "1"
    autoscaling.knative.dev/maxScale: "15"
    autoscaling.knative.dev/metric: "rps"  
    autoscaling.knative.dev/target: "100"
```

### 2. Apply Changes
```bash
kubectl apply -f zero-scaling/configuration.yaml
```

### 3. Start Load Testing
Launch Locust with:
```bash
locust -H kn-frontend.default.127.0.0.1.sslip.io -f zero-scaling/locustfile.py --processes -1
```

## Test Scenarios

### Scaling Approaches
We test two distinct scaling strategies:
1. Zero-scaling - Allows scaling to zero pods when idle
2. Non-zero scaling - Maintains minimum of one pod

### Metrics Configuration
Test each scaling approach with:
- RPS (Requests Per Second): Target = 100
- Concurrency: Target = 100

### Workload Patterns

1. **Constant Workload**
   - Number of Users: 3000
   - Users Started/Second: 3000
   - Description: Tests system behavior under sustained, steady load

2. **Incremental Workload**
   - Number of Users:100
   - Users Started/Second: 3000
   - Description: Evaluates scaling response to gradually increasing load

3. **Burst Workload**
   - Number of User: 1000 users
   - Users Started/Second: 3000
   - Description: Tests system response to sudden load spikes