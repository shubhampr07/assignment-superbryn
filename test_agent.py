"""
Test script to verify LiveKit agent and webhook logging.

This script creates a test room and simulates participant interactions
to verify that webhooks are being properly logged.
"""

import asyncio
import os
from dotenv import load_dotenv
from livekit import api
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_room_creation():
    """
    Test creating a room and verify webhook logging.
    """
    # Initialize LiveKit API client
    livekit_url = os.getenv("LIVEKIT_URL")
    livekit_api_key = os.getenv("LIVEKIT_API_KEY")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not all([livekit_url, livekit_api_key, livekit_api_secret]):
        logger.error("Missing LiveKit credentials in .env file")
        return
    
    # Create API client
    livekit_api = api.LiveKitAPI(
        url=livekit_url,
        api_key=livekit_api_key,
        api_secret=livekit_api_secret,
    )
    
    try:
        # Create a test room
        room_name = "test-voice-agent-room"
        logger.info(f"Creating room: {room_name}")
        
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=300,  # 5 minutes
                max_participants=10,
            )
        )
        
        logger.info(f"Room created successfully: {room.sid}")
        logger.info(f"Room name: {room.name}")
        
        # Generate participant token
        token = api.AccessToken(livekit_api_key, livekit_api_secret)
        token.with_identity("test-participant-1")
        token.with_name("Test User")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
        
        participant_token = token.to_jwt()
        logger.info(f"Generated participant token")
        
        # List rooms to verify
        rooms = await livekit_api.room.list_rooms(api.ListRoomsRequest())
        logger.info(f"Total active rooms: {len(rooms.rooms)}")
        
        for r in rooms.rooms:
            logger.info(f"  - Room: {r.name} (SID: {r.sid}, Participants: {r.num_participants})")
        
        logger.info("\n" + "="*80)
        logger.info("TEST INSTRUCTIONS:")
        logger.info("="*80)
        logger.info("1. Make sure webhook_handler.py is running: python webhook_handler.py")
        logger.info("2. Configure LiveKit Cloud/Server to send webhooks to your handler endpoint")
        logger.info("3. Connect to the room using the LiveKit client or test app")
        logger.info(f"4. Use this token to join: {participant_token[:50]}...")
        logger.info("5. Check webhook_handler.py logs to see events being captured")
        logger.info("6. Visit http://localhost:8080/logs to see all logged events")
        logger.info("="*80 + "\n")
        
        # Keep room alive for testing
        logger.info("Room will remain active for testing. Press Ctrl+C to exit.")
        await asyncio.sleep(300)  # Keep alive for 5 minutes
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
    finally:
        await livekit_api.aclose()


if __name__ == "__main__":
    asyncio.run(test_room_creation())
