#!/usr/bin/env python3
"""
Simple script to insert an agent into the uagent matching server
"""

import requests
import json
import sys

# Server configuration
SERVER_URL = "http://localhost:8080"

def insert_agent(agent_data):
    """
    Insert an agent into the server
    
    Args:
        agent_data (dict): Dictionary containing agent information
    """
    try:
        response = requests.post(
            f"{SERVER_URL}/store",
            json=agent_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Successfully inserted agent!")
            print(f"   Name: {agent_data.get('name', 'N/A')}")
            print(f"   Job: {agent_data.get('job', 'N/A')}")
            print(f"   ID: {result['id']}")
            print(f"   Message: {result['message']}")
            return result['id']
        else:
            print(f"❌ Failed to insert agent: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on port 8080!")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Main function to handle command line arguments or interactive mode"""
    
    if len(sys.argv) > 1:
        # Command line mode - read from JSON file
        json_file = sys.argv[1]
        try:
            with open(json_file, 'r') as f:
                agent_data = json.load(f)
            insert_agent(agent_data)
        except FileNotFoundError:
            print(f"❌ File not found: {json_file}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in file: {json_file}")
    else:
        # Interactive mode - prompt for agent data
        print("🔧 Uagent Insertion Tool")
        print("=" * 40)
        
        agent_data = {}
        
        # Get required fields
        agent_data['name'] = input("Enter agent name: ").strip()
        agent_data['address'] = input("Enter agent address: ").strip()
        agent_data['job'] = input("Enter job title: ").strip()
        
        # Get average price
        while True:
            try:
                agent_data['averagePrice'] = float(input("Enter average price: ").strip())
                break
            except ValueError:
                print("Please enter a valid number for average price.")
        
        # Get tags
        tags_input = input("Enter tags (comma-separated): ").strip()
        agent_data['tags'] = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        # Get location
        location_input = input("Enter location (comma-separated): ").strip()
        agent_data['location'] = [loc.strip() for loc in location_input.split(',') if loc.strip()]
        
        # Get description
        agent_data['description'] = input("Enter description: ").strip()
        
        print("\n" + "=" * 40)
        print("Agent data to be inserted:")
        print(json.dumps(agent_data, indent=2))
        
        confirm = input("\nProceed with insertion? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            insert_agent(agent_data)
        else:
            print("❌ Insertion cancelled.")

if __name__ == "__main__":
    main()
