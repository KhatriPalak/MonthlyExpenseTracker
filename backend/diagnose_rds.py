"""
RDS Connection Diagnostic Script
This script helps diagnose RDS connectivity issues from EC2
"""

import os
import socket
import subprocess
import psycopg2
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_network_connectivity():
    """Test basic network connectivity to RDS endpoint"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found")
        return False
    
    # Extract hostname and port from DATABASE_URL
    # Format: postgresql://user:pass@host:port/db
    try:
        parts = database_url.split('@')[1].split('/')
        host_port = parts[0]
        host = host_port.split(':')[0]
        port = int(host_port.split(':')[1])
        
        logger.info(f"🔍 Testing connection to RDS endpoint: {host}:{port}")
        
        # Test 1: DNS Resolution
        try:
            ip = socket.gethostbyname(host)
            logger.info(f"✅ DNS Resolution successful: {host} -> {ip}")
        except socket.gaierror as e:
            logger.error(f"❌ DNS Resolution failed: {e}")
            return False
        
        # Test 2: Port connectivity (telnet-like test)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        
        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                logger.info(f"✅ Port {port} is reachable on {host}")
                sock.close()
                return True
            else:
                logger.error(f"❌ Port {port} is NOT reachable on {host} (Error code: {result})")
                sock.close()
                return False
        except Exception as e:
            logger.error(f"❌ Socket connection failed: {e}")
            sock.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error parsing DATABASE_URL: {e}")
        return False

def test_postgresql_connection():
    """Test actual PostgreSQL connection"""
    database_url = os.getenv('DATABASE_URL')
    
    logger.info("🔍 Testing PostgreSQL connection...")
    try:
        # Try to connect with a shorter timeout
        conn = psycopg2.connect(database_url, connect_timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        logger.info(f"✅ PostgreSQL connection successful!")
        logger.info(f"✅ Version: {version[0][:50]}...")
        cur.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        if "timeout" in str(e).lower():
            logger.error("❌ PostgreSQL connection timed out - This is a network/security group issue")
        elif "authentication" in str(e).lower():
            logger.error("❌ PostgreSQL authentication failed - Check username/password")
        else:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection error: {e}")
        return False

def get_ec2_metadata():
    """Get EC2 instance metadata to help with troubleshooting"""
    logger.info("🔍 Getting EC2 instance metadata...")
    
    try:
        # Get instance metadata (only works from EC2)
        metadata_commands = {
            "Instance ID": "curl -s http://169.254.169.254/latest/meta-data/instance-id",
            "Availability Zone": "curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone",
            "VPC ID": "curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/)/vpc-id",
            "Subnet ID": "curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/)/subnet-id",
            "Security Groups": "curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/)/security-group-ids"
        }
        
        ec2_info = {}
        for name, command in metadata_commands.items():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ec2_info[name] = result.stdout.strip()
                    logger.info(f"✅ {name}: {ec2_info[name]}")
                else:
                    logger.warning(f"⚠️ Could not get {name}")
            except Exception as e:
                logger.warning(f"⚠️ Error getting {name}: {e}")
        
        return ec2_info
        
    except Exception as e:
        logger.warning(f"⚠️ Could not get EC2 metadata (might not be running on EC2): {e}")
        return {}

def ping_test():
    """Test basic ping connectivity"""
    database_url = os.getenv('DATABASE_URL')
    host = database_url.split('@')[1].split(':')[0]
    
    logger.info(f"🔍 Testing ping to {host}...")
    
    try:
        # Use ping command (Windows)
        result = subprocess.run(f"ping -n 4 {host}", shell=True, capture_output=True, text=True, timeout=30)
        if "Reply from" in result.stdout:
            logger.info("✅ Ping successful - Basic network connectivity works")
            return True
        else:
            logger.error("❌ Ping failed - Network connectivity issue")
            logger.info(f"Ping output: {result.stdout}")
            return False
    except Exception as e:
        logger.error(f"❌ Ping test failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    logger.info("🚀 Starting RDS Connection Diagnostics...")
    logger.info("=" * 60)
    
    # Test 1: Basic ping
    ping_success = ping_test()
    
    # Test 2: Network connectivity (port test)
    network_success = test_network_connectivity()
    
    # Test 3: PostgreSQL connection
    postgres_success = test_postgresql_connection()
    
    # Test 4: Get EC2 metadata
    ec2_info = get_ec2_metadata()
    
    logger.info("=" * 60)
    logger.info("📋 DIAGNOSTIC SUMMARY:")
    logger.info(f"  Ping Test: {'✅ PASS' if ping_success else '❌ FAIL'}")
    logger.info(f"  Network Connectivity (Port 5432): {'✅ PASS' if network_success else '❌ FAIL'}")
    logger.info(f"  PostgreSQL Connection: {'✅ PASS' if postgres_success else '❌ FAIL'}")
    
    if postgres_success:
        logger.info("🎉 RDS connection is working! Your database is ready.")
        return True
    else:
        logger.info("\n🔧 TROUBLESHOOTING STEPS:")
        
        if not ping_success:
            logger.info("1. ❌ Basic network connectivity failed")
            logger.info("   - Check if RDS instance is running")
            logger.info("   - Verify the RDS endpoint in your .env file")
            
        elif not network_success:
            logger.info("2. ❌ Port 5432 is blocked")
            logger.info("   - Check RDS Security Group inbound rules")
            logger.info("   - Ensure port 5432 is open from your EC2 security group")
            logger.info("   - Verify EC2 and RDS are in the same VPC")
            
            if ec2_info.get("Security Groups"):
                logger.info(f"   - Your EC2 Security Groups: {ec2_info['Security Groups']}")
                logger.info("   - RDS Security Group should allow inbound 5432 from these groups")
        
        else:
            logger.info("3. ❌ PostgreSQL authentication or configuration issue")
            logger.info("   - Check username/password in DATABASE_URL")
            logger.info("   - Verify database name exists")
            
        logger.info("\n🎯 Most likely issue: RDS Security Group configuration")
        logger.info("   Go to AWS Console > RDS > Your Database > Security Groups")
        logger.info("   Add inbound rule: PostgreSQL (5432) from your EC2 security group")
        
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("💥 RDS connection diagnostics completed. Please fix the issues above.")
        exit(1)
    else:
        logger.info("🚀 RDS connection is working! You can now run your migration script.")
