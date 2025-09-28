#!/usr/bin/env python3
"""
Setup script for Mock DynamoDB (no AWS required)
"""

import os
import sys
import json
import subprocess

def migrate_json_data():
    """Migrate existing JSON data to mock DynamoDB"""
    print("🔄 Migrating existing JSON data to Mock DynamoDB...")
    
    # Import the mock service
    from mock_dynamodb_service import MockDynamoDBService
    
    # Initialize mock service
    mock_service = MockDynamoDBService()
    
    # Directory containing JSON files
    json_storage_dir = "json_storage"
    
    if not os.path.exists(json_storage_dir):
        print("ℹ️  No JSON storage directory found - nothing to migrate")
        return True
    
    # Get all JSON files
    json_files = [f for f in os.listdir(json_storage_dir) if f.endswith('.json')]
    
    if not json_files:
        print("ℹ️  No JSON files found to migrate")
        return True
    
    print(f"Found {len(json_files)} JSON files to migrate")
    
    migrated_count = 0
    failed_count = 0
    
    for json_file in json_files:
        file_path = os.path.join(json_storage_dir, json_file)
        
        try:
            # Read the JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract the profile data
            if 'data' in data:
                profile_data = data['data']
                profile_id = data.get('id')
                
                # Store in mock DynamoDB
                stored_id = mock_service.store_profile(profile_data, profile_id)
                
                if stored_id:
                    print(f"✅ Migrated {json_file} -> {stored_id}")
                    migrated_count += 1
                else:
                    print(f"❌ Failed to migrate {json_file}")
                    failed_count += 1
            else:
                print(f"⚠️  Skipping {json_file} - no 'data' field found")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Error migrating {json_file}: {e}")
            failed_count += 1
    
    print(f"Migration completed: {migrated_count} successful, {failed_count} failed")
    
    # Verify migration
    all_profiles = mock_service.get_all_profiles()
    print(f"Verification: {len(all_profiles)} profiles now in Mock DynamoDB")
    
    return failed_count == 0

def test_server():
    """Test the server with mock DynamoDB"""
    print("\n🧪 Testing Server with Mock DynamoDB")
    print("=" * 40)
    
    print("Starting server test...")
    print("This will test the Mock DynamoDB functionality.")
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
    print("🚀 Mock DynamoDB Setup for Agent Matching System")
    print("=" * 50)
    print("This setup uses a mock DynamoDB service that doesn't require AWS.")
    print("Data is stored locally in JSON files for persistence.")
    
    # Check if we're in the right directory
    if not os.path.exists('mock_dynamodb_service.py'):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Step 1: Migrate existing data
    if not migrate_json_data():
        print("❌ Setup failed: Migration unsuccessful")
        sys.exit(1)
    
    print("\n🎉 Mock DynamoDB setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the server: python server.py")
    print("2. Test the API endpoints")
    print("3. Check the mock_dynamodb_storage directory to see your data")
    
    # Ask if user wants to test the server
    test_choice = input("\nWould you like to test the server now? (y/N): ").strip().lower()
    if test_choice in ['y', 'yes']:
        test_server()

if __name__ == "__main__":
    main()
