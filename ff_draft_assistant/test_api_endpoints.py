#!/usr/bin/env python3
"""
Test script for new API endpoints
"""

import requests
import json
from flask import Flask
import threading
import time
import sys
import os

# Add current directory to path for imports
sys.path.append(os.getcwd())

def test_endpoints():
    """Test the new API endpoints"""
    print("="*60)
    print("API ENDPOINT TESTING")
    print("="*60)
    
    base_url = "http://localhost:4000"
    
    # Test pagination endpoint
    print("\n1. Testing Pagination Endpoint (/api/players)")
    print("-" * 40)
    
    # Test different pagination parameters
    test_params = [
        {'page': 1, 'per_page': 5},
        {'page': 2, 'per_page': 10, 'position': 'QB'},
        {'page': 1, 'per_page': 20, 'query': 'josh'},
    ]
    
    for params in test_params:
        url = f"{base_url}/api/players"
        print(f"Testing: {url} with params {params}")
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"  ✓ Success: {len(data.get('players', []))} players returned")
                print(f"    Page {pagination.get('page')}/{pagination.get('total_pages')} "
                      f"(Total: {pagination.get('total')})")
            else:
                print(f"  ✗ Error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Connection error: {e}")
    
    # Test player detail endpoint
    print(f"\n2. Testing Player Detail Endpoint (/api/player/<name>)")
    print("-" * 40)
    
    test_players = ['Christian McCaffrey', 'Josh Allen', 'Cooper Kupp']
    
    for player_name in test_players:
        url = f"{base_url}/api/player/{player_name.replace(' ', '%20')}"
        print(f"Testing: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                player = data.get('player', {})
                print(f"  ✓ Success: {player.get('name')} ({player.get('position')} - {player.get('team')})")
                
                if player.get('career_stats'):
                    print(f"    Career stats: Available")
                else:
                    print(f"    Career stats: Not available")
                
                if player.get('similar_players'):
                    print(f"    Similar players: {len(player['similar_players'])} found")
                else:
                    print(f"    Similar players: None found")
                    
            else:
                print(f"  ✗ Error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Connection error: {e}")
    
    print("\n" + "="*60)
    print("API TESTING COMPLETE")
    print("="*60)

def start_app_for_testing():
    """Start Flask app in a separate thread for testing"""
    try:
        from app import app
        app.run(debug=False, port=4000, use_reloader=False)
    except Exception as e:
        print(f"Error starting Flask app: {e}")

def main():
    print("Starting Flask app for endpoint testing...")
    
    # Start Flask app in background
    flask_thread = threading.Thread(target=start_app_for_testing, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    print("Waiting for Flask app to start...")
    time.sleep(3)
    
    # Test endpoints
    test_endpoints()

if __name__ == "__main__":
    main()