# Deployment Guide

This project includes a GitHub Actions workflow for automated deployment to your production server.

## Prerequisites

1. **SSH Access**: Ensure you have SSH access to your production server (46.62.134.177)
2. **Docker & Docker Compose**: Make sure Docker and Docker Compose are installed on your server
3. **GitHub Repository**: Your code should be in a GitHub repository

## GitHub Secrets Setup

You need to configure the following secrets in your GitHub repository:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following repository secrets:

### Required Secrets

- `SSH_USERNAME`: The username for SSH access to your server
- `SSH_PRIVATE_KEY`: Your private SSH key (the entire key content, including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)
- `SSH_PORT`: The SSH port (usually 22)

### Optional Secrets

- `MONGO_URI`: Your MongoDB connection string (if not already set in your server environment)

## How the Deployment Works

The workflow (`/.github/workflows/deploy.yml`) will:

1. **Trigger**: Run on pushes to `main` or `master` branch, or manually via workflow dispatch
2. **SSH Connection**: Connect to your server using the provided credentials
3. **Code Update**: Clone the repository (if first time) or pull latest changes
4. **Docker Deployment**: Stop existing containers, build new images, and start the application
5. **Health Check**: Verify the application is running on port 3000
6. **Cleanup**: Remove old Docker images to save space

## Manual Deployment

You can also trigger deployment manually:

1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Select **Deploy to Production** workflow
4. Click **Run workflow**

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**: 
   - Verify your SSH credentials are correct
   - Ensure the server is accessible from GitHub Actions
   - Check if the SSH port is correct

2. **Docker Build Failed**:
   - Check the Dockerfile and docker-compose.yml files
   - Ensure all required files are present in the repository

3. **Application Not Starting**:
   - Check the application logs: `docker-compose logs`
   - Verify environment variables are set correctly
   - Ensure the MongoDB connection is working

### Server Setup

Make sure your server has:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER
```

## Environment Variables

The application expects the following environment variables on your server:

- `MONGO_URI`: MongoDB connection string
- `ENVIRONMENT`: Set to "production"

You can set these in your server's environment or modify the `docker-compose.yml` file to include them.

## Security Notes

- Keep your SSH private key secure and never commit it to the repository
- Use a dedicated deployment user on your server with limited permissions
- Consider using SSH key rotation for better security
- Monitor your server logs regularly for any security issues 