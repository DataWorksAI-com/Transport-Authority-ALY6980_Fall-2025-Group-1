#!/bin/bash

# NANDA Registry - Linode Kubernetes Deployment Script
# This script deploys the registry server using Kubernetes on a Linode instance

set -e  # Exit on error

# Configuration
LINODE_HOST="${LINODE_HOST:-your-linode-ip}"
LINODE_USER="${LINODE_USER:-root}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"
ATLAS_URL="${ATLAS_URL}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
if [ -z "$ATLAS_URL" ]; then
    log_error "ATLAS_URL environment variable is not set"
    echo "Usage: ATLAS_URL=your_mongodb_url ./deploy-linode-k8s.sh"
    exit 1
fi

if [ "$LINODE_HOST" = "your-linode-ip" ]; then
    log_error "Please set LINODE_HOST environment variable"
    echo "Usage: LINODE_HOST=your-ip ATLAS_URL=your_mongodb_url ./deploy-linode-k8s.sh"
    exit 1
fi

log_info "Starting Kubernetes deployment to Linode: $LINODE_HOST"

# Test SSH connection
log_info "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$LINODE_USER@$LINODE_HOST" "echo 'SSH connection successful'"; then
    log_error "Cannot connect to Linode instance"
    exit 1
fi

# Install k3s (lightweight Kubernetes) on Linode
log_info "Installing k3s (lightweight Kubernetes)..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    # Install k3s if not present
    if ! command -v k3s &> /dev/null; then
        echo "Installing k3s..."
        curl -sfL https://get.k3s.io | sh -
        
        # Wait for k3s to be ready
        echo "Waiting for k3s to be ready..."
        sleep 15
        
        # Configure kubectl alias
        echo "alias kubectl='k3s kubectl'" >> ~/.bashrc
    else
        echo "k3s already installed"
    fi
    
    # Install Docker for building images
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        systemctl start docker
        rm get-docker.sh
    fi
    
    # Create app directory
    mkdir -p /opt/nanda-registry
ENDSSH

# Copy application files to Linode
log_info "Copying application files to Linode..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" "rm -rf /opt/nanda-registry/*"
scp -i "$SSH_KEY" -r ../../src "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"
scp -i "$SSH_KEY" ../../requirements.txt "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"
scp -i "$SSH_KEY" ../docker/Dockerfile "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"
scp -i "$SSH_KEY" deployment.yaml "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"

# Build Docker image on Linode
log_info "Building Docker image..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    cd /opt/nanda-registry
    docker build -t nanda-registry:latest -f Dockerfile .
    
    # Import image into k3s
    docker save nanda-registry:latest | k3s ctr images import -
ENDSSH

# Update deployment.yaml with actual ATLAS_URL
log_info "Configuring Kubernetes deployment..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << ENDSSH
    cd /opt/nanda-registry
    
    # Replace placeholder with actual ATLAS_URL
    sed -i 's|\${ATLAS_URL}|$ATLAS_URL|g' deployment.yaml
ENDSSH

# Deploy to Kubernetes
log_info "Deploying to Kubernetes..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    cd /opt/nanda-registry
    
    # Apply Kubernetes manifests
    k3s kubectl apply -f deployment.yaml
    
    # Wait for deployments to be ready
    echo "Waiting for deployments to be ready..."
    k3s kubectl wait --for=condition=available --timeout=120s \
        deployment/agent-index \
        deployment/agent-facts \
        deployment/agent-mcp \
        -n nanda-registry || true
    
    # Check deployment status
    k3s kubectl get pods -n nanda-registry
    k3s kubectl get services -n nanda-registry
ENDSSH

# Configure firewall
log_info "Configuring firewall..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        apt-get update && apt-get install -y ufw
    fi
    
    # Configure firewall rules
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 30690/tcp  # Agent Index NodePort
    ufw allow 30800/tcp  # Agent Facts NodePort
    ufw allow 30808/tcp  # Agent MCP NodePort
    ufw allow 6443/tcp   # Kubernetes API
    ufw reload
ENDSSH

# Test services
log_info "Testing deployed services..."
sleep 10

log_info "Testing Agent Index service (NodePort 30690)..."
if curl -f -s "http://$LINODE_HOST:30690/health" > /dev/null; then
    log_info "✓ Agent Index service is healthy"
else
    log_warn "✗ Agent Index service health check failed"
fi

log_info "Testing Agent Facts service (NodePort 30800)..."
if curl -f -s "http://$LINODE_HOST:30800/health" > /dev/null; then
    log_info "✓ Agent Facts service is healthy"
else
    log_warn "✗ Agent Facts service health check failed"
fi

log_info "Testing Agent MCP service (NodePort 30808)..."
if curl -f -s "http://$LINODE_HOST:30808/health" > /dev/null; then
    log_info "✓ Agent MCP service is healthy"
else
    log_warn "✗ Agent MCP service health check failed"
fi

# Display deployment info
log_info "Kubernetes deployment completed successfully!"
echo ""
echo "Service URLs (NodePort):"
echo "  Agent Index:  http://$LINODE_HOST:30690"
echo "  Agent Facts:  http://$LINODE_HOST:30800"
echo "  Agent MCP:    http://$LINODE_HOST:30808"
echo ""
echo "Health Check URLs:"
echo "  Agent Index:  http://$LINODE_HOST:30690/health"
echo "  Agent Facts:  http://$LINODE_HOST:30800/health"
echo "  Agent MCP:    http://$LINODE_HOST:30808/health"
echo ""
echo "Kubernetes Management:"
echo "  View pods:    ssh $LINODE_USER@$LINODE_HOST 'k3s kubectl get pods -n nanda-registry'"
echo "  View logs:    ssh $LINODE_USER@$LINODE_HOST 'k3s kubectl logs -f deployment/agent-index -n nanda-registry'"
echo "  Scale:        ssh $LINODE_USER@$LINODE_HOST 'k3s kubectl scale deployment/agent-index --replicas=3 -n nanda-registry'"
echo "  Delete:       ssh $LINODE_USER@$LINODE_HOST 'k3s kubectl delete namespace nanda-registry'"
echo "  Update:       Run this script again"
