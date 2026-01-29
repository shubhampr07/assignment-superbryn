"""
Generate LiveKit Access Token

Run this script to generate a token for testing the voice agent.
Usage: python generate_token.py
"""

import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

def generate_token(room_name="test-room", participant_identity="test-user"):
    """Generate a LiveKit access token."""
    
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Error: LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in .env file")
        return None
    
    # Create token
    token = api.AccessToken(api_key, api_secret)
    token.with_identity(participant_identity)
    token.with_name(participant_identity)
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
    ))
    
    jwt_token = token.to_jwt()
    
    print("\n" + "="*80)
    print("🎫 LiveKit Access Token Generated!")
    print("="*80)
    print(f"\nRoom Name: {room_name}")
    print(f"Participant: {participant_identity}")
    print(f"\nToken:\n{jwt_token}")
    print("\n" + "="*80)
    print("\n📋 To test:")
    print("1. Open test_client.html in your browser")
    print("2. Paste this token in the 'Access Token' field")
    print("3. Click 'Connect to Voice Agent'")
    print("4. Start speaking!")
    print("="*80 + "\n")
    
    return jwt_token


if __name__ == "__main__":
    # You can customize these values
    ROOM_NAME = input("Enter room name (press Enter for 'test-room'): ").strip() or "test-room"
    USER_ID = input("Enter participant identity (press Enter for 'test-user'): ").strip() or "test-user"
    
    generate_token(ROOM_NAME, USER_ID)
