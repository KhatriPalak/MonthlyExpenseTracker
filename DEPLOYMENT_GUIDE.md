# AWS Deployment Guide for Monthly Expense Tracker

## Prerequisites
- AWS RDS PostgreSQL instance running
- AWS EC2 instance with Ubuntu/Amazon Linux
- Node.js and Python installed on EC2
- Security groups configured to allow:
  - Port 5002 for backend API
  - Port 3000 for frontend (or 80 if using nginx)
  - Port 5432 for RDS (only from EC2)

## Step 1: Set up RDS Database

1. Create the database and tables on RDS:
```bash
# Connect to RDS
psql -h your-rds-endpoint.amazonaws.com -U your_username -d postgres

# Create database
CREATE DATABASE expense_tracker;

# Connect to the new database
\c expense_tracker

# Run the create_tables.py script locally first to generate schema
# Or manually create tables using the SQL from backend/create_tables.py
```

## Step 2: Deploy Backend on EC2

1. SSH into your EC2 instance:
```bash
ssh -i your-key.pem ec2-user@your-ec2-public-ip
```

2. Clone the repository:
```bash
git clone <your-repo-url>
cd MonthlyExpenseTracker/backend
```

3. Install Python dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the production env file
cp .env.production .env

# Edit the .env file with your RDS details
nano .env
# Update:
# - DB_HOST with your RDS endpoint
# - DB_USER with your RDS username
# - DB_PASSWORD with your RDS password
# - JWT_SECRET with a secure random string
```

5. Initialize the database:
```bash
python create_tables.py
```

6. Run the backend:
```bash
# For testing
python app/app_integrated.py

# For production, use gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 app.app_integrated:app
```

7. (Optional) Set up as a systemd service:
```bash
sudo nano /etc/systemd/system/expense-tracker-backend.service
```

Add:
```ini
[Unit]
Description=Expense Tracker Backend
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/MonthlyExpenseTracker/backend
Environment="PATH=/home/ec2-user/MonthlyExpenseTracker/backend/venv/bin"
ExecStart=/home/ec2-user/MonthlyExpenseTracker/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5002 app.app_integrated:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl start expense-tracker-backend
sudo systemctl enable expense-tracker-backend
```

## Step 3: Deploy Frontend on EC2

1. Install Node.js if not already installed:
```bash
curl -sL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install nodejs -y
```

2. Navigate to frontend directory:
```bash
cd ~/MonthlyExpenseTracker/frontend
```

3. Install dependencies:
```bash
npm install
```

4. Update production environment:
```bash
# Copy production env
cp .env.production .env

# Edit with your EC2 public IP
nano .env
# Update REACT_APP_API_URL=http://YOUR_EC2_PUBLIC_IP:5002
```

5. Build the production version:
```bash
npm run build
```

6. Serve the frontend:

Option A - Using serve:
```bash
npm install -g serve
serve -s build -l 3000
```

Option B - Using nginx (recommended):
```bash
# Install nginx
sudo yum install nginx -y

# Copy build files
sudo cp -r build/* /usr/share/nginx/html/

# Configure nginx
sudo nano /etc/nginx/nginx.conf
```

Add in the server block:
```nginx
location / {
    root /usr/share/nginx/html;
    try_files $uri /index.html;
}

location /api {
    proxy_pass http://localhost:5002;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

Start nginx:
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Step 4: Configure Security Groups

1. **EC2 Security Group**:
   - Inbound:
     - Port 22 (SSH) from your IP
     - Port 80 (HTTP) from anywhere (if using nginx)
     - Port 3000 from anywhere (if using serve)
     - Port 5002 from anywhere (for API)
   - Outbound:
     - All traffic allowed

2. **RDS Security Group**:
   - Inbound:
     - Port 5432 from EC2 security group
   - Outbound:
     - All traffic allowed

## Step 5: Test the Application

1. Access the frontend:
   - If using nginx: `http://YOUR_EC2_PUBLIC_IP`
   - If using serve: `http://YOUR_EC2_PUBLIC_IP:3000`

2. Test the API directly:
   ```bash
   curl http://YOUR_EC2_PUBLIC_IP:5002/api/test-db
   ```

## Quick Start Commands

```bash
# On EC2, after setup:

# Start backend
cd ~/MonthlyExpenseTracker/backend
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5002 app.app_integrated:app &

# Start frontend (if using serve)
cd ~/MonthlyExpenseTracker/frontend
serve -s build -l 3000 &
```

## Troubleshooting

1. **Backend not connecting to RDS**:
   - Check RDS security group allows EC2
   - Verify DB credentials in .env
   - Test connection: `psql -h your-rds-endpoint.amazonaws.com -U username -d expense_tracker`

2. **Frontend not connecting to backend**:
   - Check REACT_APP_API_URL in frontend .env
   - Verify backend is running: `curl localhost:5002/api/test-db`
   - Check EC2 security group allows port 5002

3. **Check logs**:
   ```bash
   # Backend logs
   sudo journalctl -u expense-tracker-backend -f
   
   # Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

## Important Notes

1. **For production**, you should:
   - Use HTTPS with SSL certificates (Let's Encrypt)
   - Use a domain name instead of IP
   - Set up a load balancer
   - Use environment-specific JWT secrets
   - Set up proper backup for RDS
   - Use AWS Secrets Manager for sensitive data

2. **Database migrations**: When updating schema, create migration scripts

3. **Monitoring**: Set up CloudWatch for monitoring

4. **Auto-scaling**: Consider using Elastic Beanstalk or ECS for easier management