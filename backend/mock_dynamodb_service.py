#!/usr/bin/env python3
"""
Mock DynamoDB service for testing without AWS
"""

import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MockDynamoDBService:
    def __init__(self, region_name='us-east-1', profile_table='agent-profiles', conversation_table='agent-conversations', endpoint_url=None):
        """
        Initialize Mock DynamoDB service
        
        Args:
            region_name (str): AWS region name (not used in mock)
            profile_table (str): Name of the profiles table
            conversation_table (str): Name of the conversations table
            endpoint_url (str): Custom endpoint URL (not used in mock)
        """
        self.region_name = region_name
        self.profile_table_name = profile_table
        self.conversation_table_name = conversation_table
        
        # Create storage directory
        self.storage_dir = "mock_dynamodb_storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize in-memory storage
        self.profiles = {}
        self.conversations = {}
        
        logger.info("Mock DynamoDB service initialized")

    def create_tables(self):
        """Create mock tables (no-op for mock)"""
        logger.info("Mock tables created (in-memory storage)")

    def store_profile(self, profile_data: Dict[str, Any], profile_id: Optional[str] = None) -> str:
        """
        Store an agent profile in mock storage
        
        Args:
            profile_data (dict): Agent profile data
            profile_id (str, optional): Custom profile ID. If None, generates a new UUID
            
        Returns:
            str: The profile ID
        """
        if profile_id is None:
            profile_id = str(uuid.uuid4())
        
        # Prepare the item for storage
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
        
        # Store in memory
        self.profiles[profile_id] = item
        
        # Also save to file for persistence
        filepath = os.path.join(self.storage_dir, f"profile_{profile_id}.json")
        with open(filepath, 'w') as f:
            json.dump(item, f, indent=2)
        
        logger.info(f"Successfully stored profile with ID: {profile_id}")
        return profile_id

    def retrieve_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an agent profile by ID
        
        Args:
            profile_id (str): Profile ID to retrieve
            
        Returns:
            dict: Profile data or None if not found
        """
        if profile_id in self.profiles:
            item = self.profiles[profile_id]
            # Return in the same format as the original JSON storage
            return {
                'id': item['id'],
                'timestamp': item['timestamp'],
                'data': item['profile_data']
            }
        return None

    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """
        Get all stored agent profiles
        
        Returns:
            list: List of all profiles
        """
        profiles = []
        for item in self.profiles.values():
            profiles.append({
                'id': item['id'],
                'timestamp': item['timestamp'],
                'data': item['profile_data']
            })
        return profiles

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
        
        # Store in memory
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append(item)
        
        # Also save to file for persistence
        filepath = os.path.join(self.storage_dir, f"conversation_{conversation_id}.json")
        with open(filepath, 'w') as f:
            json.dump(self.conversations[conversation_id], f, indent=2)
        
        logger.info(f"Successfully stored conversation message for agent {agent_id}")
        return conversation_id

    def get_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages in a conversation
        
        Args:
            conversation_id (str): Conversation ID
            
        Returns:
            list: List of conversation messages
        """
        return self.conversations.get(conversation_id, [])

    def get_agent_conversations(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a specific agent
        
        Args:
            agent_id (str): Agent ID
            
        Returns:
            list: List of conversations for the agent
        """
        agent_conversations = []
        for conv_id, messages in self.conversations.items():
            for message in messages:
                if message['agent_id'] == agent_id:
                    agent_conversations.append(message)
        return agent_conversations

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete an agent profile
        
        Args:
            profile_id (str): Profile ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            
            # Also delete file
            filepath = os.path.join(self.storage_dir, f"profile_{profile_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            logger.info(f"Successfully deleted profile: {profile_id}")
            return True
        return False

    def search_profiles_by_job(self, job: str) -> List[Dict[str, Any]]:
        """
        Search profiles by job title
        
        Args:
            job (str): Job title to search for
            
        Returns:
            list: List of matching profiles
        """
        profiles = []
        for item in self.profiles.values():
            if item['job'].lower() == job.lower():
                profiles.append({
                    'id': item['id'],
                    'timestamp': item['timestamp'],
                    'data': item['profile_data']
                })
        return profiles

    def search_profiles_by_location(self, city: str) -> List[Dict[str, Any]]:
        """
        Search profiles by location
        
        Args:
            city (str): City to search for
            
        Returns:
            list: List of matching profiles
        """
        profiles = []
        for item in self.profiles.values():
            if city.lower() in item['location_city'].lower():
                profiles.append({
                    'id': item['id'],
                    'timestamp': item['timestamp'],
                    'data': item['profile_data']
                })
        return profiles

    def load_from_files(self):
        """Load existing data from files"""
        # Load profiles
        for filename in os.listdir(self.storage_dir):
            if filename.startswith('profile_') and filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        item = json.load(f)
                        self.profiles[item['id']] = item
                except Exception as e:
                    logger.error(f"Error loading profile file {filename}: {e}")
        
        # Load conversations
        for filename in os.listdir(self.storage_dir):
            if filename.startswith('conversation_') and filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        messages = json.load(f)
                        if messages:
                            conv_id = messages[0]['conversation_id']
                            self.conversations[conv_id] = messages
                except Exception as e:
                    logger.error(f"Error loading conversation file {filename}: {e}")
        
        logger.info(f"Loaded {len(self.profiles)} profiles and {len(self.conversations)} conversations from files")
