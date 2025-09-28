#!/usr/bin/env python3
"""
DynamoDB service for storing agent profiles and conversations
"""

import boto3
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DynamoDBService:
    def __init__(self, region_name='us-east-1', profile_table='agent-profiles', conversation_table='agent-conversations', endpoint_url=None):
        """
        Initialize DynamoDB service
        
        Args:
            region_name (str): AWS region name
            profile_table (str): Name of the profiles table
            conversation_table (str): Name of the conversations table
            endpoint_url (str): Custom endpoint URL for local DynamoDB
        """
        self.region_name = region_name
        self.profile_table_name = profile_table
        self.conversation_table_name = conversation_table
        
        # Initialize DynamoDB client
        try:
            # Check for local DynamoDB endpoint
            if endpoint_url or os.getenv('AWS_ENDPOINT_URL'):
                endpoint = endpoint_url or os.getenv('AWS_ENDPOINT_URL')
                self.dynamodb = boto3.resource('dynamodb', region_name=region_name, endpoint_url=endpoint)
                self.client = boto3.client('dynamodb', region_name=region_name, endpoint_url=endpoint)
                logger.info(f"DynamoDB service initialized for local endpoint: {endpoint}")
            else:
                self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
                self.client = boto3.client('dynamodb', region_name=region_name)
                logger.info(f"DynamoDB service initialized for region: {region_name}")
            
            self.profile_table = self.dynamodb.Table(profile_table)
            self.conversation_table = self.dynamodb.Table(conversation_table)
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB: {e}")
            raise

    def create_tables(self):
        """Create DynamoDB tables if they don't exist"""
        try:
            # Create profiles table
            self._create_profiles_table()
            # Create conversations table
            self._create_conversations_table()
            logger.info("DynamoDB tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def _create_profiles_table(self):
        """Create the agent profiles table"""
        try:
            self.client.create_table(
                TableName=self.profile_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'job',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'location_city',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'job-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'job',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'location-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'location_city',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                BillingMode='PROVISIONED',
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )
            logger.info(f"Created table: {self.profile_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"Table {self.profile_table_name} already exists")
            else:
                raise

    def _create_conversations_table(self):
        """Create the conversations table"""
        try:
            self.client.create_table(
                TableName=self.conversation_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'conversation_id',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'conversation_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'agent_id',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'agent-conversations-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'agent_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                BillingMode='PROVISIONED',
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )
            logger.info(f"Created table: {self.conversation_table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"Table {self.conversation_table_name} already exists")
            else:
                raise

    def store_profile(self, profile_data: Dict[str, Any], profile_id: Optional[str] = None) -> str:
        """
        Store an agent profile in DynamoDB
        
        Args:
            profile_data (dict): Agent profile data
            profile_id (str, optional): Custom profile ID. If None, generates a new UUID
            
        Returns:
            str: The profile ID
        """
        if profile_id is None:
            profile_id = str(uuid.uuid4())
        
        # Prepare the item for DynamoDB
        item = {
            'id': profile_id,
            'timestamp': datetime.now().isoformat(),
            'name': profile_data.get('name', ''),
            'address': profile_data.get('address', ''),
            'job': profile_data.get('job', ''),
            'averagePrice': profile_data.get('averagePrice', 0.0),
            'tags': profile_data.get('tags', []),
            'location': profile_data.get('location', []),
            'location_city': profile_data.get('location', [''])[0] if profile_data.get('location') else '',
            'description': profile_data.get('description', ''),
            'profile_data': profile_data  # Store original data for compatibility
        }
        
        try:
            self.profile_table.put_item(Item=item)
            logger.info(f"Successfully stored profile with ID: {profile_id}")
            return profile_id
        except Exception as e:
            logger.error(f"Error storing profile: {e}")
            raise

    def retrieve_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an agent profile by ID
        
        Args:
            profile_id (str): Profile ID to retrieve
            
        Returns:
            dict: Profile data or None if not found
        """
        try:
            response = self.profile_table.get_item(Key={'id': profile_id})
            if 'Item' in response:
                item = response['Item']
                # Return in the same format as the original JSON storage
                return {
                    'id': item['id'],
                    'timestamp': item['timestamp'],
                    'data': item['profile_data']
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving profile {profile_id}: {e}")
            return None

    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """
        Get all stored agent profiles
        
        Returns:
            list: List of all profiles
        """
        try:
            response = self.profile_table.scan()
            profiles = []
            for item in response['Items']:
                profiles.append({
                    'id': item['id'],
                    'timestamp': item['timestamp'],
                    'data': item['profile_data']
                })
            return profiles
        except Exception as e:
            logger.error(f"Error retrieving all profiles: {e}")
            return []

    def store_conversation(self, agent_id: str, message: str, sender: str, conversation_id: Optional[str] = None) -> str:
        """
        Store a conversation message
        
        Args:
            agent_id (str): ID of the agent involved in the conversation
            message (str): The message content
            sender (str): Who sent the message ('user' or 'agent')
            conversation_id (str, optional): Conversation ID. If None, generates a new one
            
        Returns:
            str: The conversation ID
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        timestamp = datetime.now().isoformat()
        
        item = {
            'conversation_id': conversation_id,
            'timestamp': timestamp,
            'agent_id': agent_id,
            'message': message,
            'sender': sender
        }
        
        try:
            self.conversation_table.put_item(Item=item)
            logger.info(f"Successfully stored conversation message for agent {agent_id}")
            return conversation_id
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            raise

    def get_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages in a conversation
        
        Args:
            conversation_id (str): Conversation ID
            
        Returns:
            list: List of conversation messages
        """
        try:
            response = self.conversation_table.query(
                KeyConditionExpression='conversation_id = :conv_id',
                ExpressionAttributeValues={':conv_id': conversation_id}
            )
            return response['Items']
        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {e}")
            return []

    def get_agent_conversations(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a specific agent
        
        Args:
            agent_id (str): Agent ID
            
        Returns:
            list: List of conversations for the agent
        """
        try:
            response = self.conversation_table.query(
                IndexName='agent-conversations-index',
                KeyConditionExpression='agent_id = :agent_id',
                ExpressionAttributeValues={':agent_id': agent_id}
            )
            return response['Items']
        except Exception as e:
            logger.error(f"Error retrieving conversations for agent {agent_id}: {e}")
            return []

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete an agent profile
        
        Args:
            profile_id (str): Profile ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.profile_table.delete_item(Key={'id': profile_id})
            logger.info(f"Successfully deleted profile: {profile_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting profile {profile_id}: {e}")
            return False

    def search_profiles_by_job(self, job: str) -> List[Dict[str, Any]]:
        """
        Search profiles by job title
        
        Args:
            job (str): Job title to search for
            
        Returns:
            list: List of matching profiles
        """
        try:
            response = self.profile_table.query(
                IndexName='job-index',
                KeyConditionExpression='job = :job',
                ExpressionAttributeValues={':job': job}
            )
            profiles = []
            for item in response['Items']:
                profiles.append({
                    'id': item['id'],
                    'timestamp': item['timestamp'],
                    'data': item['profile_data']
                })
            return profiles
        except Exception as e:
            logger.error(f"Error searching profiles by job {job}: {e}")
            return []

    def search_profiles_by_location(self, city: str) -> List[Dict[str, Any]]:
        """
        Search profiles by location
        
        Args:
            city (str): City to search for
            
        Returns:
            list: List of matching profiles
        """
        try:
            response = self.profile_table.query(
                IndexName='location-index',
                KeyConditionExpression='location_city = :city',
                ExpressionAttributeValues={':city': city}
            )
            profiles = []
            for item in response['Items']:
                profiles.append({
                    'id': item['id'],
                    'timestamp': item['timestamp'],
                    'data': item['profile_data']
                })
            return profiles
        except Exception as e:
            logger.error(f"Error searching profiles by location {city}: {e}")
            return []
