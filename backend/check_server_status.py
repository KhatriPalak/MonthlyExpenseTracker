#!/usr/bin/env python3
"""
Quick server status checker for EC2 deployment
Run this on your EC2 instance to check what's deployed and running
"""

import subprocess
import os
import json

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def check_ports():
    """Check what's running on common ports"""
    print("🔍 Checking ports...")
    ports = [80, 443, 3000, 5000, 22, 5432]
    
    for port in ports:
        output, code = run_command(f"sudo netstat -tlnp")
        if f":{port}" in output:
            lines = [line for line in output.split('\n') if f":{port}" in line]
            for line in lines:
                print(f"✅ Port {port}: {line.split()[-1] if line.split() else 'Unknown process'}")
        else:
            print(f"❌ Port {port}: Not in use")

def check_processes():
    """Check for running processes"""
    print("\n🔍 Checking processes...")
    
    processes = {
        'python': 'Flask backend',
        'node': 'Node.js/React',
        'nginx': 'Web server',
        'postgres': 'Database'
    }
    
    for process, description in processes.items():
        output, code = run_command(f"pgrep -f {process}")
        if code == 0 and output:
            pids = output.split('\n')
            print(f"✅ {description}: Running ({len(pids)} processes)")
        else:
            print(f"❌ {description}: Not running")

def check_services():
    """Check systemd services"""
    print("\n🔍 Checking services...")
    
    services = ['nginx', 'postgresql']
    
    for service in services:
        output, code = run_command(f"sudo systemctl is-active {service}")
        if code == 0 and output == "active":
            print(f"✅ {service}: Active")
        else:
            print(f"❌ {service}: Inactive")

def check_pm2():
    """Check PM2 processes"""
    print("\n🔍 Checking PM2...")
    
    output, code = run_command("pm2 list")
    if code == 0:
        if "online" in output.lower():
            print("✅ PM2 processes running")
            print(output)
        else:
            print("⚠️ PM2 installed but no processes running")
    else:
        print("❌ PM2 not available")

def check_directories():
    """Check if app directories exist"""
    print("\n🔍 Checking app directories...")
    
    paths = [
        '/home/ubuntu/monthly_expense_tracker',
        '/home/ubuntu/monthly_expense_tracker/backend',
        '/home/ubuntu/monthly_expense_tracker/frontend',
        '/home/ubuntu/monthly_expense_tracker/frontend/build'
    ]
    
    for path in paths:
        if os.path.exists(path):
            files = len(os.listdir(path)) if os.path.isdir(path) else 0
            print(f"✅ {path}: Exists ({files} items)")
        else:
            print(f"❌ {path}: Missing")

def check_nginx_config():
    """Check Nginx configuration"""
    print("\n🔍 Checking Nginx config...")
    
    config_path = "/etc/nginx/sites-enabled/"
    if os.path.exists(config_path):
        configs = os.listdir(config_path)
        if configs:
            print(f"✅ Nginx configs: {configs}")
        else:
            print("❌ No Nginx site configs")
    else:
        print("❌ Nginx sites-enabled directory missing")

def check_environment():
    """Check environment variables"""
    print("\n🔍 Checking environment...")
    
    # Check if .env exists
    env_path = "/home/ubuntu/monthly_expense_tracker/backend/.env"
    if os.path.exists(env_path):
        print("✅ Backend .env file exists")
    else:
        print("❌ Backend .env file missing")

def test_connectivity():
    """Test local connectivity"""
    print("\n🔍 Testing connectivity...")
    
    tests = [
        ("http://localhost:3000", "React frontend"),
        ("http://3.141.164.136:5000/api/health", "Flask API"),
        ("http://localhost:80", "Nginx web server")
    ]
    
    for url, description in tests:
        output, code = run_command(f"curl -s -o /dev/null -w '%{{http_code}}' {url}")
        if code == 0 and output in ['200', '404', '302']:
            print(f"✅ {description}: Responding (HTTP {output})")
        else:
            print(f"❌ {description}: Not responding")

def main():
    """Run all checks"""
    print("🚀 EC2 Deployment Status Check")
    print("=" * 50)
    
    # System info
    print(f"📍 Hostname: {os.uname().nodename}")
    print(f"📍 User: {os.getenv('USER', 'unknown')}")
    print(f"📍 Working Directory: {os.getcwd()}")
    
    check_ports()
    check_processes()
    check_services()
    check_pm2()
    check_directories()
    check_nginx_config()
    check_environment()
    test_connectivity()
    
    print("\n" + "=" * 50)
    print("✅ Status check complete!")
    print("\n💡 Next steps:")
    print("   - If services are missing: Install and configure them")
    print("   - If processes not running: Start your applications")
    print("   - If connectivity fails: Check firewall and security groups")

if __name__ == "__main__":
    main()
