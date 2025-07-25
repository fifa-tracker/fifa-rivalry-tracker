# GitHub Secrets Setup Guide

This guide will help you set up the required GitHub secrets for your FIFA Rivalry Tracker deployment.

## Required Secrets

You need to add these secrets to your GitHub repository:

### 1. Go to GitHub Repository Settings
1. Navigate to your repository on GitHub
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** for each secret below

### 2. Add These Secrets

#### `MONGO_URI`
- **Value**: Your MongoDB connection string
- **Example**: `mongodb+srv://username:password@cluster.mongodb.net/database`
- **Description**: Connection string for your MongoDB database

#### `SECRET_KEY`
- **Value**: A secure secret key for JWT authentication
- **Example**: Use the generated key from `scripts/generate_secret_key.py`
- **Description**: Used for signing JWT tokens

#### `SSH_USERNAME`
- **Value**: Your server username
- **Example**: `root` or `ubuntu`
- **Description**: Username for SSH access to your deployment server

#### `SSH_PRIVATE_KEY`
- **Value**: Your SSH private key content
- **Example**: The entire content of your private key file
- **Description**: Private key for SSH authentication

#### `SSH_PORT`
- **Value**: SSH port number
- **Example**: `22`
- **Description**: Port for SSH connection (usually 22)

## How to Generate a Secret Key

Run this command to generate a secure secret key:

```bash
python3 scripts/generate_secret_key.py
```

Copy the Base64 encoded key (option 1) for production use.

## How to Get Your SSH Private Key

If you don't have an SSH key pair:

1. **Generate a new key pair**:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
   ```

2. **Copy the public key to your server**:
   ```bash
   ssh-copy-id username@your-server-ip
   ```

3. **Copy the private key content**:
   ```bash
   cat ~/.ssh/id_rsa
   ```
   Copy the entire output (including the BEGIN and END lines).

## Verification

After setting up the secrets:

1. **Test locally**:
   ```bash
   python3 scripts/test_env.py
   ```

2. **Trigger a deployment**:
   - Push to main branch, or
   - Go to Actions tab and manually trigger the workflow

3. **Check deployment logs**:
   - Go to Actions tab
   - Click on the latest deployment
   - Check the logs for any errors

## Security Notes

- ✅ Never commit secrets to your repository
- ✅ Use different secrets for different environments
- ✅ Rotate secrets periodically
- ✅ Use strong, randomly generated keys
- ✅ Limit access to secrets to only necessary team members

## Troubleshooting

### Common Issues

1. **"MONGO_URI is required" error**:
   - Check that `MONGO_URI` secret is set correctly
   - Verify the connection string format

2. **"SECRET_KEY must be changed in production" error**:
   - Make sure `SECRET_KEY` is not the default value
   - Use a generated key from the script

3. **SSH connection failed**:
   - Verify `SSH_USERNAME`, `SSH_PRIVATE_KEY`, and `SSH_PORT`
   - Check that the public key is added to the server

4. **Docker build failed**:
   - Check that all environment variables are properly set
   - Verify the `.env` file is created correctly

### Debug Commands

```bash
# Test environment variables locally
python3 scripts/test_env.py

# Generate a new secret key
python3 scripts/generate_secret_key.py

# Check if .env file exists and has content
ls -la .env
cat .env | sed 's/=.*/=***/'
``` 