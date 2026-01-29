# LiveKit Voice Agent with Webhook Logging

This project implements a LiveKit voice agent with webhook event logging and evaluation using `livekit-evals`.

## Project Structure

```
assignment-superbryn/
├── agent.py                              # Main LiveKit voice agent
├── webhook_handler.py                    # Webhook handler for logging events
├── test_agent.py                         # Test script for verifying setup
├── requirements.txt                      # Python dependencies
├── .env.example                          # Environment variables template
├── WEBHOOK_PAYLOAD_DOCUMENTATION.md      # Detailed webhook documentation
└── README.md                             # This file
```

## Features

- ✅ **LiveKit Voice Agent**: Full-featured voice assistant using OpenAI GPT-4 and TTS
- ✅ **Webhook Logging**: Captures and logs all LiveKit events (room, participant, track events)
- ✅ **livekit-evals Integration**: Ready for call evaluation and metrics tracking
- ✅ **Comprehensive Documentation**: Detailed explanation of webhook payload construction

## Prerequisites

- Python 3.8 or higher
- LiveKit Cloud account or self-hosted LiveKit server
- OpenAI API key (for voice agent)
- Deepgram API key (optional, for better STT)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `livekit` - LiveKit Python SDK
- `livekit-agents` - Agent framework
- `livekit-plugins-openai` - OpenAI integration (GPT-4, TTS)
- `livekit-plugins-deepgram` - Deepgram STT integration
- `livekit-evals` - Call evaluation and metrics
- `python-dotenv` - Environment variable management

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Get these from LiveKit Cloud Dashboard (https://cloud.livekit.io)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxx

# Get from OpenAI (https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# Optional: Get from Deepgram (https://console.deepgram.com/)
DEEPGRAM_API_KEY=xxxxxxxxxxxxxxxxxxxxx

# Generate a strong random secret for webhook security
WEBHOOK_SECRET=your_random_secret_here
```

### 3. Configure Webhooks in LiveKit

1. Go to LiveKit Cloud Dashboard → Settings → Webhooks
2. Add webhook URL: `https://your-domain.com/webhook` (or use ngrok for local testing)
3. Enter the same `WEBHOOK_SECRET` from your `.env` file
4. Enable events you want to track:
   - Room events: `room_started`, `room_finished`
   - Participant events: `participant_joined`, `participant_left`
   - Track events: `track_published`, `track_unpublished`

**For local testing with ngrok**:
```bash
ngrok http 8080
# Use the ngrok URL (e.g., https://abc123.ngrok.io/webhook) in LiveKit Dashboard
```

## Running the Project

### Start the Webhook Handler

First, start the webhook handler to capture events:

```bash
python webhook_handler.py
```

This starts a Flask server on port 8080 that listens for webhook events.

### Start the LiveKit Agent

In a separate terminal, start the voice agent:

```bash
python agent.py start
```

This connects to LiveKit and waits for participants to join rooms.

### Test the Setup

In a third terminal, run the test script:

```bash
python test_agent.py
```

This creates a test room and provides instructions for connecting.

## Verifying Webhook Logging

### Check Real-Time Logs

Watch the `webhook_handler.py` terminal. You should see output like:

```
================================================================================
WEBHOOK EVENT RECEIVED
================================================================================
{
  "event_type": "participant_joined",
  "event_id": "AW_...",
  "created_at": 1706284900,
  "room_info": {
    "sid": "RM_...",
    "name": "test-voice-agent-room",
    "num_participants": 1,
    "creation_time": 1706284850
  },
  "participant_info": {
    "sid": "PA_...",
    "identity": "test-participant-1",
    "joined_at": 1706284900
  }
}
================================================================================
```

### View All Logged Events

Open your browser and visit:

```
http://localhost:8080/logs
```

This returns JSON with all captured events:

```json
{
  "total_events": 5,
  "logs": [
    {
      "timestamp": "2026-01-27T10:30:00.000Z",
      "raw_webhook": { ... },
      "extracted_fields": { ... }
    },
    ...
  ]
}
```

### Health Check

```
http://localhost:8080/health
```

Returns:
```json
{
  "status": "healthy",
  "service": "webhook_handler"
}
```

## Understanding Webhook Payloads

For a comprehensive explanation of how webhook payload fields are constructed within the LiveKit environment, see:

📄 **[WEBHOOK_PAYLOAD_DOCUMENTATION.md](WEBHOOK_PAYLOAD_DOCUMENTATION.md)**

This document covers:
- Detailed field-by-field breakdown
- Construction process within LiveKit server
- Real-world examples
- Security (signature verification)
- Integration with `livekit-evals`

## Using livekit-evals

The `livekit-evals` package can analyze the webhook data to provide call metrics:

```python
from livekit_evals import CallEvaluator

evaluator = CallEvaluator()

# Process webhook events
evaluator.process_event(webhook_data)

# After room finishes, get metrics
metrics = evaluator.get_metrics(room_sid)
print(f"Call duration: {metrics.duration}s")
print(f"Participant talk time: {metrics.participant_talk_time}s")
print(f"Agent response time: {metrics.avg_response_time}s")
```

## Testing the Voice Agent

### Using LiveKit Meet

1. Go to https://meet.livekit.io
2. Enter your room name (e.g., `test-voice-agent-room`)
3. Generate a token using your LiveKit credentials
4. Join the room
5. Speak to test the voice agent
6. Check webhook logs to see events

### Using LiveKit Playground

1. Visit https://cloud.livekit.io/projects/[your-project]/playground
2. Select your room
3. Connect with microphone enabled
4. Interact with the agent

## Project Architecture

### Voice Agent Flow

```
User speaks → Deepgram STT → OpenAI GPT-4 → OpenAI TTS → User hears response
                                ↓
                        LiveKit Server
                                ↓
                        Webhook Events → webhook_handler.py → Logs
```

### Webhook Event Flow

```
LiveKit Server
    ↓ (Event occurs: room created, participant joined, etc.)
Webhook Dispatcher
    ↓ (Constructs payload + HMAC signature)
HTTP POST to your webhook endpoint
    ↓
webhook_handler.py
    ↓ (Verifies signature, extracts fields, logs event)
Call Logs Database/Storage
```

## Troubleshooting

### Agent won't start
- Check `.env` file has correct credentials
- Verify LIVEKIT_URL format: `wss://your-project.livekit.cloud`
- Ensure OpenAI and Deepgram API keys are valid

### Webhooks not being received
- Verify webhook URL is accessible from the internet (use ngrok for local)
- Check webhook secret matches between `.env` and LiveKit Dashboard
- Look for errors in webhook handler logs
- Verify events are enabled in LiveKit Dashboard

### Audio issues
- Check browser permissions for microphone
- Verify audio tracks are being published (check webhook logs for `track_published` events)
- Test with different browsers

### Signature verification fails
- Ensure `WEBHOOK_SECRET` is exactly the same in `.env` and LiveKit Dashboard
- Check for extra spaces or newlines in the secret
- Verify webhook handler is using the same secret to verify

## Next Steps

1. **Integrate livekit-evals**: Add call quality metrics and evaluation
2. **Persistent Storage**: Replace in-memory logs with database (PostgreSQL, MongoDB)
3. **Analytics Dashboard**: Build UI to visualize call metrics
4. **Custom Agent Logic**: Enhance agent behavior based on your use case
5. **Production Deployment**: Deploy to cloud platform (AWS, GCP, Azure)

## Resources

- [LiveKit Documentation](https://docs.livekit.io/)
- [LiveKit Agents Guide](https://docs.livekit.io/agents/)
- [livekit-evals PyPI](https://pypi.org/project/livekit-evals/)
- [LiveKit Webhooks](https://docs.livekit.io/guides/webhooks/)
- [OpenAI API](https://platform.openai.com/docs)

## License

MIT

## Support

For issues or questions, refer to:
- LiveKit Community: https://livekit.io/community
- GitHub Issues: [Your repo URL]
