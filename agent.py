"""
LiveKit Voice Agent

This agent uses LiveKit to create a voice-enabled AI assistant.
It connects to a LiveKit room and responds to voice inputs.
"""

import asyncio
import logging
from dotenv import load_dotenv
import os

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents import voice
from livekit.plugins import openai, deepgram

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the LiveKit agent.
    
    This function is called when a participant joins a room.
    It sets up the voice assistant with:
    - Speech-to-Text (STT)
    - Large Language Model (LLM)
    - Text-to-Speech (TTS)
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Create the voice agent with instructions and components
    agent = voice.Agent(
        instructions=(
            "You are a helpful voice assistant powered by LiveKit. "
            "Your interface is voice-based, so keep responses concise and natural. "
            "Engage in friendly conversation and help users with their questions."
        ),
        stt=deepgram.STT(),  # Speech-to-Text using Deepgram
        llm=openai.LLM(model="gpt-4o-mini"),  # LLM using OpenAI
        tts=openai.TTS(voice="alloy"),  # Text-to-Speech using OpenAI
    )
    
    # Create and start the agent session
    session = voice.AgentSession()
    await session.start(agent, room=ctx.room)
    
    logger.info("Voice assistant is now active and listening")


if __name__ == "__main__":
    # Start the LiveKit worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
