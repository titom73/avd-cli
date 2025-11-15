#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Docker build script for avd-cli.
#
# This script automatically detects the version from git tags and builds
# the Docker image with proper versioning labels.
#
# Usage:
#     ./docker-build.sh [OPTIONS]
#
# Options:
#     -t, --tag TAG       Override the image tag (default: git describe)
#     -p, --push          Push the image after build
#     -r, --registry REG  Specify registry (e.g., ghcr.io/user)
#     -d, --dev           Build as development version
#     -h, --help          Show this help message
#
# Examples:
#     # Build with auto-detected version
#     ./docker-build.sh
#
#     # Build with custom tag
#     ./docker-build.sh --tag v1.0.0
#
#     # Build and push to registry
#     ./docker-build.sh --push --registry ghcr.io/titom73
#
#     # Build dev version
#     ./docker-build.sh --dev

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PUSH=false
DEV=false
REGISTRY=""
CUSTOM_TAG=""
IMAGE_NAME="avd-cli"

# Function to print colored output
log_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to show help
show_help() {
    cat << 'EOF'
Docker build script for avd-cli

This script automatically detects the version from git tags and builds
the Docker image with proper versioning labels.

Usage:
    ./docker-build.sh [OPTIONS]

Options:
    -t, --tag TAG       Override the image tag (default: git describe)
    -p, --push          Push the image after build
    -r, --registry REG  Specify registry (e.g., ghcr.io/user)
    -d, --dev           Build as development version
    -h, --help          Show this help message

Examples:
    # Build with auto-detected version
    ./docker-build.sh

    # Build with custom tag
    ./docker-build.sh --tag v1.0.0

    # Build and push to registry
    ./docker-build.sh --push --registry ghcr.io/titom73

    # Build dev version
    ./docker-build.sh --dev
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            CUSTOM_TAG="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -d|--dev)
            DEV=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Detect version information
if [ "$DEV" = true ]; then
    VERSION="dev"
    REVISION="dev"
    IMAGE_TAG="dev"
    log_info "Building development version"
else
    # Try to get version from git
    if git rev-parse --git-dir > /dev/null 2>&1; then
        # Get version (tag or describe)
        if [ -n "$CUSTOM_TAG" ]; then
            VERSION="$CUSTOM_TAG"
            IMAGE_TAG="$CUSTOM_TAG"
        else
            VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
            IMAGE_TAG="$VERSION"
        fi
        
        # Get commit SHA
        REVISION=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        
        log_info "Detected version from git: $VERSION"
    else
        log_warning "Not in a git repository, using 'dev' version"
        VERSION="dev"
        REVISION="unknown"
        IMAGE_TAG="dev"
    fi
fi

# Build date (ISO 8601)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Construct full image name with registry
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

# Display build information
log_info "Build configuration:"
echo "  Version:    $VERSION"
echo "  Revision:   ${REVISION:0:7}"
echo "  Build date: $BUILD_DATE"
echo "  Image tag:  $IMAGE_TAG"
echo "  Full name:  $FULL_IMAGE_NAME:$IMAGE_TAG"

# Build Docker image
log_info "Building Docker image..."

docker build \
    --build-arg VERSION="$VERSION" \
    --build-arg REVISION="$REVISION" \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    -t "${FULL_IMAGE_NAME}:${IMAGE_TAG}" \
    -t "${FULL_IMAGE_NAME}:latest" \
    .

if [ $? -eq 0 ]; then
    log_success "Docker image built successfully"
    log_success "Tags: ${FULL_IMAGE_NAME}:${IMAGE_TAG}, ${FULL_IMAGE_NAME}:latest"
else
    log_error "Docker build failed"
    exit 1
fi

# Show image labels
log_info "Image labels:"
docker inspect "${FULL_IMAGE_NAME}:${IMAGE_TAG}" \
    --format='  Version:  {{index .Config.Labels "org.opencontainers.image.version"}}' 2>/dev/null || true
docker inspect "${FULL_IMAGE_NAME}:${IMAGE_TAG}" \
    --format='  Revision: {{index .Config.Labels "org.opencontainers.image.revision"}}' 2>/dev/null || true
docker inspect "${FULL_IMAGE_NAME}:${IMAGE_TAG}" \
    --format='  Created:  {{index .Config.Labels "org.opencontainers.image.created"}}' 2>/dev/null || true

# Push if requested
if [ "$PUSH" = true ]; then
    log_info "Pushing images to registry..."
    
    docker push "${FULL_IMAGE_NAME}:${IMAGE_TAG}"
    docker push "${FULL_IMAGE_NAME}:latest"
    
    if [ $? -eq 0 ]; then
        log_success "Images pushed successfully"
    else
        log_error "Failed to push images"
        exit 1
    fi
fi

log_success "Done!"
echo ""
log_info "To run the container:"
echo "  docker run --rm -it ${FULL_IMAGE_NAME}:${IMAGE_TAG} --help"
