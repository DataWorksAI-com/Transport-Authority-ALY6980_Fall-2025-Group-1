#!/bin/bash

# NANDA Registry - Linode Simple Deployment Script
# This script deploys the registry server as simple Python processes on a single Linode instance

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
    echo "Usage: ATLAS_URL=your_mongodb_url ./deploy-linode-simple.sh"
    exit 1
fi

if [ "$LINODE_HOST" = "your-linode-ip" ]; then
    log_error "Please set LINODE_HOST environment variable"
    echo "Usage: LINODE_HOST=your-ip ATLAS_URL=your_mongodb_url ./deploy-linode-simple.sh"
    exit 1
fi

log_info "Starting simple deployment to Linode: $LINODE_HOST"

# Test SSH connection
log_info "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$LINODE_USER@$LINODE_HOST" "echo 'SSH connection successful'"; then
    log_error "Cannot connect to Linode instance"
    exit 1
fi

# Install system dependencies on Linode
log_info "Installing system dependencies..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install Python 3.11 and pip
    apt-get install -y python3.11 python3.11-venv python3-pip curl
    
    # Create app directory
    mkdir -p /opt/nanda-registry
    
    # Create virtual environment
    cd /opt/nanda-registry
    python3.11 -m venv venv
ENDSSH

# Copy application files to Linode
log_info "Copying application files to Linode..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" "rm -rf /opt/nanda-registry/src"
scp -i "$SSH_KEY" -r ../../src "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"
scp -i "$SSH_KEY" ../../requirements.txt "$LINODE_USER@$LINODE_HOST:/opt/nanda-registry/"

# Install Python dependencies
log_info "Installing Python dependencies..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    cd /opt/nanda-registry
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
ENDSSH

# Create environment file
log_info "Creating environment configuration..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << ENDSSH
    cat > /opt/nanda-registry/.env << 'EOF'
ATLAS_URL=$ATLAS_URL
EOF
ENDSSH

# Create systemd service files
log_info "Creating systemd services..."

# Agent Index Service
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    cat > /etc/systemd/system/nanda-agent-index.service << 'EOF'
[Unit]
Description=NANDA Agent Index Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nanda-registry
EnvironmentFile=/opt/nanda-registry/.env
ExecStart=/opt/nanda-registry/venv/bin/uvicorn src.agentIndex:app --host 0.0.0.0 --port 6900
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
ENDSSH

# Agent Facts Service
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    cat > /etc/systemd/system/nanda-agent-facts.service << 'EOF'
[Unit]
Description=NANDA Agent Facts Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nanda-registry
EnvironmentFile=/opt/nanda-registry/.env
ExecStart=/opt/nanda-registry/venv/bin/uvicorn src.agentFactsServer:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
ENDSSH

# Agent MCP Service
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    cat > /etc/systemd/system/nanda-agent-mcp.service << 'EOF'
[Unit]
Description=NANDA Agent MCP Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nanda-registry
EnvironmentFile=/opt/nanda-registry/.env
ExecStart=/opt/nanda-registry/venv/bin/fastmcp run src/agent_mcp.py --transport sse --port 8080 --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
ENDSSH

# Reload systemd and start services
log_info "Starting services..."
ssh -i "$SSH_KEY" "$LINODE_USER@$LINODE_HOST" << 'ENDSSH'
    # Reload systemd
    systemctl daemon-reload
    
    # Stop existing services if running
    systemctl stop nanda-agent-index || true
    systemctl stop nanda-agent-facts || true
    systemctl stop nanda-agent-mcp || true
    
    # Enable and start services
    systemctl enable nanda-agent-index
    systemctl enable nanda-agent-facts
    systemctl enable nanda-agent-mcp
    
    systemctl start nanda-agent-index
    systemctl start nanda-agent-facts
    systemctl start nanda-agent-mcp
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    echo "Service status:"
    systemctl status nanda-agent-index --no-pager || true
    systemctl status nanda-agent-facts --no-pager || true
    systemctl status nanda-agent-mcp --no-pager || true
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
log_info "Simple deployment completed successfully!"
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
echo "Service Management:"
echo "  View logs:    ssh $LINODE_USER@$LINODE_HOST 'journalctl -u nanda-agent-index -f'"
echo "  Restart:      ssh $LINODE_USER@$LINODE_HOST 'systemctl restart nanda-agent-index'"
echo "  Status:       ssh $LINODE_USER@$LINODE_HOST 'systemctl status nanda-agent-*'"
echo "  Stop:         ssh $LINODE_USER@$LINODE_HOST 'systemctl stop nanda-agent-*'"
echo "  Update:       Run this script again"
echo ""
echo "All services:"
echo "  Stop all:     ssh $LINODE_USER@$LINODE_HOST 'systemctl stop nanda-agent-{index,facts,mcp}'"
echo "  Start all:    ssh $LINODE_USER@$LINODE_HOST 'systemctl start nanda-agent-{index,facts,mcp}'"
echo "  Restart all:  ssh $LINODE_USER@$LINODE_HOST 'systemctl restart nanda-agent-{index,facts,mcp}'"
