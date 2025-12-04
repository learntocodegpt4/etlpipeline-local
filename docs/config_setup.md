# Nginx Configuration Setup Guide

This guide provides instructions for configuring Nginx as a reverse proxy for the FWC ETL Pipeline on Windows 11.

## Overview

Nginx acts as a reverse proxy to expose the ETL Pipeline services through a single port (8081):
- **UI**: `http://localhost:8081/` → Next.js (port 3000)
- **API**: `http://localhost:8081/api/` → FastAPI (port 8000)
- **WebSocket**: `http://localhost:8081/ws/` → FastAPI WebSocket

## Prerequisites

1. Nginx installed on Windows 11
   - Typical location: `C:\nginx\`
   - Download from: https://nginx.org/en/download.html

2. ETL Pipeline services running:
   - FastAPI on port 8000
   - Next.js UI on port 3000

## Configuration Steps

### Step 1: Backup Existing Configuration

```powershell
# Create backup directory
mkdir C:\nginx\conf\backup

# Backup existing config
copy C:\nginx\conf\nginx.conf C:\nginx\conf\backup\nginx.conf.bak
```

### Step 2: Update nginx.conf

Replace `C:\nginx\conf\nginx.conf` with the following configuration:

```nginx
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    
    # Logging
    access_log logs/access.log;
    error_log logs/error.log;
    
    sendfile on;
    keepalive_timeout 65;
    
    # Upstream servers
    upstream etl_api {
        server 127.0.0.1:8000;
        keepalive 32;
    }

    upstream etl_ui {
        server 127.0.0.1:3000;
        keepalive 32;
    }

    server {
        listen 8081;
        server_name localhost;
        
        # Buffer settings for large responses
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        # API routes
        location /api/ {
            proxy_pass http://etl_api/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket routes
        location /ws/ {
            proxy_pass http://etl_api/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 86400;
        }

        # UI routes (catch-all)
        location / {
            proxy_pass http://etl_ui/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check endpoint
        location /nginx-health {
            return 200 "OK";
            add_header Content-Type text/plain;
        }
    }
}
```

### Step 3: Test Configuration

```powershell
# Navigate to Nginx directory
cd C:\nginx

# Test configuration syntax
.\nginx.exe -t
```

Expected output:
```
nginx: the configuration file C:\nginx/conf/nginx.conf syntax is ok
nginx: configuration file C:\nginx/conf/nginx.conf test is successful
```

### Step 4: Start/Reload Nginx

**Start Nginx (if not running):**
```powershell
cd C:\nginx
.\nginx.exe
```

**Reload configuration (if already running):**
```powershell
cd C:\nginx
.\nginx.exe -s reload
```

**Stop Nginx:**
```powershell
cd C:\nginx
.\nginx.exe -s stop
```

## Windows Firewall Configuration

To allow external access on port 8081:

### Option 1: PowerShell (Run as Administrator)

```powershell
# Allow inbound traffic on port 8081
New-NetFirewallRule -DisplayName "ETL Pipeline - Nginx Port 8081" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 8081 `
    -Action Allow
```

### Option 2: Windows Defender Firewall GUI

1. Open **Windows Defender Firewall with Advanced Security**
2. Click **Inbound Rules** → **New Rule**
3. Select **Port** → Next
4. Select **TCP**, enter **8081** → Next
5. Select **Allow the connection** → Next
6. Select all profiles (Domain, Private, Public) → Next
7. Name: **ETL Pipeline - Nginx Port 8081** → Finish

## Running Nginx as a Windows Service

To run Nginx automatically on startup, you can use NSSM (Non-Sucking Service Manager):

```powershell
# Download NSSM from https://nssm.cc/download
# Extract and run:

nssm install nginx

# In the GUI:
# Path: C:\nginx\nginx.exe
# Startup directory: C:\nginx
# Service name: nginx
```

## Verification

1. **Test health endpoint:**
   ```powershell
   curl http://localhost:8081/nginx-health
   ```

2. **Test API:**
   ```powershell
   curl http://localhost:8081/api/status
   ```

3. **Test UI:**
   Open `http://localhost:8081/` in a web browser

## Troubleshooting

### Common Issues

#### 1. Port 8081 already in use
```powershell
# Find process using port 8081
netstat -ano | findstr :8081

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

#### 2. Nginx won't start
```powershell
# Check for running instances
tasklist | findstr nginx

# Kill all nginx processes
taskkill /IM nginx.exe /F

# Start fresh
cd C:\nginx
.\nginx.exe
```

#### 3. 502 Bad Gateway
- Ensure FastAPI (port 8000) and Next.js (port 3000) are running
- Check if upstream servers are accessible:
  ```powershell
  curl http://localhost:8000/api/status
  curl http://localhost:3000
  ```

#### 4. Check Nginx logs
```powershell
# View access logs
type C:\nginx\logs\access.log

# View error logs
type C:\nginx\logs\error.log
```

#### 5. WebSocket connection issues
- Ensure the `Upgrade` and `Connection` headers are properly set
- Check that `proxy_read_timeout` is set high enough (86400 for 24 hours)

## Docker Deployment Notes

When running services in Docker while using Nginx on Windows host:

1. Ensure Docker containers expose ports to host:
   ```yaml
   ports:
     - "8000:8000"  # API
     - "3000:3000"  # UI
   ```

2. Keep the same Nginx configuration pointing to localhost ports

3. Alternatively, create a Docker network and run Nginx in Docker too

## Security Considerations

For production deployments:

1. **Enable HTTPS:**
   ```nginx
   server {
       listen 8081 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       # ... rest of configuration
   }
   ```

2. **Rate limiting:**
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   
   location /api/ {
       limit_req zone=api burst=20 nodelay;
       # ... rest of configuration
   }
   ```

3. **Restrict access by IP:**
   ```nginx
   location /api/ {
       allow 192.168.1.0/24;
       deny all;
       # ... rest of configuration
   }
   ```
