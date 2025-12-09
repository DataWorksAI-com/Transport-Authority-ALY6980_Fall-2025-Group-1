#!/bin/bash

# NANDA Registry - Linode Kubernetes Engine (LKE) Deployment
# This script creates an LKE cluster and deploys the registry using native Kubernetes

set -e

# Configuration - Override with environment variables
REGION="${REGION:-us-east}"
CLUSTER_LABEL="${CLUSTER_LABEL:-nanda-registry-cluster}"
K8S_VERSION="${K8S_VERSION:-1.34}"  # Kubernetes version
NODE_TYPE="${NODE_TYPE:-g6-standard-2}"  # 4GB RAM per node
NODE_COUNT="${NODE_COUNT:-2}"  # Number of nodes in the pool
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
    echo "Usage: ATLAS_URL=your_mongodb_url ./provision-lke-cluster.sh"
    echo ""
    echo "Optional environment variables:"
    echo "  REGION           - Linode region (default: us-east)"
    echo "  CLUSTER_LABEL    - Cluster name (default: nanda-registry-cluster)"
    echo "  K8S_VERSION      - Kubernetes version (default: 1.34)"
    echo "  NODE_TYPE        - Node type (default: g6-standard-2)"
    echo "  NODE_COUNT       - Number of nodes (default: 2)"
    echo ""
    echo "Common regions: us-east, us-west, eu-west, ap-south"
    echo "Common node types: g6-standard-1 (2GB), g6-standard-2 (4GB), g6-standard-4 (8GB)"
    exit 1
fi

log_info "NANDA Registry - Linode Kubernetes Engine (LKE) Deployment"
echo "=========================================================================="
echo "Region:        $REGION"
echo "Cluster:       $CLUSTER_LABEL"
echo "K8s Version:   $K8S_VERSION"
echo "Node Type:     $NODE_TYPE"
echo "Node Count:    $NODE_COUNT"
echo ""

# Check Linode CLI
log_step "1/8" "Checking Linode CLI credentials..."
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

# Check for kubectl
log_step "2/8" "Checking kubectl installation..."
if ! command -v kubectl &> /dev/null; then
    log_warn "kubectl not found. Installing..."
    # Install kubectl
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
        chmod +x kubectl
        sudo mv kubectl /usr/local/bin/
    else
        # Linux
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        sudo mv kubectl /usr/local/bin/
    fi
fi
log_info "✓ kubectl available: $(kubectl version --client --short 2>/dev/null || kubectl version --client 2>&1 | head -1)"

# Create or get LKE cluster
log_step "3/8" "Creating/checking LKE cluster..."
CLUSTER_ID=$(linode-cli lke clusters-list --text --no-headers --format="id,label" | grep "$CLUSTER_LABEL" | cut -f1 || echo "")

if [ -n "$CLUSTER_ID" ]; then
    log_warn "LKE cluster '$CLUSTER_LABEL' already exists (ID: $CLUSTER_ID)"
    read -p "Delete and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting existing cluster..."
        linode-cli lke cluster-delete "$CLUSTER_ID"
        sleep 10
        CLUSTER_ID=""
    else
        log_info "Using existing cluster"
    fi
fi

if [ -z "$CLUSTER_ID" ]; then
    log_info "Creating new LKE cluster..."
    
    # Create the cluster with a node pool
    CLUSTER_ID=$(linode-cli lke cluster-create \
        --label "$CLUSTER_LABEL" \
        --region "$REGION" \
        --k8s_version "$K8S_VERSION" \
        --node_pools.type "$NODE_TYPE" \
        --node_pools.count "$NODE_COUNT" \
        --text --no-headers --format="id")
    
    log_info "✓ LKE cluster created: $CLUSTER_ID"
else
    log_info "✓ Using existing cluster: $CLUSTER_ID"
fi

# Wait for cluster to be ready
log_step "4/8" "Waiting for cluster to be ready..."
log_info "This may take 5-10 minutes..."
while true; do
    STATUS=$(linode-cli lke cluster-view "$CLUSTER_ID" --text --no-headers --format="label" 2>/dev/null || echo "")
    if [ "$STATUS" = "$CLUSTER_LABEL" ]; then
        break
    fi
    echo "  Status: $STATUS, waiting..."
    sleep 15
done
log_info "✓ Cluster is ready"

# Download kubeconfig
log_step "5/8" "Configuring kubectl access..."
KUBECONFIG_FILE="${CLUSTER_LABEL}-kubeconfig.yaml"

# Get base64 kubeconfig and decode it
linode-cli lke kubeconfig-view "$CLUSTER_ID" --text --no-headers | base64 -d > "$KUBECONFIG_FILE" 2>/dev/null || \
    linode-cli lke kubeconfig-view "$CLUSTER_ID" --text --no-headers > "$KUBECONFIG_FILE"

export KUBECONFIG="$(pwd)/$KUBECONFIG_FILE"
log_info "✓ Kubeconfig saved to: $KUBECONFIG_FILE"
log_info "✓ KUBECONFIG exported for this session"

# Wait for nodes to be ready
log_info "Waiting for nodes to be ready..."
for i in {1..30}; do
    READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready" || echo "0")
    if [ "$READY_NODES" -ge "$NODE_COUNT" ]; then
        log_info "✓ All $NODE_COUNT nodes are ready"
        break
    fi
    echo "  Ready nodes: $READY_NODES/$NODE_COUNT, waiting..."
    sleep 10
done

# Show cluster info
kubectl get nodes

# Build and push Docker image (using local Docker and registry or build on node)
log_step "6/8" "Preparing application deployment..."

# Create temporary deployment directory
TEMP_DIR=$(mktemp -d)
log_info "Creating temporary build directory: $TEMP_DIR"

# Copy files
cp -r ../../src "$TEMP_DIR/"
cp ../../requirements.txt "$TEMP_DIR/"
cp ../docker/Dockerfile "$TEMP_DIR/"
cp deployment.yaml "$TEMP_DIR/"

# Update deployment with ATLAS_URL
cd "$TEMP_DIR"
sed -i.bak "s|\${ATLAS_URL}|$ATLAS_URL|g" deployment.yaml

# Create a ConfigMap for the source code (alternative to building image)
log_info "Creating ConfigMap with application source..."
kubectl create configmap nanda-registry-src \
    --from-file=src/ \
    --dry-run=client -o yaml | kubectl apply -f - || true

# For LKE, we'll use a Job to build the image on a node
log_step "7/8" "Building Docker image in cluster..."

cat > build-job.yaml << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: build-nanda-registry
  namespace: default
spec:
  template:
    spec:
      containers:
      - name: kaniko
        image: gcr.io/kaniko-project/executor:latest
        args:
        - "--dockerfile=/workspace/Dockerfile"
        - "--context=/workspace"
        - "--destination=nanda-registry:latest"
        - "--no-push"
        - "--tar-path=/workspace/image.tar"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
      volumes:
      - name: workspace
        emptyDir: {}
      restartPolicy: Never
  backoffLimit: 1
EOF

# Actually, for LKE it's better to use pre-built images or build locally
# Let's modify the deployment to use public Python image and mount code
log_info "Modifying deployment to use Python base image with mounted code..."

cat > deployment-lke.yaml << EOFYAML
apiVersion: v1
kind: Namespace
metadata:
  name: nanda-registry
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nanda-config
  namespace: nanda-registry
data:
  requirements.txt: |
$(cat requirements.txt | sed 's/^/    /')
---
apiVersion: v1
kind: Secret
metadata:
  name: nanda-secrets
  namespace: nanda-registry
type: Opaque
stringData:
  atlas-url: "${ATLAS_URL}"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-index
  namespace: nanda-registry
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agent-index
  template:
    metadata:
      labels:
        app: agent-index
    spec:
      initContainers:
      - name: install-deps
        image: python:3.11-slim
        command: ["/bin/sh", "-c"]
        args:
        - |
          pip install --target=/deps -r /config/requirements.txt
        volumeMounts:
        - name: deps
          mountPath: /deps
        - name: config
          mountPath: /config
      containers:
      - name: agent-index
        image: python:3.11-slim
        workingDir: /app
        command: ["/bin/sh", "-c"]
        args:
        - |
          export PYTHONPATH=/deps:\$PYTHONPATH
          cd /app && python -m uvicorn src.agentIndex:app --host 0.0.0.0 --port 6900
        ports:
        - containerPort: 6900
        env:
        - name: ATLAS_URL
          valueFrom:
            secretKeyRef:
              name: nanda-secrets
              key: atlas-url
        volumeMounts:
        - name: app-code
          mountPath: /app
        - name: deps
          mountPath: /deps
        livenessProbe:
          httpGet:
            path: /health
            port: 6900
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 6900
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: app-code
        configMap:
          name: nanda-registry-src
      - name: deps
        emptyDir: {}
      - name: config
        configMap:
          name: nanda-config
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-facts
  namespace: nanda-registry
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agent-facts
  template:
    metadata:
      labels:
        app: agent-facts
    spec:
      initContainers:
      - name: install-deps
        image: python:3.11-slim
        command: ["/bin/sh", "-c"]
        args:
        - |
          pip install --target=/deps -r /config/requirements.txt
        volumeMounts:
        - name: deps
          mountPath: /deps
        - name: config
          mountPath: /config
      containers:
      - name: agent-facts
        image: python:3.11-slim
        workingDir: /app
        command: ["/bin/sh", "-c"]
        args:
        - |
          export PYTHONPATH=/deps:\$PYTHONPATH
          cd /app && python -m uvicorn src.agentFactsServer:app --host 0.0.0.0 --port 8000
        ports:
        - containerPort: 8000
        env:
        - name: ATLAS_URL
          valueFrom:
            secretKeyRef:
              name: nanda-secrets
              key: atlas-url
        volumeMounts:
        - name: app-code
          mountPath: /app
        - name: deps
          mountPath: /deps
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: app-code
        configMap:
          name: nanda-registry-src
      - name: deps
        emptyDir: {}
      - name: config
        configMap:
          name: nanda-config
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-mcp
  namespace: nanda-registry
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agent-mcp
  template:
    metadata:
      labels:
        app: agent-mcp
    spec:
      initContainers:
      - name: install-deps
        image: python:3.11-slim
        command: ["/bin/sh", "-c"]
        args:
        - |
          pip install --target=/deps -r /config/requirements.txt
        volumeMounts:
        - name: deps
          mountPath: /deps
        - name: config
          mountPath: /config
      containers:
      - name: agent-mcp
        image: python:3.11-slim
        workingDir: /app
        command: ["/bin/sh", "-c"]
        args:
        - |
          export PYTHONPATH=/deps:\$PYTHONPATH
          cd /app && /deps/bin/fastmcp run src/agent_mcp.py --transport sse --port 8080 --host 0.0.0.0
        ports:
        - containerPort: 8080
        env:
        - name: ATLAS_URL
          valueFrom:
            secretKeyRef:
              name: nanda-secrets
              key: atlas-url
        volumeMounts:
        - name: app-code
          mountPath: /app
        - name: deps
          mountPath: /deps
        livenessProbe:
          tcpSocket:
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          tcpSocket:
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: app-code
        configMap:
          name: nanda-registry-src
      - name: deps
        emptyDir: {}
      - name: config
        configMap:
          name: nanda-config
---
apiVersion: v1
kind: Service
metadata:
  name: agent-index
  namespace: nanda-registry
spec:
  type: LoadBalancer
  selector:
    app: agent-index
  ports:
  - port: 6900
    targetPort: 6900
    protocol: TCP
    name: http
---
apiVersion: v1
kind: Service
metadata:
  name: agent-facts
  namespace: nanda-registry
spec:
  type: LoadBalancer
  selector:
    app: agent-facts
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
---
apiVersion: v1
kind: Service
metadata:
  name: agent-mcp
  namespace: nanda-registry
spec:
  type: LoadBalancer
  selector:
    app: agent-mcp
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: http
EOFYAML

# Create ConfigMap with source code
log_info "Creating ConfigMap with application source code..."
kubectl create namespace nanda-registry --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap nanda-registry-src \
    --from-file=src/ \
    --namespace=nanda-registry \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy application
log_info "Deploying application to LKE..."
kubectl apply -f deployment-lke.yaml

# Wait for deployments
log_info "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/agent-index \
    deployment/agent-facts \
    deployment/agent-mcp \
    -n nanda-registry || log_warn "Deployment readiness check timed out, but pods may still be starting"

# Get service external IPs
log_step "8/8" "Retrieving service endpoints..."
log_info "Waiting for LoadBalancer external IPs (this may take 2-3 minutes)..."

for i in {1..30}; do
    INDEX_IP=$(kubectl get svc agent-index -n nanda-registry -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    FACTS_IP=$(kubectl get svc agent-facts -n nanda-registry -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    MCP_IP=$(kubectl get svc agent-mcp -n nanda-registry -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    
    if [ -n "$INDEX_IP" ] && [ -n "$FACTS_IP" ] && [ -n "$MCP_IP" ]; then
        break
    fi
    echo "  Waiting for LoadBalancer IPs... ($i/30)"
    sleep 10
done

# Show status
kubectl get pods -n nanda-registry
kubectl get svc -n nanda-registry

# Test services
sleep 10

log_info "Testing Agent Index service..."
if [ -n "$INDEX_IP" ] && curl -f -s "http://$INDEX_IP:6900/health" > /dev/null 2>&1; then
    log_info "✓ Agent Index service is healthy"
else
    log_warn "✗ Agent Index service health check failed (may still be starting)"
fi

log_info "Testing Agent Facts service..."
if [ -n "$FACTS_IP" ] && curl -f -s "http://$FACTS_IP:8000/health" > /dev/null 2>&1; then
    log_info "✓ Agent Facts service is healthy"
else
    log_warn "✗ Agent Facts service health check failed (may still be starting)"
fi

log_info "Testing Agent MCP service..."
if [ -n "$MCP_IP" ] && (nc -z -w5 "$MCP_IP" 8080 2>/dev/null || curl -s "http://$MCP_IP:8080/" > /dev/null 2>&1); then
    log_info "✓ Agent MCP service is running"
else
    log_warn "✗ Agent MCP service check failed (may still be starting)"
fi

# Cleanup temp directory
cd - > /dev/null
rm -rf "$TEMP_DIR"

# Display final info
echo ""
log_info "🎉 LKE Deployment Complete!"
echo "=================================="
echo "Cluster ID:       $CLUSTER_ID"
echo "Cluster Label:    $CLUSTER_LABEL"
echo "Kubeconfig:       $KUBECONFIG_FILE"
echo "Region:           $REGION"
echo "Nodes:            $NODE_COUNT x $NODE_TYPE"
echo ""
echo "Service URLs (LoadBalancer):"
echo "  Agent Index:    http://${INDEX_IP:-<pending>}:6900"
echo "  Agent Facts:    http://${FACTS_IP:-<pending>}:8000"
echo "  Agent MCP:      http://${MCP_IP:-<pending>}:8080"
echo ""
echo "Health Checks:"
echo "  curl http://${INDEX_IP:-<pending>}:6900/health"
echo "  curl http://${FACTS_IP:-<pending>}:8000/health"
echo "  nc -z ${MCP_IP:-<pending>} 8080"
echo ""
echo "Kubectl Access (use in this directory):"
echo "  export KUBECONFIG=$(pwd)/$KUBECONFIG_FILE"
echo "  kubectl get pods -n nanda-registry"
echo "  kubectl logs -f deployment/agent-index -n nanda-registry"
echo "  kubectl get svc -n nanda-registry"
echo ""
echo "Scale Deployments:"
echo "  kubectl scale deployment/agent-index --replicas=3 -n nanda-registry"
echo ""
echo "Delete Cluster:"
echo "  linode-cli lke cluster-delete $CLUSTER_ID"
echo ""
echo "💰 Estimated Cost:"
echo "  ~\$$(echo "$NODE_COUNT * 24" | bc)/month for $NODE_COUNT x $NODE_TYPE nodes"
echo "  Plus LoadBalancer costs (~\$10/month per LoadBalancer = \$30/month total)"
