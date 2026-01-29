"""
Understanding livekit-evals Webhook Payload Construction

This document explains how the livekit-evals package constructs webhook payloads
from LiveKit session data by examining the event flow and data extraction.

Reference: https://pypi.org/project/livekit-evals/

## Overview

The livekit-evals package automatically tracks LiveKit agent sessions and sends
comprehensive webhook payloads containing transcripts, metrics, and session metadata.

## How Webhook Payloads Are Constructed

### 1. SESSION INITIALIZATION

When you call `create_webhook_handler(room, is_deployed_on_lk_cloud)`:

- **room**: LiveKit Room object → Extracts room metadata
  - room.name → session identifier
  - room.sid → unique session ID
  - room.metadata → custom session data

- **is_deployed_on_lk_cloud**: Boolean flag
  - True: Uses LiveKit Cloud infrastructure
  - False: Self-hosted deployment

### 2. EVENT CAPTURE (via attach_to_session)

After calling `webhook_handler.attach_to_session(session)`, the handler subscribes
to LiveKit session events to build the webhook payload:

#### A. TRANSCRIPT CONSTRUCTION

**Event Source**: Voice Activity Detection (VAD) state changes

```python
# Captured from AgentSession events:
- 'user_speech_started' → User turn begins
- 'user_speech_ended' → User turn ends
- 'agent_speech_started' → Agent turn begins
- 'agent_speech_ended' → Agent turn ends
```

**Field Construction**:
```python
transcript_entry = {
    "speaker": "user" | "agent",  # From event type
    "text": transcription_result.text,  # From STT output
    "start_time": event.timestamp,  # From VAD event
    "end_time": event.timestamp + duration,  # Calculated
    "confidence": stt_result.confidence,  # From STT provider
}
```

#### B. USAGE METRICS CONSTRUCTION

**LLM Token Usage**:
```python
# Captured from LLM completion events
llm_metrics = {
    "model": llm_instance.model,  # e.g., "gpt-4o-mini"
    "provider": detect_provider(llm_instance),  # e.g., "openai"
    "input_tokens": completion_response.usage.prompt_tokens,
    "output_tokens": completion_response.usage.completion_tokens,
    "total_tokens": completion_response.usage.total_tokens,
}
```

**STT Duration**:
```python
# Calculated from STT processing events
stt_metrics = {
    "model": stt_instance.model,  # e.g., "nova-2"
    "provider": detect_provider(stt_instance),  # e.g., "deepgram"
    "duration_seconds": sum(all_stt_processing_times),
    "audio_duration": total_audio_processed,
}
```

**TTS Character Count**:
```python
# Captured from TTS synthesis events
tts_metrics = {
    "model": tts_instance.voice,  # e.g., "alloy"
    "provider": detect_provider(tts_instance),  # e.g., "openai"
    "characters_synthesized": sum(len(text) for text in tts_requests),
}
```

#### C. LATENCY TRACKING

**Measured from Event Timestamps**:
```python
latency_metrics = {
    "llm_latency_ms": {
        "mean": avg(llm_response_times),
        "p50": median(llm_response_times),
        "p95": percentile_95(llm_response_times),
        "max": max(llm_response_times),
    },
    "stt_latency_ms": {
        "mean": avg(stt_processing_times),
        # ... similar structure
    },
    "tts_latency_ms": {
        "mean": avg(tts_synthesis_times),
        # ... similar structure
    },
}
```

#### D. SESSION METADATA AUTO-DETECTION

**From Environment Variables**:
```python
metadata = {
    "project_id": os.getenv("LIVEKIT_PROJECT_ID") or extract_from_url(os.getenv("LIVEKIT_URL")),
    "agent_id": os.getenv("AGENT_ID") or ctx.job.metadata.get("agent_id") or "livekit-agent",
    "version_id": os.getenv("VERSION_ID") or ctx.job.metadata.get("version") or "v1",
}
```

**From Room Context**:
```python
room_data = {
    "room_name": room.name,
    "room_sid": room.sid,
    "participant_count": len(room.participants),
    "creation_time": room.creation_time,
}
```

**SIP Detection** (if applicable):
```python
# Detected from participant metadata
if "sip_trunk" in participant.attributes:
    sip_data = {
        "trunk_id": participant.attributes["sip_trunk"],
        "phone_number": participant.attributes["phone_number"],
        "is_inbound": participant.attributes["direction"] == "inbound",
    }
```

#### E. RECORDING URLs

**From LiveKit Egress Events**:
```python
# Captured from room events
recording_data = {
    "recording_url": egress_event.file_url,  # S3 or cloud storage URL
    "duration": egress_event.duration,
    "file_size": egress_event.file_size,
    "format": "mp3",  # Default format
}
```

**S3 Recording** (if enabled):
```python
s3_url = f"{os.getenv('S3_BASE_URL', 'https://superbryn-call-recordings.s3.ap-south-1.amazonaws.com')}/{room.sid}.mp3"
```

### 3. WEBHOOK PAYLOAD ASSEMBLY

When `webhook_handler.send_webhook()` is called (at session end):

```python
webhook_payload = {
    # Session identification
    "session_id": room.sid,
    "room_name": room.name,
    "agent_id": metadata["agent_id"],
    "version_id": metadata["version_id"],
    "project_id": metadata["project_id"],
    
    # Timing
    "start_time": session_start_timestamp,
    "end_time": session_end_timestamp,
    "duration_seconds": end_time - start_time,
    
    # Transcript (constructed from VAD events)
    "transcript": [
        {"speaker": "user", "text": "...", "start": 0.0, "end": 2.5},
        {"speaker": "agent", "text": "...", "start": 2.5, "end": 5.0},
        # ... more entries
    ],
    
    # Usage metrics (accumulated during session)
    "usage": {
        "llm": llm_metrics,
        "stt": stt_metrics,
        "tts": tts_metrics,
    },
    
    # Latency (calculated from event timestamps)
    "latency": latency_metrics,
    
    # Configuration (detected from instances)
    "config": {
        "llm_model": llm.model,
        "llm_provider": detect_provider(llm),
        "stt_model": stt.model,
        "stt_provider": detect_provider(stt),
        "tts_voice": tts.voice,
        "tts_provider": detect_provider(tts),
    },
    
    # Recording (if available)
    "recording_url": recording_url if exists else None,
    
    # SIP data (if applicable)
    "sip": sip_data if is_sip_call else None,
}
```

### 4. WEBHOOK DELIVERY

The payload is sent to the SuperBryn API endpoint:

```python
headers = {
    "Authorization": f"Bearer {os.getenv('SUPERBRYN_API_KEY')}",
    "Content-Type": "application/json",
}

response = requests.post(
    "https://api.superbryn.com/webhooks/livekit-evals",
    json=webhook_payload,
    headers=headers,
)
```

## Key Construction Principles

1. **Event-Driven**: All data is captured from real LiveKit events, not hardcoded
2. **Automatic Detection**: Providers, models, and configuration are auto-detected
3. **Precise Timing**: VAD state changes provide accurate transcript timestamps
4. **Comprehensive Metrics**: Every LLM call, STT request, and TTS synthesis is tracked
5. **Zero Configuration**: Works out-of-the-box with environment variable defaults

## Provider Auto-Detection Logic

The package includes a `detect_provider()` function that examines model names:

```python
def detect_provider(instance):
    model_name = str(instance.model).lower()
    
    # LLM Detection
    if "gpt" in model_name or "whisper" in model_name or "tts-1" in model_name:
        return "openai"
    elif "claude" in model_name:
        return "anthropic"
    elif "gemini" in model_name:
        return "google"
    # ... 25+ providers supported
    
    # STT Detection
    elif "deepgram" in model_name or "nova" in model_name:
        return "deepgram"
    elif "assembly" in model_name:
        return "assemblyai"
    
    # TTS Detection
    elif "eleven" in model_name:
        return "elevenlabs"
    elif "cartesia" in model_name or "sonic" in model_name:
        return "cartesia"
    
    return "unknown"
```

## Summary

The livekit-evals webhook payload is constructed through:
1. **Room metadata** extraction at initialization
2. **Real-time event capture** during the session
3. **Metric accumulation** from provider responses
4. **Timestamp analysis** for latency calculations
5. **Automatic detection** of models and providers
6. **Payload assembly** at session end
7. **Authenticated delivery** to the webhook endpoint

This ensures accurate, comprehensive call logging with minimal developer effort.
"""

# Example: How to use livekit-evals in your agent
EXAMPLE_USAGE = '''
from livekit_evals import create_webhook_handler

async def entrypoint(ctx: JobContext):
    # Step 1: Create webhook handler
    webhook_handler = create_webhook_handler(
        room=ctx.room,
        is_deployed_on_lk_cloud=True,
    )
    
    # Step 2: Set up your session
    session = voice.AgentSession(
        stt=deepgram.STT(model="nova-2"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="alloy"),
    )
    
    # Step 3: Start session
    await session.start(agent=YourAgent(), room=ctx.room)
    
    # Step 4: Attach webhook handler (AFTER session.start)
    if webhook_handler:
        webhook_handler.attach_to_session(session)
        ctx.add_shutdown_callback(webhook_handler.send_webhook)
    
    await ctx.connect()
'''


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify the webhook signature to ensure it's from LiveKit.
    
    Args:
        payload: Raw request body
        signature: Signature from X-LiveKit-Signature header
    
    Returns:
        bool: True if signature is valid
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not set, skipping signature verification")
        return True
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


def extract_webhook_fields(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and document the webhook payload fields.
    
    Webhook Payload Structure (constructed by LiveKit server):
    
    1. event: String identifier for the type of event
       - Constructed from: LiveKit event system based on server-side state changes
       - Examples: "room_started", "room_finished", "participant_joined", "participant_left"
    
    2. room: Object containing room metadata
       - sid: Room Session ID (unique identifier for the room session)
       - name: Room name (specified when creating the room)
       - emptyTimeout: Time before empty room is closed
       - maxParticipants: Maximum allowed participants
       - creationTime: Unix timestamp when room was created
       - metadata: Custom metadata string attached to the room
       - numParticipants: Current number of participants
       - numPublishers: Number of participants publishing tracks
       - activeRecording: Boolean indicating if recording is active
    
    3. participant: Object containing participant information (if applicable)
       - sid: Participant Session ID
       - identity: Unique participant identifier (user-provided or generated)
       - name: Display name of the participant
       - metadata: Custom metadata string attached to the participant
       - joinedAt: Unix timestamp when participant joined
       - state: Current state (ACTIVE, DISCONNECTED, etc.)
       - tracks: Array of track information (audio/video)
    
    4. track: Object containing track information (for track events)
       - sid: Track Session ID
       - type: Track type (AUDIO, VIDEO, DATA)
       - name: Track name/label
       - muted: Boolean indicating if track is muted
       - source: Track source (CAMERA, MICROPHONE, SCREEN_SHARE, etc.)
    
    5. createdAt: Unix timestamp when the webhook event was created
       - Constructed from: LiveKit server's system time when event occurred
    
    6. id: Unique identifier for this webhook event
       - Constructed from: UUID generated by LiveKit server for this specific webhook delivery
    
    All these fields are constructed within the LiveKit server environment based on:
    - Room state management system
    - Participant connection tracking
    - Media track publishing/unpublishing events
    - Server-side timing and session management
    """
    
    return {
        "event_type": webhook_data.get("event"),
        "event_id": webhook_data.get("id"),
        "created_at": webhook_data.get("createdAt"),
        "room_info": {
            "sid": webhook_data.get("room", {}).get("sid"),
            "name": webhook_data.get("room", {}).get("name"),
            "num_participants": webhook_data.get("room", {}).get("numParticipants"),
            "creation_time": webhook_data.get("room", {}).get("creationTime"),
        },
        "participant_info": {
            "sid": webhook_data.get("participant", {}).get("sid"),
            "identity": webhook_data.get("participant", {}).get("identity"),
            "joined_at": webhook_data.get("participant", {}).get("joinedAt"),
        } if webhook_data.get("participant") else None,
    }


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Handle incoming webhooks from LiveKit.
    
    LiveKit sends POST requests to this endpoint with event data.
    """
    try:
        # Get raw payload for signature verification
        raw_payload = request.get_data()
        signature = request.headers.get("X-LiveKit-Signature", "")
        
        # Verify signature
        if not verify_webhook_signature(raw_payload, signature):
            logger.error("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse webhook data
        webhook_data = request.json
        
        if not webhook_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract fields
        extracted_data = extract_webhook_fields(webhook_data)
        
        # Log the event
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "raw_webhook": webhook_data,
            "extracted_fields": extracted_data,
        }
        
        call_logs.append(log_entry)
        
        # Log to console
        logger.info(f"Webhook received: {extracted_data['event_type']}")
        logger.info(f"Room: {extracted_data['room_info']['name']}")
        if extracted_data['participant_info']:
            logger.info(f"Participant: {extracted_data['participant_info']['identity']}")
        
        # Pretty print the webhook data
        print("\n" + "="*80)
        print("WEBHOOK EVENT RECEIVED")
        print("="*80)
        print(json.dumps(extracted_data, indent=2))
        print("="*80 + "\n")
        
        return jsonify({"status": "success", "event_processed": extracted_data['event_type']}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/logs", methods=["GET"])
def get_logs():
    """
    Retrieve all call logs.
    """
    return jsonify({
        "total_events": len(call_logs),
        "logs": call_logs
    })


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({"status": "healthy", "service": "webhook_handler"})


if __name__ == "__main__":
    port = int(os.getenv("WEBHOOK_PORT", 8080))
    logger.info(f"Starting webhook handler on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
