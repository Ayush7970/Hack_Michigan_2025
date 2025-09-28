#!/usr/bin/env python3
"""
DynamoDB configuration settings
"""

import os

# DynamoDB Configuration
DYNAMODB_REGION = os.getenv('AWS_REGION', 'us-east-1')
PROFILE_TABLE_NAME = os.getenv('PROFILE_TABLE_NAME', 'agent-profiles')
CONVERSATION_TABLE_NAME = os.getenv('CONVERSATION_TABLE_NAME', 'agent-conversations')

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Table Configuration
PROFILE_TABLE_CONFIG = {
    'billing_mode': 'PROVISIONED',
    'read_capacity_units': 10,
    'write_capacity_units': 10
}

CONVERSATION_TABLE_CONFIG = {
    'billing_mode': 'PROVISIONED',
    'read_capacity_units': 10,
    'write_capacity_units': 10
}

# GSI Configuration
GSI_CONFIG = {
    'read_capacity_units': 5,
    'write_capacity_units': 5
}
