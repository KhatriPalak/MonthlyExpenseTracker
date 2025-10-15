# AWS Production Architecture - Monthly Expense Tracker

## 🏗️ Complete Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                            User Browser                              │
│                   https://monthlyexpensetracker.online              │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ DNS Resolution
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Route 53 (AWS)                              │
│  - Hosted Zone for monthlyexpensetracker.online                     │
│  - Domain purchased from Namecheap                                   │
│  - Points to CloudFront distribution                                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ HTTPS (Port 443)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CloudFront Distribution                           │
│  - SSL/TLS Certificate from ACM (Amazon Certificate Manager)        │
│  - Handles HTTPS termination                                         │
│  - CDN for static content caching                                    │
│  - Origin: Classic Load Balancer                                     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ HTTP/HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Classic Load Balancer                             │
│  - Distributes traffic to EC2 instance                               │
│  - Health checks on EC2                                              │
│  - Forwards all requests to EC2:80 (nginx)                           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              │ Port 80
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Default VPC                              │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Public Subnet                            │   │
│  │                   (Internet accessible)                       │   │
│  │                                                               │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │         EC2 Instance (t2.micro - Free Tier)            │  │   │
│  │  │         Public IP assigned                             │  │   │
│  │  │                                                         │  │   │
│  │  │  ┌──────────────────────────────────────────────────┐  │  │   │
│  │  │  │         Nginx (Port 80)                          │  │  │   │
│  │  │  │  - Serves React frontend static files           │  │  │   │
│  │  │  │  - Proxies /api/* to localhost:5002             │  │  │   │
│  │  │  └────────┬─────────────────────┬──────────────────┘  │  │   │
│  │  │           │                     │                      │  │   │
│  │  │           ▼                     ▼                      │  │   │
│  │  │  ┌────────────────┐   ┌──────────────────────────┐   │  │   │
│  │  │  │ React Frontend │   │  Flask Backend (5002)    │   │  │   │
│  │  │  │ /usr/share/    │   │  - REST API              │   │  │   │
│  │  │  │ nginx/html/    │   │  - JWT auth              │   │  │   │
│  │  │  │                │   │  - Google OAuth          │   │  │   │
│  │  │  └────────────────┘   └───────────┬──────────────┘   │  │   │
│  │  │                                    │                  │  │   │
│  │  └────────────────────────────────────┼──────────────────┘  │   │
│  │                                       │                     │   │
│  └───────────────────────────────────────┼─────────────────────┘   │
│                                          │                          │
│                                          │ Port 5432                │
│                                          │ (Private connection)     │
│  ┌───────────────────────────────────────┼─────────────────────┐   │
│  │                      Private Subnet                         │   │
│  │                   (No internet access)                      │   │
│  │                                       │                     │   │
│  │  ┌────────────────────────────────────▼──────────────────┐ │   │
│  │  │       RDS PostgreSQL Instance (Free Tier)             │ │   │
│  │  │       No public IP                                    │ │   │
│  │  │       - Database: expense_db                          │ │   │
│  │  │       - Only accessible from EC2 in public subnet     │ │   │
│  │  │       - Automated backups enabled                     │ │   │
│  │  └───────────────────────────────────────────────────────┘ │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🌐 VPC and Network Architecture

### VPC Configuration

**VPC Type:** AWS Default VPC
- **CIDR Block:** Typically `172.31.0.0/16`
- **Internet Gateway:** Attached (provides internet access)
- **DNS Resolution:** Enabled
- **DNS Hostnames:** Enabled

### Subnet Configuration

#### Public Subnet
- **Purpose:** Hosts EC2 instance
- **Internet Access:** Yes (via Internet Gateway)
- **Auto-assign Public IP:** Enabled
- **Route Table:** Routes `0.0.0.0/0` to Internet Gateway
- **Resources:**
  - EC2 t2.micro instance (Flask + Nginx)
  - Classic Load Balancer (attached)

#### Private Subnet
- **Purpose:** Hosts RDS PostgreSQL database
- **Internet Access:** No (isolated from internet)
- **Auto-assign Public IP:** Disabled
- **Route Table:** Local routes only (no internet gateway route)
- **Resources:**
  - RDS PostgreSQL instance
  - No public IP assigned

### Network Flow

```
Internet
   ↓
Internet Gateway (attached to VPC)
   ↓
Public Subnet (EC2 instance)
   ↓
   ├─→ Outbound: Can access internet
   └─→ Inbound: Receives traffic from Load Balancer
   ↓
Private Subnet (RDS instance)
   ↓
   ├─→ Outbound: No internet access
   └─→ Inbound: Only from EC2 security group
```

### Security Architecture

```
┌──────────────────────────────────────────────────────┐
│              Classic Load Balancer                    │
│              Security Group                           │
│  Inbound: 80, 443 from 0.0.0.0/0                     │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│              EC2 Security Group                       │
│  Inbound:                                            │
│    - Port 22 (SSH) from Your IP                      │
│    - Port 80 (HTTP) from Load Balancer SG           │
│  Outbound:                                           │
│    - All traffic to 0.0.0.0/0 (internet)            │
│    - Port 5432 to RDS Security Group                │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│              RDS Security Group                       │
│  Inbound:                                            │
│    - Port 5432 from EC2 Security Group only         │
│  Outbound:                                           │
│    - Not required (RDS doesn't initiate outbound)   │
└──────────────────────────────────────────────────────┘
```

## 🔄 Request Flow Detailed

### 1. User Accesses Website (Frontend Request)

```
User types: https://monthlyexpensetracker.online
    ↓
Route 53 resolves domain → CloudFront Distribution IP
    ↓
CloudFront receives HTTPS request (ACM certificate validates)
    ↓
CloudFront forwards to Classic Load Balancer
    ↓
Load Balancer forwards to EC2:80 (nginx)
    ↓
Nginx serves React index.html from /usr/share/nginx/html/
    ↓
Browser loads React app (JavaScript bundle)
    ↓
React app initializes, reads from window (environment vars baked into build)
```

### 2. API Request Flow (e.g., Fetching Expenses)

```
React App makes API call:
fetch('https://monthlyexpensetracker.online/api/expenses?year=2025&month=10')
    ↓
Request goes to CloudFront (same domain, no CORS issues)
    ↓
CloudFront forwards to Load Balancer
    ↓
Load Balancer forwards to EC2:80 (nginx)
    ↓
Nginx sees /api/* path → proxies to localhost:5002
    ↓
Flask backend receives request on port 5002
    ↓
Flask authenticates JWT token
    ↓
Flask queries RDS PostgreSQL on port 5432
    ↓
RDS returns expense data
    ↓
Flask formats JSON response
    ↓
Response travels back: Flask → Nginx → Load Balancer → CloudFront → User
    ↓
React app updates UI with expense data
```

### 3. Authentication Flow

```
User submits login form
    ↓
POST https://monthlyexpensetracker.online/api/auth/login
    ↓
(Same routing: CloudFront → Load Balancer → Nginx → Flask)
    ↓
Flask validates credentials against RDS
    ↓
Flask generates JWT token
    ↓
Token sent back to frontend
    ↓
React stores token in localStorage
    ↓
Subsequent requests include token in Authorization header
```

## 🔧 Configuration Details

### Nginx Configuration (on EC2)

**File:** `/etc/nginx/nginx.conf` or `/etc/nginx/sites-available/default`

```nginx
server {
    listen 80;
    server_name monthlyexpensetracker.online;

    # Serve React frontend static files
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA routing
    }

    # Proxy API requests to Flask backend
    location /api {
        proxy_pass http://localhost:5002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Frontend Environment Configuration

**Local Development:** `frontend/.env`
```env
REACT_APP_API_URL=http://localhost:5002
REACT_APP_ENV=development
REACT_APP_DEBUG=true
```

**Production Build:** `frontend/.env.production` or update `.env` before build
```env
REACT_APP_API_URL=https://monthlyexpensetracker.online
REACT_APP_ENV=production
REACT_APP_DEBUG=false
```

**IMPORTANT:** Environment variables are baked into the build at compile time!
```bash
# Must rebuild frontend after changing .env
npm run build
```

### Backend Environment Configuration

**File:** `backend/.env` (on EC2)
```env
# Database
DATABASE_URL=postgresql://username:password@your-rds-endpoint.amazonaws.com:5432/expense_db
POSTGRES_USER=your-username
POSTGRES_PW=your-password
POSTGRES_URL=your-rds-endpoint.amazonaws.com:5432
POSTGRES_DB=expense_db

# Security
SECRET_KEY=your-production-secret-key-here
JWT_SECRET=your-jwt-secret-key

# Google OAuth (Get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Flask
FLASK_ENV=production
FLASK_DEBUG=False

# Server
PORT=5002
HOST=0.0.0.0

# CORS (allow CloudFront and your domain)
ALLOWED_ORIGINS=https://monthlyexpensetracker.online,https://www.monthlyexpensetracker.online
```

**⚠️ SECURITY WARNING:**
- **NEVER** commit `.env` files to git
- Keep production credentials separate from development
- Use different Google OAuth credentials for dev vs production
- Set file permissions: `chmod 600 backend/.env`

### Backend Systemd Service (on EC2)

**File:** `/etc/systemd/system/expense-tracker.service`
```ini
[Unit]
Description=Monthly Expense Tracker Backend
After=network.target

[Service]
Type=notify
User=ec2-user
WorkingDirectory=/home/ec2-user/MonthlyExpenseTracker/backend
Environment="PATH=/home/ec2-user/MonthlyExpenseTracker/backend/venv/bin"
ExecStart=/home/ec2-user/MonthlyExpenseTracker/backend/venv/bin/gunicorn \
    -w 4 \
    -b 0.0.0.0:5002 \
    --timeout 120 \
    --access-logfile /var/log/expense-tracker/access.log \
    --error-logfile /var/log/expense-tracker/error.log \
    app.app_integrated:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands:**
```bash
sudo systemctl start expense-tracker
sudo systemctl enable expense-tracker
sudo systemctl status expense-tracker
```

## 🔒 Security Configuration

### Network Security Architecture

Your security is implemented with three layers:

1. **Classic Load Balancer Security Group** - Internet-facing
2. **EC2 Security Group** - In public subnet
3. **RDS Security Group** - In private subnet

```
Internet (0.0.0.0/0)
    ↓
[Load Balancer SG] - Ports 80, 443
    ↓
[EC2 SG] - Port 22 (Your IP), Port 80 (LB SG)
    ↓
[RDS SG] - Port 5432 (EC2 SG only)
```

### EC2 Security Group (Public Subnet)

**Security Group Name:** e.g., `expense-tracker-ec2-sg`

**Inbound Rules:**
| Type | Protocol | Port | Source | Purpose | Notes |
|------|----------|------|--------|---------|-------|
| SSH | TCP | 22 | Your IP/32 | SSH access for management | **Restrict to your IP only** |
| HTTP | TCP | 80 | Load Balancer SG | Nginx receives traffic from LB | **Only from LB, not 0.0.0.0/0** |

**Outbound Rules:**
| Type | Protocol | Port | Destination | Purpose |
|------|----------|------|-------------|---------|
| HTTPS | TCP | 443 | 0.0.0.0/0 | Package updates, API calls |
| HTTP | TCP | 80 | 0.0.0.0/0 | Package updates |
| PostgreSQL | TCP | 5432 | RDS SG or RDS Private IP | Database connection |
| All Traffic | All | All | 0.0.0.0/0 | Allow all outbound (optional, more restrictive above) |

**Important Notes:**
- ⚠️ **Port 5002 should NOT have any inbound rule** - Flask only listens on localhost (127.0.0.1)
- Nginx on port 80 proxies to Flask on localhost:5002
- SSH access should be restricted to your machine's IP address only

### RDS Security Group (Private Subnet)

**Security Group Name:** e.g., `expense-tracker-rds-sg`

**Inbound Rules:**
| Type | Protocol | Port | Source | Purpose | Notes |
|------|----------|------|--------|---------|-------|
| PostgreSQL | TCP | 5432 | EC2 Security Group ID | Database access from backend | **Source is EC2 SG, not IP** |

**Example:**
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: sg-0123456789abcdef0 (EC2 SG ID)
Description: Allow from EC2 backend
```

**Outbound Rules:**
| Type | Protocol | Port | Destination | Purpose |
|------|----------|------|-------------|---------|
| (None required) | - | - | - | RDS doesn't initiate outbound connections |

**Important Notes:**
- RDS has **NO public IP** assigned
- Only accessible from EC2 instance in public subnet
- Cannot be accessed from internet
- Cannot be accessed from your local machine directly (must SSH tunnel through EC2)

### Classic Load Balancer Security Group

**Security Group Name:** e.g., `expense-tracker-lb-sg`

**Inbound Rules:**
| Type | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP traffic from CloudFront/Internet |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS traffic from CloudFront/Internet (if terminating SSL at LB) |

**Outbound Rules:**
| Type | Protocol | Port | Destination | Purpose |
|------|----------|------|-------------|---------|
| HTTP | TCP | 80 | EC2 SG | Forward to EC2 Nginx |

### Security Best Practices Applied

✅ **Defense in Depth:**
- Load Balancer → EC2 → RDS (layered security)
- Each layer has restricted access

✅ **Principle of Least Privilege:**
- EC2 port 22 only from your IP (not 0.0.0.0/0)
- RDS only from EC2 security group
- Flask port 5002 not exposed to internet

✅ **Network Isolation:**
- RDS in private subnet (no internet access)
- EC2 in public subnet (controlled access)

✅ **Secure Communication:**
- HTTPS via CloudFront (TLS/SSL)
- Internal communication over private VPC network

### Verify Your Security Configuration

**On EC2, check what's listening:**
```bash
# Check listening ports
sudo netstat -tlnp

# Should see:
# - 0.0.0.0:80 (nginx) - OK, receives from LB
# - 127.0.0.1:5002 (python/gunicorn) - OK, localhost only
# - Should NOT see 0.0.0.0:5002 - that would be exposed!
```

**From your local machine:**
```bash
# This should work (through CloudFront → LB → EC2)
curl https://monthlyexpensetracker.online/api/test-db

# This should FAIL (port 5002 not exposed)
curl http://your-ec2-public-ip:5002/api/test-db
# Connection refused or timeout - GOOD!
```

**Test RDS isolation:**
```bash
# From your local machine - should FAIL (timeout)
psql -h your-rds-endpoint.amazonaws.com -U postgres -d expense_db
# This is expected and correct - RDS not publicly accessible

# From EC2 - should WORK
ssh -i your-key.pem ec2-user@your-ec2-ip
psql -h your-rds-endpoint.amazonaws.com -U postgres -d expense_db
# This should connect successfully
```

### Classic Load Balancer

**Listeners:**
- **Port 80 (HTTP)** → Forwards to EC2:80
- *Optional:* **Port 443 (HTTPS)** → Forwards to EC2:80 (if not using CloudFront)

**Health Check:**
- Ping Protocol: HTTP
- Ping Port: 80
- Ping Path: `/` or `/api/test-db`
- Response Timeout: 5 seconds
- Interval: 30 seconds
- Unhealthy Threshold: 2
- Healthy Threshold: 10

### CloudFront Distribution

**Origin Settings:**
- **Origin Domain:** Classic Load Balancer DNS name
- **Origin Protocol Policy:** HTTP Only (or Match Viewer)
- **Viewer Protocol Policy:** Redirect HTTP to HTTPS

**Alternate Domain Names (CNAMEs):**
- `monthlyexpensetracker.online`
- `www.monthlyexpensetracker.online` (optional)

**SSL Certificate:**
- Certificate from ACM (us-east-1 region for CloudFront)
- Security Policy: TLSv1.2_2021

**Cache Behavior:**
- **Path: `/api/*`** → Cache disabled (pass through to origin)
- **Path: `/*`** → Cache enabled for static assets

### Route 53

**Hosted Zone:** `monthlyexpensetracker.online`

**Records:**
| Name | Type | Value | Purpose |
|------|------|-------|---------|
| monthlyexpensetracker.online | A | Alias to CloudFront | Main domain |
| www.monthlyexpensetracker.online | A | Alias to CloudFront | WWW subdomain |

**Nameservers:** Must be updated in Namecheap to point to AWS Route 53 nameservers

## 📦 Deployment Process

### Initial Setup (One-time)

1. **Set up AWS Infrastructure:**
   ```bash
   # Create RDS instance
   # Create EC2 instance
   # Create Security Groups
   # Create Classic Load Balancer
   # Create CloudFront Distribution
   # Request ACM Certificate
   # Configure Route 53
   ```

2. **Configure Namecheap:**
   - Update nameservers to Route 53 NS records

3. **Set up EC2:**
   ```bash
   # SSH into EC2
   ssh -i your-key.pem ec2-user@ec2-ip

   # Install dependencies
   sudo yum update -y
   sudo yum install git python3 python3-pip nginx -y
   curl -sL https://rpm.nodesource.com/setup_18.x | sudo bash -
   sudo yum install nodejs -y

   # Clone repository
   git clone <your-repo-url>
   cd MonthlyExpenseTracker
   ```

4. **Initialize Database:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Create .env with RDS credentials
   nano .env

   # Initialize tables
   python3 create_tables.py
   ```

### Regular Deployment (Updates)

#### Backend Deployment

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@ec2-ip

# Navigate to project
cd MonthlyExpenseTracker/backend

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart the service
sudo systemctl restart expense-tracker

# Check status
sudo systemctl status expense-tracker

# View logs
sudo journalctl -u expense-tracker -f
```

#### Frontend Deployment

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@ec2-ip

# Navigate to project
cd MonthlyExpenseTracker/frontend

# Pull latest code
git pull origin main

# Install any new dependencies
npm install

# Update environment for production
cat > .env << EOF
REACT_APP_API_URL=https://monthlyexpensetracker.online
REACT_APP_ENV=production
REACT_APP_DEBUG=false
EOF

# Build production bundle
npm run build

# Copy to nginx directory
sudo rm -rf /usr/share/nginx/html/*
sudo cp -r build/* /usr/share/nginx/html/

# Restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

#### Automated Deployment Script

**File:** `deploy.sh` (on EC2)
```bash
#!/bin/bash

echo "🚀 Starting deployment..."

# Pull latest code
git pull origin main

# Backend deployment
echo "📦 Deploying backend..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart expense-tracker
cd ..

# Frontend deployment
echo "🎨 Deploying frontend..."
cd frontend
npm install
cat > .env << EOF
REACT_APP_API_URL=https://monthlyexpensetracker.online
REACT_APP_ENV=production
REACT_APP_DEBUG=false
EOF
npm run build
sudo rm -rf /usr/share/nginx/html/*
sudo cp -r build/* /usr/share/nginx/html/
sudo systemctl restart nginx
cd ..

echo "✅ Deployment complete!"
echo "Backend status:"
sudo systemctl status expense-tracker --no-pager
echo ""
echo "Nginx status:"
sudo systemctl status nginx --no-pager
```

**Make executable:**
```bash
chmod +x deploy.sh
```

**Run deployment:**
```bash
./deploy.sh
```

## 🧪 Testing & Verification

### 1. Test Backend API

```bash
# Test database connection
curl https://monthlyexpensetracker.online/api/test-db

# Test categories endpoint
curl https://monthlyexpensetracker.online/api/categories

# Test months endpoint
curl https://monthlyexpensetracker.online/api/months

# Test login
curl -X POST https://monthlyexpensetracker.online/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### 2. Test Frontend

```bash
# Check if frontend loads
curl -I https://monthlyexpensetracker.online

# Should return 200 OK with HTML content
```

### 3. Browser Testing

1. Open https://monthlyexpensetracker.online
2. Open DevTools (F12) → Network tab
3. Sign up / Log in
4. Verify:
   - All requests go to `https://monthlyexpensetracker.online/api/*`
   - No mixed content warnings
   - No CORS errors
   - JWT token in localStorage

### 4. Check Logs

```bash
# Backend logs
sudo journalctl -u expense-tracker -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# System logs
dmesg | tail
```

## 🐛 Troubleshooting

### Problem: Frontend loads but API calls fail

**Symptoms:** 404 or 502 errors on `/api/*` requests

**Solutions:**
1. Check backend is running: `sudo systemctl status expense-tracker`
2. Check nginx proxy configuration: `sudo nginx -t`
3. Verify backend is on port 5002: `curl localhost:5002/api/test-db`
4. Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`

### Problem: Mixed content errors

**Symptoms:** Browser blocks HTTP requests from HTTPS page

**Solutions:**
1. Verify `.env` has HTTPS URL: `REACT_APP_API_URL=https://monthlyexpensetracker.online`
2. Rebuild frontend: `npm run build`
3. Redeploy to nginx

### Problem: CORS errors

**Symptoms:** "Access-Control-Allow-Origin" errors in console

**Solutions:**
1. Verify backend CORS settings allow your domain
2. Check that API requests go to same domain (not different subdomain)
3. Verify CloudFront is forwarding headers correctly

### Problem: 502 Bad Gateway

**Symptoms:** CloudFront/Load Balancer returns 502

**Solutions:**
1. Check EC2 health in Load Balancer
2. Verify nginx is running: `sudo systemctl status nginx`
3. Check backend is running: `sudo systemctl status expense-tracker`
4. Review EC2 security group allows traffic from Load Balancer

### Problem: Database connection fails

**Symptoms:** Backend logs show "could not connect to database"

**Solutions:**
1. Verify RDS security group allows EC2
2. Check `.env` has correct RDS endpoint
3. Test connection from EC2:
   ```bash
   psql -h your-rds-endpoint.amazonaws.com -U username -d expense_db
   ```

## 💰 Cost Optimization (Free Tier)

### What's Free:
- **EC2:** 750 hours/month of t2.micro (enough for 1 instance 24/7)
- **RDS:** 750 hours/month of db.t2.micro + 20GB storage
- **CloudFront:** 50GB data transfer out + 2M HTTP/HTTPS requests
- **Route 53:** $0.50/month per hosted zone (not free)
- **ACM:** Free SSL certificates
- **Classic Load Balancer:** ~$16/month (NOT free tier eligible)

### Cost-Saving Tips:
1. **Stop unused resources** when not needed
2. **Use Application Load Balancer** instead (has free tier hours)
3. **Consider removing Load Balancer** and point CloudFront directly to EC2
4. **Set up billing alerts** in AWS

## 📊 Monitoring

### CloudWatch Metrics to Monitor:
- EC2 CPU Utilization
- RDS CPU Utilization
- RDS Free Storage Space
- Load Balancer Request Count
- CloudFront Request Count

### Set Up Alarms:
```bash
# Example: CPU > 80%
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## 🔄 Backup & Recovery

### RDS Automated Backups:
- Enabled by default (7-day retention)
- Manual snapshots: Create before major changes

### Application Backups:
```bash
# Backup application code (on EC2)
tar -czf backup-$(date +%Y%m%d).tar.gz MonthlyExpenseTracker/

# Upload to S3 (optional)
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

## 📝 Maintenance Checklist

### Weekly:
- [ ] Check application logs for errors
- [ ] Monitor RDS storage space
- [ ] Review CloudWatch metrics

### Monthly:
- [ ] Update dependencies (npm, pip)
- [ ] Review AWS bill
- [ ] Test backup restoration
- [ ] Update SSL certificate (ACM auto-renews)

### Quarterly:
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Cost optimization review

---

**Last Updated:** October 2025
**Domain:** https://monthlyexpensetracker.online
**Architecture Version:** 1.0
