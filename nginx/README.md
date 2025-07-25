# Nginx Configuration for FIFA Rivalry Tracker

This directory contains the nginx configuration for the FIFA Rivalry Tracker application.

## Files

- `default` - Main nginx configuration file
- `README.md` - This documentation file

## Configuration Overview

The nginx configuration provides:

1. **HTTP Server (Port 80)**: Serves content directly without redirects
2. **HTTPS Server (Port 443)**: Optional SSL configuration for secure connections
3. **Proxy Configuration**: Routes traffic to the Docker container running on port 3000
4. **WebSocket Support**: Enables real-time communication
5. **Static File Caching**: Optimizes performance for static assets
6. **Health Check Endpoint**: Dedicated endpoint for monitoring
7. **API Routing**: Proper handling of API requests

## Setup Instructions

### GitHub Workflow (Recommended)

The nginx configuration is automatically set up as part of the deployment workflow. When you push to the main branch, the workflow will:

1. Deploy the application
2. Set up nginx configuration
3. Verify nginx is running and proxying correctly

You can also run the nginx setup independently using the "Setup Nginx Configuration" workflow in the GitHub Actions tab.

### Manual Setup

Run the setup script on your VM:

```bash
sudo ./scripts/setup_nginx.sh
```

### Manual Setup

1. Copy the configuration to nginx:
   ```bash
   sudo cp nginx/default /etc/nginx/sites-available/default
   ```

2. Test the configuration:
   ```bash
   sudo nginx -t
   ```

3. Reload nginx:
   ```bash
   sudo systemctl reload nginx
   ```

## SSL Certificate Setup (Optional)

If you want to use HTTPS, you'll need to generate SSL certificates:

```bash
# Generate self-signed certificate (for development)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt
```

For production, use proper SSL certificates from a certificate authority.

## Port Configuration

The configuration expects the FIFA Rivalry Tracker to be running on port 3000. Make sure your Docker container is configured to expose this port.

## Troubleshooting

1. **Check nginx status**: `sudo systemctl status nginx`
2. **View nginx logs**: `sudo tail -f /var/log/nginx/error.log`
3. **Test configuration**: `sudo nginx -t`
4. **Check port availability**: `sudo netstat -tlnp | grep :80`

## Security Notes

- The configuration includes proper headers for proxy forwarding
- Real IP detection is configured for accurate client IP logging
- Static files have appropriate caching headers
- Health check endpoint has access logging disabled for performance 