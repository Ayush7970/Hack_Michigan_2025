#!/usr/bin/env python3
"""
Setup script for local DynamoDB testing
This creates a local DynamoDB instance for development
"""

import os
import sys
import subprocess
import time
import requests
import json

def install_dynamodb_local():
    """Install DynamoDB Local"""
    print("📦 Installing DynamoDB Local...")
    
    # Check if DynamoDB Local is already installed
    try:
        result = subprocess.run(['java', '-Djava.library.path=./DynamoDBLocal_lib', '-jar', 'DynamoDBLocal.jar', '--version'], 
                              capture_output=True, text=True, cwd='dynamodb_local')
        print("✅ DynamoDB Local already installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Create directory for DynamoDB Local
    os.makedirs('dynamodb_local', exist_ok=True)
    
    # Download DynamoDB Local
    print("Downloading DynamoDB Local...")
    try:
        subprocess.run([
            'curl', '-o', 'dynamodb_local/DynamoDBLocal.zip',
            'https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_2023.12.07.zip'
        ], check=True)
        
        # Extract the zip file
        subprocess.run(['unzip', '-o', 'dynamodb_local/DynamoDBLocal.zip', '-d', 'dynamodb_local'], check=True)
        
        print("✅ DynamoDB Local installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install DynamoDB Local: {e}")
        return False

def start_dynamodb_local():
    """Start DynamoDB Local"""
    print("🚀 Starting DynamoDB Local...")
    
    try:
        # Start DynamoDB Local in background
        process = subprocess.Popen([
            'java', '-Djava.library.path=./DynamoDBLocal_lib', 
            '-jar', 'DynamoDBLocal.jar', '--sharedDb', '--inMemory'
        ], cwd='dynamodb_local', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait a moment for it to start
        time.sleep(3)
        
        # Test if it's running
        try:
            response = requests.get('http://localhost:8000', timeout=5)
            print("✅ DynamoDB Local is running on port 8000")
            return True
        except requests.exceptions.RequestException:
            print("❌ DynamoDB Local failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start DynamoDB Local: {e}")
        return False

def create_tables():
    """Create DynamoDB tables"""
    print("🏗️  Creating DynamoDB tables...")
    
    # Create profiles table
    try:
        subprocess.run([
            'aws', 'dynamodb', 'create-table',
            '--table-name', 'agent-profiles',
            '--attribute-definitions',
            'AttributeName=id,AttributeType=S',
            'AttributeName=job,AttributeType=S',
            'AttributeName=location_city,AttributeType=S',
            '--key-schema',
            'AttributeName=id,KeyType=HASH',
            '--global-secondary-indexes',
            'IndexName=job-index,KeySchema=[{AttributeName=job,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}',
            'IndexName=location-index,KeySchema=[{AttributeName=location_city,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}',
            '--provisioned-throughput',
            'ReadCapacityUnits=10,WriteCapacityUnits=10',
            '--endpoint-url', 'http://localhost:8000'
        ], check=True)
        print("✅ Profiles table created")
    except subprocess.CalledProcessError:
        print("ℹ️  Profiles table may already exist")
    
    # Create conversations table
    try:
        subprocess.run([
            'aws', 'dynamodb', 'create-table',
            '--table-name', 'agent-conversations',
            '--attribute-definitions',
            'AttributeName=conversation_id,AttributeType=S',
            'AttributeName=timestamp,AttributeType=S',
            'AttributeName=agent_id,AttributeType=S',
            '--key-schema',
            'AttributeName=conversation_id,KeyType=HASH',
            'AttributeName=timestamp,KeyType=RANGE',
            '--global-secondary-indexes',
            'IndexName=agent-conversations-index,KeySchema=[{AttributeName=agent_id,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}',
            '--provisioned-throughput',
            'ReadCapacityUnits=10,WriteCapacityUnits=10',
            '--endpoint-url', 'http://localhost:8000'
        ], check=True)
        print("✅ Conversations table created")
    except subprocess.CalledProcessError:
        print("ℹ️  Conversations table may already exist")

def migrate_data():
    """Migrate existing JSON data"""
    print("🔄 Migrating existing data...")
    
    try:
        # Set environment variable for local DynamoDB
        env = os.environ.copy()
        env['AWS_ENDPOINT_URL'] = 'http://localhost:8000'
        
        subprocess.run([sys.executable, 'migrate_to_dynamodb.py'], 
                      env=env, check=True)
        print("✅ Data migration completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Data migration failed: {e}")
        return False

def test_setup():
    """Test the setup"""
    print("🧪 Testing setup...")
    
    try:
        # Set environment variable for local DynamoDB
        env = os.environ.copy()
        env['AWS_ENDPOINT_URL'] = 'http://localhost:8000'
        
        subprocess.run([sys.executable, 'test_dynamodb.py'], 
                      env=env, check=True)
        print("✅ Setup test completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Local DynamoDB Setup for Agent Matching System")
    print("=" * 55)
    
    # Check if we're in the right directory
    if not os.path.exists('dynamodb_service.py'):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Step 1: Install DynamoDB Local
    if not install_dynamodb_local():
        print("❌ Setup failed: Could not install DynamoDB Local")
        sys.exit(1)
    
    # Step 2: Start DynamoDB Local
    if not start_dynamodb_local():
        print("❌ Setup failed: Could not start DynamoDB Local")
        sys.exit(1)
    
    # Step 3: Create tables
    create_tables()
    
    # Step 4: Migrate data
    if not migrate_data():
        print("❌ Setup failed: Could not migrate data")
        sys.exit(1)
    
    # Step 5: Test setup
    if not test_setup():
        print("❌ Setup failed: Test failed")
        sys.exit(1)
    
    print("\n🎉 Local DynamoDB setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the server: python server.py")
    print("2. The server will use local DynamoDB on port 8000")
    print("3. Test the API endpoints")
    
    print("\nTo stop DynamoDB Local later, find the process and kill it:")
    print("ps aux | grep DynamoDBLocal")

if __name__ == "__main__":
    main()
