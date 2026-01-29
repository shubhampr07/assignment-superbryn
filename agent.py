"""
LiveKit Voice Agent with livekit-evals integration

This agent uses LiveKit to create a voice-enabled AI assistant.
It automatically logs all calls using the livekit-evals package.
"""

import logging
from dotenv import load_dotenv
import os

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    voice,
)
from livekit.plugins import openai, deepgram

# Import livekit-evals for automatic call logging
from livekit_evals import create_webhook_handler
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")


class Assistant(voice.Agent):
    """Voice AI Assistant Agent"""
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice assistant powered by LiveKit.
            Your interface is voice-based, so keep responses concise and natural.
            Engage in friendly conversation and help users with their questions.""",
        )


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the LiveKit agent.
    
    This function:
    1. Sets up the voice assistant with STT, LLM, and TTS
    2. Integrates livekit-evals for automatic call logging
    3. Sends webhook with call metrics after each session
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")
    
    # Initialize livekit-evals webhook handler
    # This will automatically track transcripts, usage metrics, and latency
    webhook_handler = create_webhook_handler(
        room=ctx.room,
        is_deployed_on_lk_cloud=True,  # Set to False if self-hosting LiveKit
        api_key="sbryn_CHnVoSu8t0bzV717l_1gu4aEo2j4rRq8",  # Pass API key directly
        # disable_recording=True  # Uncomment to disable automatic S3 recording
    )
    
    # Set up voice AI pipeline with STT, LLM, and TTS
    session = voice.AgentSession(
        stt=deepgram.STT(model="nova-2"),  # Speech-to-Text using Deepgram
        llm=openai.LLM(model="gpt-4o-mini"),  # LLM using OpenAI
        tts=openai.TTS(voice="alloy"),  # Text-to-Speech using OpenAI
    )
    
    # Start the agent session
    await session.start(Assistant(), room=ctx.room)
    logger.info("Voice assistant session started")
    
    # Attach webhook handler to capture all session events
    # IMPORTANT: Must be called AFTER session.start()
    if webhook_handler:
        await webhook_handler.attach_to_session(session)  # Must await this!
        
        # Send webhook when call ends (it will be logged to SuperBryn dashboard)
        ctx.add_shutdown_callback(webhook_handler.send_webhook)
        logger.info("✅ Webhook handler attached - calls will be logged to https://app.superbryn.com/logs")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


if __name__ == "__main__":
    # Start the LiveKit worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
