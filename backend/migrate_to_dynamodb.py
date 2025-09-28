#!/usr/bin/env python3
"""
Migration script to move existing JSON storage data to DynamoDB
"""

import json
import os
import logging
from dynamodb_service import DynamoDBService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_json_to_dynamodb():
    """Migrate all JSON files to DynamoDB"""
    
    # Initialize DynamoDB service
    try:
        dynamodb_service = DynamoDBService()
        dynamodb_service.create_tables()
        logger.info("DynamoDB service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB service: {e}")
        return False
    
    # Directory containing JSON files
    json_storage_dir = "json_storage"
    
    if not os.path.exists(json_storage_dir):
        logger.info("No JSON storage directory found - nothing to migrate")
        return True
    
    # Get all JSON files
    json_files = [f for f in os.listdir(json_storage_dir) if f.endswith('.json')]
    
    if not json_files:
        logger.info("No JSON files found to migrate")
        return True
    
    logger.info(f"Found {len(json_files)} JSON files to migrate")
    
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
                
                # Store in DynamoDB
                stored_id = dynamodb_service.store_profile(profile_data, profile_id)
                
                if stored_id:
                    logger.info(f"✅ Migrated {json_file} -> {stored_id}")
                    migrated_count += 1
                else:
                    logger.error(f"❌ Failed to migrate {json_file}")
                    failed_count += 1
            else:
                logger.warning(f"⚠️  Skipping {json_file} - no 'data' field found")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"❌ Error migrating {json_file}: {e}")
            failed_count += 1
    
    logger.info(f"Migration completed: {migrated_count} successful, {failed_count} failed")
    
    # Verify migration by checking DynamoDB
    try:
        all_profiles = dynamodb_service.get_all_profiles()
        logger.info(f"Verification: {len(all_profiles)} profiles now in DynamoDB")
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
    
    return failed_count == 0

def main():
    """Main function"""
    print("🔄 Starting migration from JSON storage to DynamoDB...")
    print("=" * 50)
    
    success = migrate_json_to_dynamodb()
    
    if success:
        print("✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Verify your data in the DynamoDB console")
        print("2. Test the server with the new DynamoDB backend")
        print("3. Consider backing up the json_storage directory before removing it")
    else:
        print("❌ Migration completed with errors. Check the logs above.")
        print("You may need to fix the issues and run the migration again.")

if __name__ == "__main__":
    main()
