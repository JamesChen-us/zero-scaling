# Useful Commands for Kubernetes and Testing

## Kubernetes Pod Management

### View All Pods
```bash
kubectl get pods
```
**Use Cases:**
- Monitor pod status (Running, Pending, Failed)
- Check pod health and restarts
- Verify deployment success
- Debug service issues

### Get Service Status
```bash
kubectl get ksvc
```
**Use Cases:**
- View Knative service status
- Check service URLs
- Monitor service readiness
- Verify configuration updates

### Generate Worker Node Join Command
```bash
kubeadm token create --print-join-command
```
**Use Cases:**
- Add new worker nodes to cluster
- Replace expired join tokens
- Expand cluster capacity
- Recover from node failures

### Delete All Configurations
```bash
kubectl delete configuration --all
```
**Use Cases:**
- Clean up test environments
- Reset cluster state
- Remove deprecated configurations
- Prepare for fresh deployment

## System Monitoring

### Monitor System Resources
```bash
top
```
**Use Cases:**
- Track CPU usage
- Monitor memory consumption
- Identify resource-heavy processes
- Debug performance issues
- Monitor node capacity

## Load Testing

### Interactive Locust Test
```bash
locust -H kn-frontend.default.127.0.0.1.sslip.io -f zero-scaling/locustfile.py --processes -1
```
**Key Parameters:**
- `-H`: Host to test
- `-f`: Test script file
- `--processes -1`: Use all available CPU cores

**Use Cases:**
- Web UI-based testing
- Real-time test monitoring
- Dynamic user load adjustment
- Interactive result analysis

### Headless Load Test
```bash
locust --headless --users 100 --spawn-rate 10 -H kn-frontend.default.127.0.0.1.sslip.io -f zero-scaling/locustfile.py
```
**Key Parameters:**
- `--headless`: Run without web interface
- `--users`: Number of simulated users
- `--spawn-rate`: Users added per second
- `-H`: Target host
- `-f`: Test script file

**Use Cases:**
- Automated testing
- CI/CD pipeline integration
- Batch testing
- Performance benchmarking
- Scalability testing

## Tips and Best Practices

1. **Resource Monitoring**
   - Always run `kubectl top pod` in a separate terminal during load tests
   - Monitor pod status with `kubectl get pods`
   - Check service health with `kubectl get ksvc`

2. **Load Testing**
   - Start with small user numbers and increase gradually
   - Monitor error rates and response times
   - Use `--headless` for automated testing
   - Save test results for comparison

3. **Cluster Management**
   - Regularly check pod status
   - Keep join tokens secure
   - Clean up unused configurations
   - Monitor node resources

4. **Troubleshooting**
   - Check logs with `kubectl logs <pod-name>`
   - Monitor system resources with `top`
   - Verify service status with `kubectl get ksvc`
   - Use `-v` flag for verbose output in commands

## Common Issues and Solutions

1. **Pod Pending State**
   ```bash
   kubectl describe pod <pod-name>
   ```
   - Check resource constraints
   - Verify node capacity
   - Review pod events

2. **Service Unavailable**
   ```bash
   kubectl get ksvc
   kubectl describe ksvc <service-name>
   ```
   - Check service configuration
   - Verify network connectivity
   - Review service endpoints

3. **Load Test Failures**
   - Verify target host accessibility
   - Check resource availability
   - Review test script logic
   - Monitor error logs

   kubectl get pods -n knative-serving

   lscpu