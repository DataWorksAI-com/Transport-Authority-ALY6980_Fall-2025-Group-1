#!/bin/bash

# NANDA Registry - Linode Kubernetes Deployment with Infrastructure Provisioning
# This script creates a Linode instance and deploys the registry using k3s

set -e

# Configuration - Override with environment variables
REGION="${REGION:-us-east}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g6-standard-4}"  # 8GB RAM recommended for k3s
INSTANCE_LABEL="${INSTANCE_LABEL:-nanda-registry-k8s}"
IMAGE_ID="${IMAGE_ID:-linode/ubuntu25.04}"
FIREWALL_LABEL="${FIREWALL_LABEL:-nanda-registry-k8s-firewall}"
SSH_KEY_LABEL="${SSH_KEY_LABEL:-nanda-registry-key}"
ROOT_PASSWORD="${ROOT_PASSWORD:-}"
ATLAS_URL="${ATLAS_URL}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[$1]${NC} $2"
}

# Validate environment
if [ -z "$ATLAS_URL" ]; then
    log_error "ATLAS_URL environment variable is not set"
    echo ""
    echo "Usage: ATLAS_URL=your_mongodb_url ./provision-and-deploy-k8s.sh"
    echo ""
    echo "Optional environment variables:"
    echo "  REGION           - Linode region (default: us-east)"
    echo "  INSTANCE_TYPE    - Linode plan (default: g6-standard-4)"
    echo "  INSTANCE_LABEL   - Instance label (default: nanda-registry-k8s)"
    echo "  ROOT_PASSWORD    - Root password (auto-generated if not provided)"
    echo ""
    echo "Common regions: us-east, us-west, eu-west, ap-south"
    echo "Common types: g6-standard-2 (4GB), g6-standard-4 (8GB), g6-standard-6 (16GB)"
    exit 1
fi

# Generate secure password if not provided
if [ -z "$ROOT_PASSWORD" ]; then
    ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    log_info "Generated root password: $ROOT_PASSWORD"
fi

log_info "NANDA Registry - Kubernetes Deployment with Infrastructure Provisioning"
echo "=========================================================================="
echo "Region: $REGION"
echo "Instance Type: $INSTANCE_TYPE"
echo "Instance Label: $INSTANCE_LABEL"
echo ""

# Check Linode CLI
log_step "1/9" "Checking Linode CLI credentials..."
if ! linode-cli --version >/dev/null 2>&1; then
    log_error "Linode CLI not installed. Install: https://www.linode.com/docs/products/tools/cli/get-started/"
    exit 1
fi

CONFIG="$HOME/.config/linode-cli"
if [ ! -s "$CONFIG" ] && [ -z "$LINODE_CLI_TOKEN" ]; then
    log_error "Linode CLI not configured. Run 'linode-cli configure' first."
    exit 1
fi
log_info "✓ Linode CLI credentials valid"

# Setup firewall
log_step "2/9" "Setting up firewall..."
FIREWALL_ID=$(linode-cli firewalls list --text --no-headers --format="id,label" | grep "$FIREWALL_LABEL" | cut -f1 || echo "")

if [ -z "$FIREWALL_ID" ]; then
    log_info "Creating firewall..."
    linode-cli firewalls create \
        --label "$FIREWALL_LABEL" \
        --rules.inbound_policy DROP \
        --rules.outbound_policy ACCEPT \
        --rules.inbound '[
            {"protocol": "TCP", "ports": "22", "addresses": {"ipv4": ["0.0.0.0/0"]}, "action": "ACCEPT"},
            {"protocol": "TCP", "ports": "6443", "addresses": {"ipv4": ["0.0.0.0/0"]}, "action": "ACCEPT"},
            {"protocol": "TCP", "ports": "30690", "addresses": {"ipv4": ["0.0.0.0/0"]}, "action": "ACCEPT"},
            {"protocol": "TCP", "ports": "30800", "addresses": {"ipv4": ["0.0.0.0/0"]}, "action": "ACCEPT"},
            {"protocol": "TCP", "ports": "30808", "addresses": {"ipv4": ["0.0.0.0/0"]}, "action": "ACCEPT"}
        ]' > /dev/null

    FIREWALL_ID=$(linode-cli firewalls list --text --no-headers --format="id,label" | grep "$FIREWALL_LABEL" | cut -f1)
fi
log_info "✓ Firewall ID: $FIREWALL_ID"

# Setup SSH key
log_step "3/9" "Setting up SSH key..."
if [ ! -f "${SSH_KEY_LABEL}.pub" ]; then
    log_info "Generating SSH key pair..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_LABEL" -N "" -C "nanda-registry"
fi
log_info "✓ SSH key: ${SSH_KEY_LABEL}"

# Create Linode instance
log_step "4/9" "Creating Linode instance..."
INSTANCE_ID=$(linode-cli linodes list --label "$INSTANCE_LABEL" --text --no-headers --format="id" | head -n1)

if [ -n "$INSTANCE_ID" ]; then
    log_warn "Instance '$INSTANCE_LABEL' already exists (ID: $INSTANCE_ID)"
    read -p "Delete and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting existing instance..."
        linode-cli linodes delete "$INSTANCE_ID"
        sleep 5
        INSTANCE_ID=""
    else
        log_info "Using existing instance"
    fi
fi

if [ -z "$INSTANCE_ID" ]; then
    log_info "Launching new instance..."
    INSTANCE_ID=$(linode-cli linodes create \
        --type "$INSTANCE_TYPE" \
        --region "$REGION" \
        --image "$IMAGE_ID" \
        --label "$INSTANCE_LABEL" \
        --tags "nanda-registry,kubernetes,k3s" \
        --root_pass "$ROOT_PASSWORD" \
        --authorized_keys "$(cat ${SSH_KEY_LABEL}.pub)" \
        --firewall_id "$FIREWALL_ID" \
        --text --no-headers --format="id")
    log_info "✓ Instance created: $INSTANCE_ID"
fi

# Wait for instance to be running
log_step "5/9" "Waiting for instance to be ready..."
while true; do
    STATUS=$(linode-cli linodes view "$INSTANCE_ID" --text --no-headers --format="status")
    if [ "$STATUS" = "running" ]; then
        break
    fi
    echo "  Status: $STATUS, waiting..."
    sleep 10
done

# Get public IP
PUBLIC_IP=$(linode-cli linodes view "$INSTANCE_ID" --text --no-headers --format="ipv4")
log_info "✓ Instance running at: $PUBLIC_IP"

# Wait for SSH to be available
log_step "6/9" "Waiting for SSH to be available..."
for i in {1..30}; do
    if ssh -i "$SSH_KEY_LABEL" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "root@$PUBLIC_IP" "echo 'SSH ready'" 2>/dev/null; then
        log_info "✓ SSH connection established"
        break
    fi
    echo "  Attempt $i/30..."
    sleep 10
done

# Install k3s and Docker
log_step "7/9" "Installing k3s and Docker..."
ssh -i "$SSH_KEY_LABEL" -o StrictHostKeyChecking=no "root@$PUBLIC_IP" << 'ENDSSH'
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install k3s
    if ! command -v k3s &> /dev/null; then
        echo "Installing k3s..."
        curl -sfL https://get.k3s.io | sh -
        sleep 15
        echo "alias kubectl='k3s kubectl'" >> ~/.bashrc
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

# Copy application files
log_step "8/9" "Copying application files and building image..."
log_info "Copying files..."
scp -i "$SSH_KEY_LABEL" -o StrictHostKeyChecking=no -r ../../src "root@$PUBLIC_IP:/opt/nanda-registry/"
scp -i "$SSH_KEY_LABEL" -o StrictHostKeyChecking=no ../../requirements.txt "root@$PUBLIC_IP:/opt/nanda-registry/"
scp -i "$SSH_KEY_LABEL" -o StrictHostKeyChecking=no ../docker/Dockerfile "root@$PUBLIC_IP:/opt/nanda-registry/"
scp -i "$SSH_KEY_LABEL" -o StrictHostKeyChecking=no deployment.yaml "root@$PUBLIC_IP:/opt/nanda-registry/"

# Build image and deploy to Kubernetes
log_info "Building Docker image and deploying to k3s..."
ssh -i "$SSH_KEY_LABEL" -o StrictHostKeyChecking=no "root@$PUBLIC_IP" << ENDSSH
    cd /opt/nanda-registry
    
    # Build Docker image
    docker build -t nanda-registry:latest -f Dockerfile .
    
    # Import into k3s
    docker save nanda-registry:latest | k3s ctr images import -
    
    # Update deployment with ATLAS_URL
    sed -i 's|\${ATLAS_URL}|$ATLAS_URL|g' deployment.yaml
    
    # Deploy to k3s
    k3s kubectl apply -f deployment.yaml
    
    # Wait for deployments
    echo "Waiting for deployments to be ready..."
    k3s kubectl wait --for=condition=available --timeout=180s \
        deployment/agent-index \
        deployment/agent-facts \
        deployment/agent-mcp \
        -n nanda-registry || true
    
    # Show status
    k3s kubectl get pods -n nanda-registry
    k3s kubectl get services -n nanda-registry
ENDSSH

# Test services
log_step "9/9" "Testing deployed services..."
sleep 10

log_info "Testing Agent Index service (NodePort 30690)..."
if curl -f -s "http://$PUBLIC_IP:30690/health" > /dev/null 2>&1; then
    log_info "✓ Agent Index service is healthy"
else
    log_warn "✗ Agent Index service health check failed"
fi

log_info "Testing Agent Facts service (NodePort 30800)..."
if curl -f -s "http://$PUBLIC_IP:30800/health" > /dev/null 2>&1; then
    log_info "✓ Agent Facts service is healthy"
else
    log_warn "✗ Agent Facts service health check failed"
fi

log_info "Testing Agent MCP service (NodePort 30808)..."
if curl -f -s "http://$PUBLIC_IP:30808/health" > /dev/null 2>&1; then
    log_info "✓ Agent MCP service is running on port 30808"
else
    log_warn "✗ Agent MCP service port 30808 not accessible"
fi

# Display final info
echo ""
log_info "🎉 Kubernetes Deployment Complete!"
echo "=================================="
echo "Instance ID:      $INSTANCE_ID"
echo "Public IP:        $PUBLIC_IP"
echo "Root Password:    $ROOT_PASSWORD"
echo "SSH Key:          ${SSH_KEY_LABEL}"
echo ""
echo "Service URLs (NodePort):"
echo "  Agent Index:    http://$PUBLIC_IP:30690"
echo "  Agent Facts:    http://$PUBLIC_IP:30800"
echo "  Agent MCP:      http://$PUBLIC_IP:30808/sse"
echo ""
echo "Health Checks:"
echo "  curl http://$PUBLIC_IP:30690/health"
echo "  curl http://$PUBLIC_IP:30800/health"
echo "  curl http://$PUBLIC_IP:30808/health"
echo ""
echo "SSH Access:"
echo "  ssh -i ${SSH_KEY_LABEL} root@$PUBLIC_IP"
echo ""
echo "Kubernetes Management:"
echo "  ssh -i ${SSH_KEY_LABEL} root@$PUBLIC_IP 'k3s kubectl get pods -n nanda-registry'"
echo "  ssh -i ${SSH_KEY_LABEL} root@$PUBLIC_IP 'k3s kubectl logs -f deployment/agent-index -n nanda-registry'"
echo "  ssh -i ${SSH_KEY_LABEL} root@$PUBLIC_IP 'k3s kubectl scale deployment/agent-index --replicas=3 -n nanda-registry'"
echo ""
echo "Terminate Instance:"
echo "  linode-cli linodes delete $INSTANCE_ID"
