# NANDA Registry - Linode Deployment Quick Reference

## 🚀 One-Command Deployments

### Docker Deployment (4GB RAM)
```bash
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/dbname"
cd deploy/docker && ./provision-and-deploy-docker.sh
```

### Kubernetes Deployment (8GB RAM)
```bash
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/dbname"
cd deploy/kubernetes && ./provision-and-deploy-k8s.sh
```

### Simple Deployment (2GB RAM)
```bash
export ATLAS_URL="mongodb+srv://user:pass@cluster.mongodb.net/dbname"
cd deploy/simple && ./provision-and-deploy-simple.sh
```

## 📋 What These Scripts Do

1. ✅ Install & configure Linode CLI
2. ✅ Create firewall with proper rules
3. ✅ Generate SSH keys
4. ✅ Provision Linode instance
5. ✅ Install all dependencies
6. ✅ Deploy application
7. ✅ Run health checks
8. ✅ Display access info

## 🌍 Available Regions

- `us-east` (New Jersey, USA) - **Default**
- `us-west` (Fremont, CA, USA)
- `us-central` (Dallas, TX, USA)
- `us-southeast` (Atlanta, GA, USA)
- `eu-west` (London, UK)
- `eu-central` (Frankfurt, Germany)
- `ap-south` (Singapore)
- `ap-northeast` (Tokyo, Japan)

## 💾 Instance Types

| Type | RAM | CPU | Storage | Monthly Cost | Recommended For |
|------|-----|-----|---------|--------------|-----------------|
| g6-nanode-1 | 1GB | 1 core | 25GB | $5 | Testing only |
| g6-standard-1 | 2GB | 1 core | 50GB | $12 | Simple deployment |
| g6-standard-2 | 4GB | 2 cores | 80GB | $24 | Docker deployment |
| g6-standard-4 | 8GB | 4 cores | 160GB | $48 | Kubernetes deployment |
| g6-standard-6 | 16GB | 6 cores | 320GB | $96 | Production k8s |

## 🎛️ Customization Examples

### Different Region
```bash
export ATLAS_URL="mongodb+srv://..."
export REGION="eu-west"
cd deploy/docker && ./provision-and-deploy-docker.sh
```

### Larger Instance
```bash
export ATLAS_URL="mongodb+srv://..."
export INSTANCE_TYPE="g6-standard-6"
cd deploy/kubernetes && ./provision-and-deploy-k8s.sh
```

### Custom Label
```bash
export ATLAS_URL="mongodb+srv://..."
export INSTANCE_LABEL="my-production-registry"
export REGION="us-west"
cd deploy/simple && ./provision-and-deploy-simple.sh
```

### Full Customization
```bash
export ATLAS_URL="mongodb+srv://..."
export REGION="ap-south"
export INSTANCE_TYPE="g6-standard-4"
export INSTANCE_LABEL="nanda-prod-singapore"
export ROOT_PASSWORD="MySecurePassword123!"
cd deploy/docker && ./provision-and-deploy-docker.sh
```

## 🔍 After Deployment

### Service URLs (Docker & Simple)
- Agent Index: `http://YOUR_IP:6900`
- Agent Facts: `http://YOUR_IP:8000`
- Agent MCP: `http://YOUR_IP:8080`

### Service URLs (Kubernetes)
- Agent Index: `http://YOUR_IP:30690`
- Agent Facts: `http://YOUR_IP:30800`
- Agent MCP: `http://YOUR_IP:30808`

### Health Checks
```bash
curl http://YOUR_IP:6900/health
curl http://YOUR_IP:8000/health
curl http://YOUR_IP:8080/health
```

### SSH Access
```bash
ssh -i nanda-registry-key root@YOUR_IP
```

## 🧹 Cleanup

### Delete Instance
```bash
linode-cli linodes list
linode-cli linodes delete INSTANCE_ID
```

### Delete Firewall
```bash
linode-cli firewalls list
linode-cli firewalls delete FIREWALL_ID
```

### Remove SSH Keys
```bash
rm nanda-registry-key nanda-registry-key.pub
```

## 🔄 Updates

To update an existing deployment, just re-run the provision script:
```bash
cd deploy/docker && ./provision-and-deploy-docker.sh
```

The script will:
1. Ask if you want to recreate the instance
2. If yes: Delete old instance and create new one
3. If no: Use existing instance and redeploy

## 🆘 Troubleshooting

### Linode CLI Not Configured
```bash
pip install linode-cli
linode-cli configure
# Enter your Linode Personal Access Token
```

### Services Not Starting
```bash
# SSH into instance
ssh -i nanda-registry-key root@YOUR_IP

# Check logs (Docker)
cd /opt/nanda-registry && docker-compose logs -f

# Check logs (Kubernetes)
k3s kubectl logs -f deployment/agent-index -n nanda-registry

# Check logs (Simple)
journalctl -u nanda-agent-index -f
```

### MongoDB Connection Issues
- Verify ATLAS_URL is correct
- Check MongoDB Atlas network access (allow Linode IP)
- Test connection from instance:
  ```bash
  ssh -i nanda-registry-key root@YOUR_IP
  python3 -c "from pymongo import MongoClient; import os; client = MongoClient('YOUR_ATLAS_URL'); print(client.admin.command('ping'))"
  ```

### Firewall Issues
```bash
# List firewalls
linode-cli firewalls list

# View firewall rules
linode-cli firewalls rules-list FIREWALL_ID

# Delete and recreate
linode-cli firewalls delete FIREWALL_ID
# Re-run deployment script
```

## 📊 Cost Estimates

### Docker Deployment
- Instance: g6-standard-2 (4GB) = $24/month
- Bandwidth: 4TB included
- **Total: ~$24/month**

### Kubernetes Deployment
- Instance: g6-standard-4 (8GB) = $48/month
- Bandwidth: 8TB included
- **Total: ~$48/month**

### Simple Deployment
- Instance: g6-standard-1 (2GB) = $12/month
- Bandwidth: 2TB included
- **Total: ~$12/month**

**Note:** MongoDB Atlas pricing is separate

## 🎯 Best Practices

1. **Use Simple deployment** for development/testing
2. **Use Docker deployment** for staging environments
3. **Use Kubernetes deployment** for production with high availability
4. **Always use environment variables** for sensitive data
5. **Keep SSH keys secure** - never commit to git
6. **Set up monitoring** in production
7. **Enable backups** for production instances
8. **Use separate instances** for dev/staging/production

## 📚 Next Steps

1. Deploy your registry
2. Test all three services
3. Register an agent: `POST http://YOUR_IP:6900/register`
4. Set up monitoring (e.g., UptimeRobot)
5. Configure DNS for production domains
6. Set up SSL/TLS certificates (e.g., Let's Encrypt)
7. Implement backup strategy

## 🔗 Useful Links

- [Linode CLI Docs](https://www.linode.com/docs/products/tools/cli/get-started/)
- [MongoDB Atlas Setup](https://www.mongodb.com/docs/atlas/getting-started/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [k3s Documentation](https://k3s.io/)
- [NANDA Registry GitHub](https://github.com/projnanda/registry-server)
