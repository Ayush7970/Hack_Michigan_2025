#!/usr/bin/env python3
"""
Setup script for DynamoDB migration
This script will guide you through the setup process
"""

import os
import sys
import subprocess
import json

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True, check=True)
        print("✅ AWS credentials are configured")
        return True
    except subprocess.CalledProcessError:
        print("❌ AWS credentials not configured")
        return False
    except FileNotFoundError:
        print("❌ AWS CLI not found")
        return False

def configure_aws():
    """Guide user through AWS configuration"""
    print("\n🔧 AWS Configuration Required")
    print("=" * 40)
    print("To use DynamoDB, you need to configure AWS credentials.")
    print("\nYou have several options:")
    print("1. Use AWS CLI: aws configure")
    print("2. Use environment variables")
    print("3. Use IAM roles (if running on EC2)")
    print("4. Use AWS SSO")
    
    print("\nFor this setup, we'll use AWS CLI configuration.")
    print("\nYou'll need:")
    print("- AWS Access Key ID")
    print("- AWS Secret Access Key") 
    print("- Default region (e.g., us-east-1)")
    print("- Default output format (json)")
    
    print("\nTo get these credentials:")
    print("1. Go to AWS Console → IAM → Users")
    print("2. Create a new user or use existing one")
    print("3. Attach policy: AmazonDynamoDBFullAccess")
    print("4. Create access keys")
    
    input("\nPress Enter when you have your credentials ready...")
    
    # Run aws configure
    try:
        subprocess.run(['aws', 'configure'], check=True)
        print("\n✅ AWS configuration completed")
        return True
    except subprocess.CalledProcessError:
        print("❌ AWS configuration failed")
        return False

def test_dynamodb_access():
    """Test DynamoDB access"""
    print("\n🧪 Testing DynamoDB Access")
    print("=" * 30)
    
    try:
        # Test by listing tables
        result = subprocess.run(['aws', 'dynamodb', 'list-tables'], 
                              capture_output=True, text=True, check=True)
        print("✅ DynamoDB access confirmed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ DynamoDB access failed: {e}")
        return False

def run_migration():
    """Run the migration script"""
    print("\n🔄 Running Migration")
    print("=" * 20)
    
    try:
        subprocess.run([sys.executable, 'migrate_to_dynamodb.py'], check=True)
        print("✅ Migration completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_server():
    """Test the server"""
    print("\n🚀 Testing Server")
    print("=" * 20)
    
    print("Starting server test...")
    print("This will test the DynamoDB functionality.")
    print("Make sure no other server is running on port 8080.")
    
    try:
        subprocess.run([sys.executable, 'test_dynamodb.py'], check=True)
        print("✅ Server test completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 DynamoDB Setup for Agent Matching System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('dynamodb_service.py'):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Step 1: Check AWS credentials
    if not check_aws_credentials():
        if not configure_aws():
            print("\n❌ Setup failed: Could not configure AWS credentials")
            sys.exit(1)
    
    # Step 2: Test DynamoDB access
    if not test_dynamodb_access():
        print("\n❌ Setup failed: Could not access DynamoDB")
        print("Please check your AWS permissions and try again")
        sys.exit(1)
    
    # Step 3: Run migration
    if not run_migration():
        print("\n❌ Setup failed: Migration unsuccessful")
        sys.exit(1)
    
    # Step 4: Test server
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the server: python server.py")
    print("2. Test the API endpoints")
    print("3. Check the DynamoDB console to see your data")
    
    # Ask if user wants to test the server
    test_choice = input("\nWould you like to test the server now? (y/N): ").strip().lower()
    if test_choice in ['y', 'yes']:
        test_server()

if __name__ == "__main__":
    main()
