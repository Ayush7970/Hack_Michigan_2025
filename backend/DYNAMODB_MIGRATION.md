# DynamoDB Migration Guide

This document outlines the migration from JSON file storage to AWS DynamoDB for the agent matching system.

## Overview

The system has been migrated from storing agent profiles in JSON files to using AWS DynamoDB for both profiles and conversations. This provides better scalability, reliability, and query capabilities.

## What Changed

### Storage Backend
- **Before**: JSON files in `json_storage/` directory
- **After**: AWS DynamoDB tables

### New Features
- **Conversation Storage**: Agents can now have conversations stored in DynamoDB
- **Advanced Querying**: Query agents by job title and location
- **Better Scalability**: DynamoDB handles large datasets efficiently
- **Data Persistence**: No risk of data loss from file system issues

## Files Added/Modified

### New Files
- `dynamodb_service.py` - Core DynamoDB operations
- `dynamodb_config.py` - Configuration settings
- `migrate_to_dynamodb.py` - Migration script
- `test_dynamodb.py` - DynamoDB-specific tests
- `DYNAMODB_MIGRATION.md` - This guide

### Modified Files
- `server.py` - Updated to use DynamoDB instead of JSON files
- `requirements.txt` - Added boto3 dependency
- `README.md` - Updated documentation

## DynamoDB Schema

### agent-profiles Table
```
Primary Key: id (String)
Attributes:
- name (String)
- address (String)
- job (String)
- averagePrice (Number)
- tags (List)
- location (List)
- location_city (String) - for GSI
- description (String)
- timestamp (String)
- profile_data (Map) - original data

Global Secondary Indexes:
- job-index: Query by job title
- location-index: Query by location
```

### agent-conversations Table
```
Primary Key: conversation_id (String)
Sort Key: timestamp (String)
Attributes:
- agent_id (String)
- message (String)
- sender (String)

Global Secondary Index:
- agent-conversations-index: Query by agent_id
```

## API Changes

### Existing Endpoints (Updated)
- `POST /store` - Now stores in DynamoDB
- `GET /retrieve/<id>` - Now retrieves from DynamoDB
- `GET /list` - Now lists from DynamoDB
- `POST /match` - Now searches DynamoDB

### New Endpoints
- `POST /conversation` - Store conversation message
- `GET /conversation/<id>` - Get conversation by ID
- `GET /agent/<id>/conversations` - Get all conversations for an agent

## Migration Process

### 1. Prerequisites
```bash
# Install new dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure
```

### 2. Run Migration
```bash
# Migrate existing JSON data to DynamoDB
python migrate_to_dynamodb.py
```

### 3. Test Migration
```bash
# Test the new DynamoDB backend
python test_dynamodb.py
```

### 4. Start Server
```bash
# Start server with DynamoDB backend
python server.py
```

## Configuration

### Environment Variables
- `AWS_REGION` - AWS region (default: us-east-1)
- `PROFILE_TABLE_NAME` - Profile table name (default: agent-profiles)
- `CONVERSATION_TABLE_NAME` - Conversation table name (default: agent-conversations)
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

### AWS Permissions Required
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DescribeTable",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:DeleteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/agent-profiles",
                "arn:aws:dynamodb:*:*:table/agent-profiles/index/*",
                "arn:aws:dynamodb:*:*:table/agent-conversations",
                "arn:aws:dynamodb:*:*:table/agent-conversations/index/*"
            ]
        }
    ]
}
```

## Benefits of Migration

### Performance
- **Faster Queries**: DynamoDB provides fast, consistent performance
- **Parallel Processing**: Multiple queries can run simultaneously
- **Indexing**: GSI allows efficient querying by job and location

### Scalability
- **Auto-scaling**: DynamoDB can handle varying loads
- **No File System Limits**: No directory size or file count limits
- **Global Distribution**: Can be replicated across regions

### Reliability
- **Built-in Backup**: DynamoDB provides automatic backups
- **High Availability**: 99.99% uptime SLA
- **Data Durability**: Data is replicated across multiple AZs

### Features
- **Conversation Storage**: New capability to store agent conversations
- **Advanced Querying**: Query by multiple attributes
- **Real-time Updates**: Changes are immediately available

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Configured**
   ```bash
   aws configure
   ```

2. **DynamoDB Tables Not Created**
   - Check AWS permissions
   - Verify region configuration
   - Check CloudWatch logs

3. **Migration Fails**
   - Verify JSON files are valid
   - Check AWS credentials
   - Ensure DynamoDB service is available

### Monitoring
- Check CloudWatch metrics for DynamoDB
- Monitor read/write capacity usage
- Set up alarms for errors

## Rollback Plan

If you need to rollback to JSON storage:

1. Stop the DynamoDB server
2. Revert `server.py` to use JSON storage functions
3. Remove DynamoDB dependencies from `requirements.txt`
4. Restart with original JSON storage

## Cost Considerations

### DynamoDB Pricing
- **On-Demand**: Pay per request (good for variable workloads)
- **Provisioned**: Pay for allocated capacity (good for predictable workloads)

### Current Configuration
- **Read Capacity**: 10 units (40,000 reads/second)
- **Write Capacity**: 10 units (10,000 writes/second)
- **GSI Capacity**: 5 units each

### Cost Optimization
- Monitor usage with CloudWatch
- Adjust capacity based on actual usage
- Consider on-demand billing for unpredictable workloads

## Support

For issues or questions:
1. Check the logs in CloudWatch
2. Verify AWS credentials and permissions
3. Test with the provided test scripts
4. Review DynamoDB documentation
