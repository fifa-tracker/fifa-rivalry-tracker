#!/bin/bash

# FIFA Rivalry Tracker - Nginx Setup Script
# This script copies the nginx configuration to the VM and sets it up

set -e

echo "Setting up nginx configuration for FIFA Rivalry Tracker..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Copy nginx configuration
echo "Copying nginx configuration..."
cp "$PROJECT_ROOT/nginx/default" /etc/nginx/sites-available/default

# Test nginx configuration
echo "Testing nginx configuration..."
if nginx -t; then
    echo "Nginx configuration test passed"
else
    echo "Nginx configuration test failed"
    exit 1
fi

# Reload nginx
echo "Reloading nginx..."
systemctl reload nginx

echo "Nginx configuration has been successfully set up!"
echo "The FIFA Rivalry Tracker should now be accessible via nginx proxy" 