"""
AWS CLI commands to make RDS publicly accessible
Run these commands in your local terminal (requires AWS CLI configured)
"""

import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_rds_public():
    """Commands to make RDS publicly accessible"""
    
    logger.info("🚀 Commands to make your RDS publicly accessible:")
    logger.info("=" * 60)
    
    # Step 1: Get your current public IP
    logger.info("📋 Step 1: Get your current public IP")
    logger.info("Visit: https://whatismyipaddress.com/ and note your IP")
    
    # Step 2: AWS CLI commands (you need to run these)
    logger.info("\n📋 Step 2: Run these AWS CLI commands:")
    
    commands = [
        "# 1. Make RDS instance publicly accessible",
        "aws rds modify-db-instance --db-instance-identifier my-expense-tracker-database --publicly-accessible --apply-immediately",
        "",
        "# 2. Find your RDS security group ID",
        "aws rds describe-db-instances --db-instance-identifier my-expense-tracker-database --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' --output text",
        "",
        "# 3. Add your IP to security group (replace YOUR_IP and SECURITY_GROUP_ID)",
        "aws ec2 authorize-security-group-ingress --group-id SECURITY_GROUP_ID --protocol tcp --port 5432 --cidr YOUR_IP/32",
        "",
        "# Alternative: Allow from anywhere (NOT SECURE - only for testing)",
        "aws ec2 authorize-security-group-ingress --group-id SECURITY_GROUP_ID --protocol tcp --port 5432 --cidr 0.0.0.0/0"
    ]
    
    for cmd in commands:
        logger.info(cmd)
    
    logger.info("\n" + "=" * 60)
    logger.info("⚠️  SECURITY WARNING:")
    logger.info("- Only use 0.0.0.0/0 for testing")
    logger.info("- Always use your specific IP (YOUR_IP/32) for security")
    logger.info("- Consider using EC2 as a bastion host for production")

def aws_console_steps():
    """Manual steps via AWS Console"""
    
    logger.info("🖱️  Alternative: Manual steps via AWS Console:")
    logger.info("=" * 60)
    
    steps = [
        "1. Go to AWS Console → RDS → Databases",
        "2. Click 'my-expense-tracker-database'",
        "3. Click 'Modify' button",
        "4. Scroll to 'Connectivity' section",
        "5. Check ✅ 'Publicly accessible'",
        "6. Click 'Continue' → 'Apply immediately'",
        "",
        "7. Go to AWS Console → EC2 → Security Groups",
        "8. Find your RDS security group (check RDS database details)",
        "9. Click 'Edit inbound rules'",
        "10. Click 'Add rule':",
        "    - Type: PostgreSQL",
        "    - Port: 5432",
        "    - Source: My IP (for your IP only)",
        "    - OR Source: Anywhere IPv4 (0.0.0.0/0) for testing only ⚠️",
        "11. Click 'Save rules'"
    ]
    
    for step in steps:
        logger.info(step)

def main():
    """Main function"""
    logger.info("🌐 Making RDS Publicly Accessible Guide")
    
    make_rds_public()
    logger.info("\n")
    aws_console_steps()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ After completing these steps, you can run:")
    logger.info("   python add_name_column.py")
    logger.info("   (from your local machine)")
    
    logger.info("\n🔐 Security Best Practices:")
    logger.info("- Use your specific IP address, not 0.0.0.0/0")
    logger.info("- Consider using EC2 as a secure tunnel")
    logger.info("- Never expose production databases to the internet")

if __name__ == "__main__":
    main()
