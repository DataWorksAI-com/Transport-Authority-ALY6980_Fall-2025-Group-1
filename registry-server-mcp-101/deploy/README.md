# NANDA Registry - Linode Deployment Guide

This directory contains three different deployment strategies for the NANDA Registry Server on Linode:

1. **Docker** - Containerized deployment using Docker Compose
2. **Kubernetes** - Orchestrated deployment using k3s (lightweight Kubernetes)
3. **Simple** - Direct Python process deployment using systemd

Each deployment strategy has **two scripts**:
- **`provision-and-deploy-*.sh`** - Complete automation (creates Linode instance + deploys)
- **`deploy-linode-*.sh`** - Deploy only (requires existing Linode instance)

## Quick Start

### Prerequisites

**For Full Automation (provision-and-deploy scripts):**
1. **Linode CLI**: Install and configure Linode CLI
   ```bash
   pip install linode-cli
   linode-cli configure
   ```
2. **MongoDB Atlas**: Set up MongoDB Atlas and get connection URL
3. **Local Requirements**: `bash`, `curl`, `openssl`

**For Manual Deployment (deploy-linode scripts):**
1. **Linode Instance**: Create a Linode instance (ubuntu 25.04 LTS recommended)
2. **SSH Access**: Configure SSH key-based authentication
3. **MongoDB Atlas**: Set up MongoDB Atlas and get connection URL
4. **Local Requirements**: `bash`, `ssh`, `scp`, `curl`

### Environment Variables

All deployment scripts require these environment variables:

```bash
export LINODE_HOST="your-linode-ip"        # Your Linode instance IP
export LINODE_USER="root"                   # SSH user (default: root)
export SSH_KEY="~/.ssh/id_rsa"             # Path to SSH private key
export ATLAS_URL="mongodb+srv://..."       # MongoDB Atlas connection URL
```

## Deployment Options

### 1. Docker Deployment (Recommended for Development)

Uses Docker Compose to run all three services in separate containers.

**Advantages:**
- ✅ Isolated environments
- ✅ Easy to update and rollback
- ✅ Port mapping flexibility
- ✅ Built-in health checks
- ✅ Container orchestration

**Option A: Full Automation (Recommended)**
```bash
cd deploy/docker
export ATLAS_URL="mongodb+srv://..."
./provision-and-deploy-docker.sh

# Optional: Override defaults
export REGION="us-west"
export INSTANCE_TYPE="g6-standard-4"
export INSTANCE_LABEL="my-registry"
./provision-and-deploy-docker.sh
```

**Option B: Deploy to Existing Instance**
```bash
cd deploy/docker
export LINODE_HOST="your-ip"
export ATLAS_URL="mongodb+srv://..."
./deploy-linode-docker.sh
```

**Services:**
- Agent Index: `http://your-ip:6900`
- Agent Facts: `http://your-ip:8000`
- Agent MCP: `http://your-ip:8080`

**Management:**
```bash
# View logs
ssh root@your-ip 'cd /opt/nanda-registry && docker-compose logs -f'

# Restart services
ssh root@your-ip 'cd /opt/nanda-registry && docker-compose restart'

# Stop services
ssh root@your-ip 'cd /opt/nanda-registry && docker-compose down'

# Update deployment
./deploy-linode-docker.sh
```

### 2. Kubernetes Deployment (Recommended for Production)

Two Kubernetes options available:

#### Option A: Linode Kubernetes Engine (LKE) - **Highly Recommended**

Uses managed Kubernetes with LoadBalancers and auto-scaling.

**Advantages:**
- ✅ Fully managed Kubernetes (no maintenance)
- ✅ High availability (2 replicas per service)
- ✅ LoadBalancer integration (public IPs)
- ✅ Auto-healing and auto-scaling
- ✅ Easy cluster management
- ✅ Production-grade reliability

**Deploy to LKE:**
```bash
cd deploy/kubernetes
export ATLAS_URL="mongodb+srv://..."
./provision-lke-cluster.sh

# Optional: Override defaults
export REGION="eu-west"
export NODE_TYPE="g6-standard-4"
export NODE_COUNT="3"
export CLUSTER_LABEL="my-prod-cluster"
./provision-lke-cluster.sh
```

#### Option B: Self-Managed k3s on Linode

Uses k3s (lightweight Kubernetes) on a single Linode instance.

**Advantages:**
- ✅ Lower cost (single instance)
- ✅ Quick setup
- ✅ Good for development/staging

**Deploy k3s:**
```bash
cd deploy/kubernetes
export ATLAS_URL="mongodb+srv://..."
./provision-and-deploy-k8s.sh

# Optional: Override defaults
export REGION="eu-west"
export INSTANCE_TYPE="g6-standard-6"
./provision-and-deploy-k8s.sh
```

**Services (NodePort):**
- Agent Index: `http://your-ip:30690`
- Agent Facts: `http://your-ip:30800`
- Agent MCP: `http://your-ip:30808`

**Management:**
```bash
# View pods
ssh root@your-ip 'k3s kubectl get pods -n nanda-registry'

# View logs
ssh root@your-ip 'k3s kubectl logs -f deployment/agent-index -n nanda-registry'

# Scale deployment
ssh root@your-ip 'k3s kubectl scale deployment/agent-index --replicas=3 -n nanda-registry'

# Delete deployment
ssh root@your-ip 'k3s kubectl delete namespace nanda-registry'
```

### 3. Simple Deployment (Recommended for Small Projects)

Runs services directly as Python processes managed by systemd.

**Advantages:**
- ✅ Minimal overhead
- ✅ Simple to understand
- ✅ Easy to debug
- ✅ Direct access to logs
- ✅ No container dependencies

**Option A: Full Automation (Recommended)**
```bash
cd deploy/simple
export ATLAS_URL="mongodb+srv://..."
./provision-and-deploy-simple.sh

# Optional: Override defaults
export REGION="ap-south"
export INSTANCE_TYPE="g6-standard-1"
export INSTANCE_LABEL="my-simple-registry"
./provision-and-deploy-simple.sh
```

**Option B: Deploy to Existing Instance**
```bash
cd deploy/simple
export LINODE_HOST="your-ip"
export ATLAS_URL="mongodb+srv://..."
./deploy-linode-simple.sh
```

**Services:**
- Agent Index: `http://your-ip:6900`
- Agent Facts: `http://your-ip:8000`
- Agent MCP: `http://your-ip:8080`

**Management:**
```bash
# View logs
ssh root@your-ip 'journalctl -u nanda-agent-index -f'

# Restart service
ssh root@your-ip 'systemctl restart nanda-agent-index'

# Check status
ssh root@your-ip 'systemctl status nanda-agent-*'

# Restart all services
ssh root@your-ip 'systemctl restart nanda-agent-{index,facts,mcp}'

# Stop all services
ssh root@your-ip 'systemctl stop nanda-agent-{index,facts,mcp}'
```

## Service Ports

All deployments expose the same services on these ports:

| Service | Port | Description |
|---------|------|-------------|
| Agent Index | 6900 | FastAPI - Main agent registry |
| Agent Facts | 8000 | FastAPI - Agent facts lookup |
| Agent MCP | 8080 | FastMCP - MCP protocol server |

**Note:** Kubernetes uses NodePorts (30690, 30800, 30808) for external access.

## Health Checks

All services provide health check endpoints:

```bash
curl http://your-ip:6900/health
curl http://your-ip:8000/health
curl http://your-ip:8080/health
```

Expected response:
```json
{"status": "healthy", "mongodb": "connected"}
```

## Security

All deployment scripts automatically:
- ✅ Configure UFW firewall
- ✅ Allow only required ports (SSH, 6900, 8000, 8080)
- ✅ Enable auto-restart on failure
- ✅ Run services with proper permissions

### Manual Firewall Configuration

If needed, manually configure firewall:

```bash
ssh root@your-ip
ufw enable
ufw allow ssh
ufw allow 6900/tcp
ufw allow 8000/tcp
ufw allow 8080/tcp
ufw reload
```

## Troubleshooting

### Check Service Status

**Docker:**
```bash
ssh root@your-ip 'cd /opt/nanda-registry && docker-compose ps'
```

**Kubernetes:**
```bash
ssh root@your-ip 'k3s kubectl get pods -n nanda-registry'
```

**Simple:**
```bash
ssh root@your-ip 'systemctl status nanda-agent-*'
```

### View Logs

**Docker:**
```bash
ssh root@your-ip 'cd /opt/nanda-registry && docker-compose logs -f agent-index'
```

**Kubernetes:**
```bash
ssh root@your-ip 'k3s kubectl logs -f deployment/agent-index -n nanda-registry'
```

**Simple:**
```bash
ssh root@your-ip 'journalctl -u nanda-agent-index -f'
```

### Test MongoDB Connection

```bash
ssh root@your-ip
cd /opt/nanda-registry
source venv/bin/activate  # For simple deployment
python3 -c "from pymongo import MongoClient; import os; client = MongoClient(os.getenv('ATLAS_URL')); print(client.admin.command('ping'))"
```

### Common Issues

**Issue: Cannot connect to MongoDB**
- ✓ Check ATLAS_URL is correct
- ✓ Verify MongoDB Atlas allows connections from Linode IP
- ✓ Check firewall rules on MongoDB Atlas

**Issue: Services not starting**
- ✓ Check logs for error messages
- ✓ Verify all dependencies are installed
- ✓ Check disk space: `df -h`
- ✓ Check memory: `free -h`

**Issue: Port already in use**
- ✓ Check for conflicting services: `netstat -tulpn`
- ✓ Stop conflicting services
- ✓ Modify ports in deployment scripts if needed

## Updating Deployment

To update the application code:

1. Update your local code
2. Re-run the deployment script:

```bash
# Docker
cd deploy/docker && ./deploy-linode-docker.sh

# Kubernetes
cd deploy/kubernetes && ./deploy-linode-k8s.sh

# Simple
cd deploy/simple && ./deploy-linode-simple.sh
```

The scripts will:
- Copy new code to Linode
- Rebuild/restart services
- Verify health checks

## Comparison Table

| Feature | Simple | Docker | k3s | **LKE** |
|---------|--------|--------|-----|---------|
| **Setup Complexity** | Low | Medium | High | Medium |
| **Resource Usage** | Low | Medium | High | Medium |
| **High Availability** | No | No | Yes | **Yes** |
| **Auto-scaling** | No | No | No | **Yes** |
| **Managed Service** | No | No | No | **Yes** |
| **LoadBalancers** | No | No | NodePort | **Yes** |
| **Update Strategy** | Restart | Recreate | Rolling | **Rolling** |
| **Multi-Node** | No | No | No | **Yes** |
| **Production Ready** | Limited | Yes | Yes | **Best** |
| **Cost/Month** | ~$12 | ~$24 | ~$48 | ~$78+ |
| **Best For** | Testing | Dev/Staging | Small Prod | **Production** |

## Automation Scripts

### provision-and-deploy-*.sh (Full Automation)

These scripts handle everything:
1. ✅ Check Linode CLI credentials
2. ✅ Create/reuse firewall rules
3. ✅ Generate SSH keys
4. ✅ Create Linode instance
5. ✅ Wait for instance to be ready
6. ✅ Install all dependencies
7. ✅ Deploy application
8. ✅ Test services
9. ✅ Display access information

**Environment Variables:**
- `ATLAS_URL` (required) - MongoDB Atlas connection URL
- `REGION` (optional) - Linode region (default varies by script)
- `INSTANCE_TYPE` (optional) - Linode plan type
- `INSTANCE_LABEL` (optional) - Instance name
- `ROOT_PASSWORD` (optional) - Auto-generated if not provided

**Example:**
```bash
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/dbname"
export REGION="us-west"
export INSTANCE_TYPE="g6-standard-4"
cd deploy/docker
./provision-and-deploy-docker.sh
```

### deploy-linode-*.sh (Manual Deployment)

These scripts require an existing Linode instance:
- Use when you've already created infrastructure
- Useful for re-deploying to existing instances
- Requires manual SSH key setup

**Environment Variables:**
- `LINODE_HOST` (required) - Linode instance IP address
- `LINODE_USER` (optional) - SSH user (default: root)
- `SSH_KEY` (optional) - SSH private key path
- `ATLAS_URL` (required) - MongoDB Atlas connection URL

## Cost Estimates (Linode)

- **Linode 2GB**: $12/month (Simple deployment)
- **Linode 4GB**: $24/month (Docker deployment)
- **Linode 8GB**: $48/month (Kubernetes deployment)

## Next Steps

1. Choose deployment strategy based on your needs
2. Create Linode instance
3. Configure MongoDB Atlas
4. Run deployment script
5. Test services using health checks
6. Monitor logs and performance

## Support

For issues or questions:
- Check logs for error messages
- Review MongoDB Atlas network access
- Verify environment variables are set correctly
- Test network connectivity to Linode instance

## Architecture

All deployments use the same shared service layer architecture:

```
┌─────────────────────────────────────────┐
│         Linode Instance                  │
│                                          │
│  ┌──────────────────────────────────┐  │
│  │  Agent Index (Port 6900)         │  │
│  │  FastAPI - Registry endpoints     │  │
│  └──────────────────────────────────┘  │
│                                          │
│  ┌──────────────────────────────────┐  │
│  │  Agent Facts (Port 8000)         │  │
│  │  FastAPI - Facts lookup           │  │
│  └──────────────────────────────────┘  │
│                                          │
│  ┌──────────────────────────────────┐  │
│  │  Agent MCP (Port 8080)           │  │
│  │  FastMCP - MCP protocol           │  │
│  └──────────────────────────────────┘  │
│                                          │
│  ┌──────────────────────────────────┐  │
│  │  RegistryService (Shared Layer)  │  │
│  │  - MongoDB operations             │  │
│  │  - Business logic                 │  │
│  │  - AgentFacts API integration     │  │
│  └──────────────────────────────────┘  │
│                                          │
└─────────────────────────────────────────┘
            │
            ↓
    ┌───────────────┐
    │ MongoDB Atlas │
    └───────────────┘
```

All three services share the same `RegistryService` layer, ensuring consistent behavior and DRY code! 🎉
