# Nginx Setup Guide for Monthly Expense Tracker

## 🎯 What Nginx Does in Your Architecture

```
CloudFront/Load Balancer → EC2:80 (Nginx)
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
            Static Files          Proxy to Flask
            (React App)           localhost:5002
            /usr/share/           /api/* requests
            nginx/html/
```

Nginx serves two purposes:
1. **Serves React frontend** static files (HTML, JS, CSS)
2. **Proxies API requests** from `/api/*` to Flask backend on port 5002

---

## 📦 Step 1: Install Nginx on EC2

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Update system packages
sudo yum update -y

# Install Nginx
sudo yum install nginx -y

# Verify installation
nginx -v

# Start Nginx
sudo systemctl start nginx

# Enable Nginx to start on boot
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

**Expected output:**
```
● nginx.service - The nginx HTTP and reverse proxy server
   Loaded: loaded (/usr/lib/systemd/system/nginx.service; enabled)
   Active: active (running)
```

---

## 🔧 Step 2: Configure Nginx

### Create/Edit Nginx Configuration

```bash
# Backup original config (just in case)
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Edit the main config file
sudo nano /etc/nginx/nginx.conf
```

### Replace the `server` block with this configuration:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name monthlyexpensetracker.online www.monthlyexpensetracker.online;

        # Root directory for React build files
        root /usr/share/nginx/html;
        index index.html;

        # Enable gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript
                   application/x-javascript application/xml+rss
                   application/javascript application/json;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API proxy - Forward all /api requests to Flask backend
        location /api {
            proxy_pass http://127.0.0.1:5002;
            proxy_http_version 1.1;

            # Forward headers
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';

            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;

            # Disable caching for API requests
            proxy_cache_bypass $http_upgrade;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }

        # Google OAuth callback route (if your backend has it)
        location /login/google {
            proxy_pass http://127.0.0.1:5002;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /auth/callback {
            proxy_pass http://127.0.0.1:5002;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Serve React app for all other routes (SPA routing)
        location / {
            try_files $uri $uri/ /index.html;

            # Cache static assets
            location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # Health check endpoint (optional)
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Deny access to hidden files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

---

## 🧪 Step 3: Test Nginx Configuration

```bash
# Test configuration for syntax errors
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If you get errors:**
- Check for typos in the config
- Make sure all brackets `{}` are closed
- Verify semicolons `;` at the end of statements

---

## 📦 Step 4: Build and Deploy React Frontend

```bash
# Navigate to frontend directory
cd ~/MonthlyExpenseTracker/frontend

# Make sure .env has production URL
cat > .env << EOF
REACT_APP_API_URL=https://monthlyexpensetracker.online
REACT_APP_ENV=production
REACT_APP_DEBUG=false
EOF

# Install dependencies (if not already done)
npm install

# Build production bundle
npm run build
```

**This creates a `build/` directory with optimized static files**

```bash
# Remove old files from nginx directory
sudo rm -rf /usr/share/nginx/html/*

# Copy new build to nginx directory
sudo cp -r build/* /usr/share/nginx/html/

# Set proper permissions
sudo chown -R nginx:nginx /usr/share/nginx/html/
sudo chmod -R 755 /usr/share/nginx/html/

# Verify files are there
ls -la /usr/share/nginx/html/
```

**You should see:**
```
index.html
static/
  ├── css/
  ├── js/
  └── media/
manifest.json
favicon.ico
...
```

---

## 🚀 Step 5: Start/Restart Services

### Start Backend (Flask)

```bash
# Navigate to backend
cd ~/MonthlyExpenseTracker/backend

# If not already set up as service, run manually first to test:
source venv/bin/activate
python3 app/app_integrated.py

# Or if you have systemd service configured:
sudo systemctl restart expense-tracker
sudo systemctl status expense-tracker
```

**Backend should be running on port 5002**

### Restart Nginx

```bash
# Reload nginx configuration
sudo systemctl reload nginx

# Or restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

---

## ✅ Step 6: Verify Everything Works

### Test 1: Check Services are Running

```bash
# Check Nginx
sudo systemctl status nginx

# Check Flask backend
curl http://localhost:5002/api/test-db

# Should return database connection status
```

### Test 2: Test from EC2 (Local)

```bash
# Test frontend
curl http://localhost/

# Should return HTML with React app

# Test API through Nginx proxy
curl http://localhost/api/test-db

# Should return same as direct Flask call above
```

### Test 3: Test from Internet

```bash
# Test API endpoint
curl https://monthlyexpensetracker.online/api/test-db

# Test categories
curl https://monthlyexpensetracker.online/api/categories
```

### Test 4: Browser Testing

1. Open browser: `https://monthlyexpensetracker.online`
2. Open DevTools (F12) → Network tab
3. You should see:
   - HTML page loads from CloudFront/Nginx
   - JavaScript/CSS files load
   - API calls go to `https://monthlyexpensetracker.online/api/*`
4. Try logging in with Google OAuth
5. Try adding an expense

---

## 🔒 Step 7: Configure EC2 Security Group

Make sure your EC2 security group allows traffic:

```
Inbound Rules:
- Port 22 (SSH) from Your IP
- Port 80 (HTTP) from Load Balancer Security Group (or 0.0.0.0/0)
- Port 443 (HTTPS) from Load Balancer Security Group (if needed)
```

**Port 5002 should NOT be exposed to the internet** - only accessible via localhost!

---

## 🐛 Troubleshooting

### Problem: Nginx won't start

```bash
# Check error logs
sudo tail -50 /var/log/nginx/error.log

# Check if port 80 is already in use
sudo netstat -tlnp | grep :80

# Check SELinux (if enabled)
sudo setenforce 0  # Temporarily disable for testing
```

### Problem: 502 Bad Gateway

**Means:** Nginx can't reach Flask backend

```bash
# Check if backend is running
curl http://localhost:5002/api/test-db

# Check backend logs
sudo journalctl -u expense-tracker -f

# Verify Flask is listening on 0.0.0.0:5002
sudo netstat -tlnp | grep :5002
```

### Problem: 404 on React routes

**Means:** `try_files` not working correctly

**Solution:** Make sure this is in your Nginx config:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Problem: API calls return 404

**Means:** Nginx proxy not configured correctly

```bash
# Test direct backend call
curl http://localhost:5002/api/categories

# Test through Nginx
curl http://localhost/api/categories

# Compare responses - they should be the same
```

### Problem: Mixed content errors

**Means:** Frontend is making HTTP calls from HTTPS page

**Solution:**
- Verify `.env` has `https://` URL
- Rebuild frontend: `npm run build`
- Redeploy to Nginx

### Check Logs in Real-Time

```bash
# Watch all Nginx logs
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log

# Watch backend logs
sudo journalctl -u expense-tracker -f

# Watch both simultaneously
sudo tail -f /var/log/nginx/error.log & sudo journalctl -u expense-tracker -f
```

---

## 📋 Quick Reference Commands

```bash
# Restart Nginx
sudo systemctl restart nginx

# Reload Nginx config (without downtime)
sudo systemctl reload nginx

# Test Nginx config
sudo nginx -t

# View Nginx status
sudo systemctl status nginx

# View Nginx error logs
sudo tail -50 /var/log/nginx/error.log

# View Nginx access logs
sudo tail -50 /var/log/nginx/access.log

# Restart backend
sudo systemctl restart expense-tracker

# View backend logs
sudo journalctl -u expense-tracker -n 50
```

---

## 🔄 Deployment Script (All-in-One)

Create this script for easy deployments:

**File:** `~/deploy-frontend.sh`

```bash
#!/bin/bash

echo "🚀 Deploying Monthly Expense Tracker Frontend..."

# Navigate to project
cd ~/MonthlyExpenseTracker/frontend

# Pull latest code
git pull origin master

# Set production environment
cat > .env << EOF
REACT_APP_API_URL=https://monthlyexpensetracker.online
REACT_APP_ENV=production
REACT_APP_DEBUG=false
EOF

# Install dependencies
npm install

# Build
echo "📦 Building React app..."
npm run build

# Deploy to Nginx
echo "🚀 Deploying to Nginx..."
sudo rm -rf /usr/share/nginx/html/*
sudo cp -r build/* /usr/share/nginx/html/
sudo chown -R nginx:nginx /usr/share/nginx/html/
sudo chmod -R 755 /usr/share/nginx/html/

# Reload Nginx
sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo ""
echo "🌐 Visit: https://monthlyexpensetracker.online"
echo ""
echo "📊 Check logs:"
echo "  Nginx: sudo tail -f /var/log/nginx/error.log"
echo "  Backend: sudo journalctl -u expense-tracker -f"
```

**Make executable:**
```bash
chmod +x ~/deploy-frontend.sh
```

**Run deployment:**
```bash
~/deploy-frontend.sh
```

---

## 📝 Configuration Summary

| Component | Port | Access |
|-----------|------|--------|
| Nginx | 80 | Public (via Load Balancer) |
| Flask Backend | 5002 | Localhost only |
| PostgreSQL RDS | 5432 | From EC2 only |

**Request Flow:**
```
User → CloudFront → Load Balancer → EC2:80 (Nginx)
                                      ↓
                        ┌─────────────┴─────────────┐
                        ↓                           ↓
                   Static Files              localhost:5002
                   (React)                   (Flask API)
```

---

## ✨ Next Steps After Setup

1. ✅ Test the application thoroughly
2. ✅ Set up backend as systemd service (if not done)
3. ✅ Configure CloudFront cache behaviors
4. ✅ Set up monitoring and alerts
5. ✅ Configure automated backups
6. ✅ Set up CI/CD pipeline (optional)

---

**Last Updated:** October 2025
**For:** https://monthlyexpensetracker.online
