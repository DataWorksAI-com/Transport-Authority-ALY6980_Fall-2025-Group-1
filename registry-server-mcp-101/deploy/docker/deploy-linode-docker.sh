#!/bin/bash

# NANDA Registry - Linode Docker Deployment Script
# This script deploys the registry server using Docker Compose on a Linode instance

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
    echo "Usage: ATLAS_URL=your_mongodb_url ./deploy-linode-docker.sh"
    exit 1
fi

if [ "$LINODE_HOST" = "your-linode-ip" ]; then
    log_error "Please set LINODE_HOST environment variable"
    echo "Usage: LINODE_HOST=your-ip ATLAS_URL=your_mongodb_url ./deploy-linode-docker.sh"
    exit 1
fi

log_info "Starting Docker deployment to Linode: $LINODE_HOST"

# Test SSH connection
log_info "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$LINODE_USER@$LINODE_HOST" "echo 'SSH connection successful'"; then
    log_error "Cannot connect to Linode instance"
    exit 1
fi

# Install Docker and Docker Compose on Linode (if not already installed)
log_info "Installing Docker and Docker Compose..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    # Update system
    apt-get update
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        systemctl start docker
        rm get-docker.sh
    else
        echo "Docker already installed"
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        echo "Docker Compose already installed"
    fi
    
    # Create app directory
    mkdir -p /opt/nanda-registry
ENDSSH

# Copy application files to Linode
log_info "Copying application files to Linode..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" "rm -rf /opt/nanda-registry/*"
scp -i "$SSH_KEY" -r ../../src "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"
scp -i "$SSH_KEY" ../../requirements.txt "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"
scp -i "$SSH_KEY" Dockerfile "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"
scp -i "$SSH_KEY" docker-compose.yml "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"

# Create .env file on Linode
log_info "Creating environment configuration..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << ENDSSH
    cat > /opt/nanda-registry/.env << 'EOF'
ATLAS_URL=$ATLAS_URL
EOF
ENDSSH

# Stop existing containers and deploy new ones
log_info "Deploying containers..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    cd /opt/nanda-registry
    
    # Stop and remove existing containers
    docker-compose down || true
    
    # Build and start containers
    docker-compose build --no-cache
    docker-compose up -d
    
    # Wait for services to be healthy
    echo "Waiting for services to start..."
    sleep 10
    
    # Check container status
    docker-compose ps
ENDSSH

# Configure firewall
log_info "Configuring firewall..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    # Configure firewall rules
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 6900/tcp  # Agent Index
    ufw allow 8000/tcp  # Agent Facts
    ufw allow 8080/tcp  # Agent MCP
    ufw reload
ENDSSH

# Test services
log_info "Testing deployed services..."
sleep 5

log_info "Testing Agent Index service (port 6900)..."
if curl -f -s "http://$LINODE_HOST:6900/health" > /dev/null; then
    log_info "✓ Agent Index service is healthy"
else
    log_warn "✗ Agent Index service health check failed"
fi

log_info "Testing Agent Facts service (port 8000)..."
if curl -f -s "http://$LINODE_HOST:8000/health" > /dev/null; then
    log_info "✓ Agent Facts service is healthy"
else
    log_warn "✗ Agent Facts service health check failed"
fi

log_info "Testing Agent MCP service (port 8080)..."
if curl -f -s "http://$LINODE_HOST:8080/health" > /dev/null; then
    log_info "✓ Agent MCP service is healthy"
else
    log_warn "✗ Agent MCP service health check failed"
fi

# Display deployment info
log_info "Deployment completed successfully!"
echo ""
echo "Service URLs:"
echo "  Agent Index:  http://$LINODE_HOST:6900"
echo "  Agent Facts:  http://$LINODE_HOST:8000"
echo "  Agent MCP:    http://$LINODE_HOST:8080"
echo ""
echo "Health Check URLs:"
echo "  Agent Index:  http://$LINODE_HOST:6900/health"
echo "  Agent Facts:  http://$LINODE_HOST:8000/health"
echo "  Agent MCP:    http://$LINODE_HOST:8080/health"
echo ""
echo "Container Management:"
echo "  View logs:    ssh $LINODE_USER@$LINODE_HOST 'cd /opt/nanda-registry && docker-compose logs -f'"
echo "  Restart:      ssh $LINODE_USER@$LINODE_HOST 'cd /opt/nanda-registry && docker-compose restart'"
echo "  Stop:         ssh $LINODE_USER@$LINODE_HOST 'cd /opt/nanda-registry && docker-compose down'"
echo "  Update:       Run this script again"
