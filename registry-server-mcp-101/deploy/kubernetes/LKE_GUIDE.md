# Linode Kubernetes Engine (LKE) Deployment Guide

## Overview

This guide covers deploying the NANDA Registry to Linode Kubernetes Engine (LKE), Akamai's managed Kubernetes service.

## Why LKE?

### Advantages over Self-Managed k3s

| Feature | Self-Managed k3s | LKE |
|---------|------------------|-----|
| **Cluster Management** | Manual | Automatic |
| **Control Plane** | You manage | Linode manages (free) |
| **Node Maintenance** | Manual updates | Auto-updates available |
| **LoadBalancers** | NodePort only | Native LoadBalancers |
| **Scaling** | Manual | Click or API |
| **High Availability** | Single node | Multi-node by default |
| **Monitoring** | Setup required | Built-in metrics |
| **Cost** | $48/month (single 8GB node) | $48/month (2x 4GB nodes) + $30 LB |

### Key Benefits

1. **Managed Control Plane** - Free! Linode manages the Kubernetes control plane
2. **LoadBalancer Integration** - Each service gets a public IP automatically
3. **Auto-Healing** - Nodes automatically replaced if they fail
4. **Easy Scaling** - Add/remove nodes with one command
5. **Production-Ready** - Built-in redundancy and reliability
6. **No Maintenance** - Linode handles updates and patches

## Quick Start

### Prerequisites

1. **Linode CLI** configured with valid credentials
2. **kubectl** installed (script can install it)
3. **MongoDB Atlas** connection URL

### One-Command Deployment

```bash
cd deploy/kubernetes
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/db"
./provision-lke-cluster.sh
```

## Configuration Options

### Environment Variables

```bash
# Required
export ATLAS_URL="mongodb+srv://..."

# Optional (with defaults)
export REGION="us-east"                    # Linode region
export CLUSTER_LABEL="nanda-registry-cluster"  # Cluster name
export K8S_VERSION="1.28"                  # Kubernetes version
export NODE_TYPE="g6-standard-2"           # 4GB RAM per node
export NODE_COUNT="2"                      # Number of nodes
```

### Node Types and Pricing

| Type | RAM | CPU | Storage | Cost/Node/Month |
|------|-----|-----|---------|-----------------|
| g6-standard-1 | 2GB | 1 | 50GB | $12 |
| g6-standard-2 | 4GB | 2 | 80GB | $24 ⭐ |
| g6-standard-4 | 8GB | 4 | 160GB | $48 |
| g6-standard-6 | 16GB | 6 | 320GB | $96 |

⭐ **Recommended**: g6-standard-2 (4GB) × 2 nodes = $48/month + LoadBalancers

### Regions

- `us-east` (Newark, NJ) - Default
- `us-west` (Fremont, CA)
- `us-central` (Dallas, TX)
- `us-southeast` (Atlanta, GA)
- `eu-west` (London, UK)
- `eu-central` (Frankfurt, Germany)
- `ap-south` (Singapore)
- `ap-northeast` (Tokyo, Japan)
- `ap-west` (Mumbai, India)

## Deployment Process

### What the Script Does

1. **Validates** Linode CLI and kubectl
2. **Creates** LKE cluster with specified nodes
3. **Waits** for cluster to be ready (5-10 min)
4. **Downloads** kubeconfig for cluster access
5. **Creates** ConfigMap with application source
6. **Deploys** all three services with init containers
7. **Provisions** LoadBalancers (public IPs)
8. **Tests** all services

### Architecture

```
┌─────────────────────────────────────────────────┐
│         Linode Kubernetes Engine (LKE)          │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Control Plane (Managed by Linode - FREE)  │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌─────────────┐        ┌─────────────┐        │
│  │   Node 1    │        │   Node 2    │        │
│  │  4GB RAM    │        │  4GB RAM    │        │
│  │             │        │             │        │
│  │ ┌─────────┐ │        │ ┌─────────┐ │        │
│  │ │ Index   │ │        │ │ Index   │ │        │
│  │ │ Pod     │ │        │ │ Pod     │ │        │
│  │ └─────────┘ │        │ └─────────┘ │        │
│  │ ┌─────────┐ │        │ ┌─────────┐ │        │
│  │ │ Facts   │ │        │ │ Facts   │ │        │
│  │ │ Pod     │ │        │ │ Pod     │ │        │
│  │ └─────────┘ │        │ └─────────┘ │        │
│  │ ┌─────────┐ │        │ ┌─────────┐ │        │
│  │ │ MCP     │ │        │ │ MCP     │ │        │
│  │ │ Pod     │ │        │ │ Pod     │ │        │
│  │ └─────────┘ │        │ └─────────┘ │        │
│  └─────────────┘        └─────────────┘        │
│         ↓                       ↓                │
│  ┌─────────────┐        ┌─────────────┐        │
│  │ LoadBalancer│        │ LoadBalancer│        │
│  │ (Public IP) │        │ (Public IP) │        │
│  └─────────────┘        └─────────────┘        │
└─────────────────────────────────────────────────┘
```

### Services with LoadBalancers

Each service gets its own LoadBalancer with a public IP:

- **Agent Index** - http://\<LB-IP\>:6900
- **Agent Facts** - http://\<LB-IP\>:8000
- **Agent MCP** - http://\<LB-IP\>:8080

## Managing Your Cluster

### Access Cluster

```bash
# Export kubeconfig (from deployment directory)
export KUBECONFIG=$(pwd)/nanda-registry-cluster-kubeconfig.yaml

# View cluster info
kubectl cluster-info
kubectl get nodes
```

### View Deployments

```bash
# List all resources
kubectl get all -n nanda-registry

# View pods
kubectl get pods -n nanda-registry

# View services and external IPs
kubectl get svc -n nanda-registry
```

### View Logs

```bash
# Logs from a specific pod
kubectl logs -f deployment/agent-index -n nanda-registry

# Logs from all replicas
kubectl logs -l app=agent-index -n nanda-registry --tail=100
```

### Scale Services

```bash
# Scale up
kubectl scale deployment/agent-index --replicas=4 -n nanda-registry

# Scale down
kubectl scale deployment/agent-index --replicas=1 -n nanda-registry

# Scale all services
kubectl scale deployment --all --replicas=3 -n nanda-registry
```

### Update Application

```bash
# Update source code ConfigMap
kubectl create configmap nanda-registry-src \
    --from-file=../../src/ \
    --namespace=nanda-registry \
    --dry-run=client -o yaml | kubectl apply -f -

# Restart deployments to pick up changes
kubectl rollout restart deployment/agent-index -n nanda-registry
kubectl rollout restart deployment/agent-facts -n nanda-registry
kubectl rollout restart deployment/agent-mcp -n nanda-registry

# Watch rollout status
kubectl rollout status deployment/agent-index -n nanda-registry
```

### Add/Remove Nodes

```bash
# Get cluster ID
CLUSTER_ID=$(linode-cli lke clusters-list --text --no-headers --format="id,label" | grep "nanda-registry-cluster" | cut -f1)

# List node pools
linode-cli lke pools-list $CLUSTER_ID

# Get pool ID
POOL_ID=$(linode-cli lke pools-list $CLUSTER_ID --text --no-headers --format="id" | head -1)

# Update node count
linode-cli lke pool-update $CLUSTER_ID $POOL_ID --count 3
```

## Monitoring

### Health Checks

```bash
# Get LoadBalancer IPs
INDEX_IP=$(kubectl get svc agent-index -n nanda-registry -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
FACTS_IP=$(kubectl get svc agent-facts -n nanda-registry -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
MCP_IP=$(kubectl get svc agent-mcp -n nanda-registry -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test services
curl http://$INDEX_IP:6900/health
curl http://$FACTS_IP:8000/health
nc -z $MCP_IP 8080
```

### Resource Usage

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods -n nanda-registry
```

### Events

```bash
# Cluster events
kubectl get events -n nanda-registry --sort-by='.lastTimestamp'

# Pod events
kubectl describe pod <pod-name> -n nanda-registry
```

## Cost Management

### Monthly Costs

**Base Cluster (2 nodes):**
- Control Plane: $0 (free!)
- 2 × g6-standard-2 (4GB): $48/month
- 3 × LoadBalancers: $30/month
- **Total: ~$78/month**

**Production Cluster (3 nodes):**
- Control Plane: $0 (free!)
- 3 × g6-standard-2 (4GB): $72/month
- 3 × LoadBalancers: $30/month
- **Total: ~$102/month**

### Cost Optimization

1. **Use fewer LoadBalancers** - Use Ingress controller instead
2. **Auto-scale nodes** - Scale down during low usage
3. **Right-size nodes** - Start with g6-standard-1 (2GB) for testing
4. **Use single LoadBalancer** - Configure Ingress with path routing

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n nanda-registry

# Check logs
kubectl logs <pod-name> -n nanda-registry

# Check events
kubectl get events -n nanda-registry
```

### LoadBalancer Pending

```bash
# Check service status
kubectl describe svc agent-index -n nanda-registry

# LoadBalancers take 2-3 minutes to provision
# If still pending after 5 minutes, check Linode dashboard
```

### Can't Connect to Service

```bash
# Verify LoadBalancer has external IP
kubectl get svc -n nanda-registry

# Check if pods are running
kubectl get pods -n nanda-registry

# Test from inside cluster
kubectl run test --rm -it --image=busybox -- sh
# Then: wget -O- http://agent-index.nanda-registry:6900/health
```

### MongoDB Connection Issues

```bash
# Check secret
kubectl get secret nanda-secrets -n nanda-registry -o yaml

# View pod logs for connection errors
kubectl logs -l app=agent-index -n nanda-registry | grep -i mongo

# Verify ATLAS_URL in secret
kubectl get secret nanda-secrets -n nanda-registry -o jsonpath='{.data.atlas-url}' | base64 -d
```

## Cleanup

### Delete Cluster

```bash
# Get cluster ID
CLUSTER_ID=$(linode-cli lke clusters-list --text --no-headers --format="id,label" | grep "nanda-registry-cluster" | cut -f1)

# Delete cluster (this deletes all nodes and LoadBalancers)
linode-cli lke cluster-delete $CLUSTER_ID
```

### Delete Kubeconfig

```bash
rm nanda-registry-cluster-kubeconfig.yaml
```

## Production Recommendations

1. **Use 3+ nodes** for true high availability
2. **Enable auto-scaling** for node pools
3. **Set resource limits** on pods
4. **Use Ingress** instead of multiple LoadBalancers
5. **Enable monitoring** with Prometheus/Grafana
6. **Set up alerts** for pod failures
7. **Use secrets management** for MongoDB credentials
8. **Regular backups** of MongoDB
9. **Use staging cluster** for testing
10. **Implement CI/CD** for automated deployments

## Next Steps

1. ✅ Deploy to LKE
2. ✅ Verify all services are running
3. ✅ Test health endpoints
4. 🔧 Configure custom domain with DNS
5. 🔧 Set up Ingress controller
6. 🔧 Enable SSL/TLS certificates
7. 🔧 Implement monitoring
8. 🔧 Set up CI/CD pipeline
9. 🔧 Configure auto-scaling
10. 🔧 Implement backup strategy

## Support

For LKE-specific issues:
- [Linode Kubernetes Engine Documentation](https://www.linode.com/docs/products/compute/kubernetes/)
- [LKE API Reference](https://www.linode.com/docs/api/linode-kubernetes-engine-lke/)
- [Linode Community](https://www.linode.com/community/)

For Kubernetes issues:
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
