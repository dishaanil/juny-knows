# Juny 🗽

> *Because every great trip needs someone who's already been there.*

Juny is a voice agent that acts as your personalized NYC local friend. Tell Juny where you are and she'll give you the insider scoop — history, hacks, and vibes tailored to who you are. Same location, completely different experience depending on your profile.

---

## Demo

Pick who you are → hit **Start talking to Juny!** → Juny auto-detects your location and starts the conversation.

**Profiles**
- 🎓 **Just Vibing** — cheap eats, late nights, real talk
- 👨‍👩‍👧 **Travelling with Kids** — fun, safe, and surprisingly cool
- 🗽 **Culture First** — history, context, the real story

**Supported locations**
- Times Square
- Washington Square Park
- The High Line
- Grand Central Terminal
- Wall Street / Bowling Green
- Chelsea Market

---

## How it works

1. User selects a profile
2. On call start, the browser requests GPS coordinates
3. Google Maps Geocoding API reverse-geocodes to the nearest known location
4. Claude generates a personalized opening greeting
5. AssemblyAI streams mic audio in real time — when you speak, Juny listens; when Juny speaks, you can interrupt and she stops mid-sentence
6. Every response is tailored to your profile using hardcoded NYC knowledge + Claude

---

## Tech Stack

- **AssemblyAI Streaming STT** — real-time transcription with barge-in interruption detection
- **Anthropic Claude Sonnet** — personalized, voice-optimized responses per profile
- **Google Maps Geocoding API** — auto-detects your NYC location on call start
- **Browser SpeechSynthesis** — zero-latency TTS playback
- **FastAPI** — backend handling tokens, Claude calls, geocoding, and static file serving
- **Google Cloud Run** — containerized deployment

---

## Project Structure

```
juny/
├── backend/
│   ├── main.py          # FastAPI — /token, /locate, /greet, /chat
│   ├── knowledge.py     # Hardcoded NYC content for 6 locations × 3 profiles
│   └── .env.example     # API key template
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js           # AudioWorklet → AssemblyAI WS → Claude → SpeechSynthesis
├── Dockerfile
└── requirements.txt
```

---

## Running locally

**1. Clone and install**
```bash
git clone https://github.com/dishaanil/juny-knows.git
cd juny-knows
pip install -r requirements.txt
```

**2. Add your API keys**
```bash
cp backend/.env.example backend/.env
# Fill in your keys in backend/.env
```

You'll need:
- [AssemblyAI API key](https://www.assemblyai.com/dashboard/api-keys)
- [Anthropic API key](https://console.anthropic.com)
- [Google Maps Geocoding API key](https://console.cloud.google.com)

**3. Start the server**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**4. Open in browser**
```
http://localhost:8000
```

> **Tip:** Use headphones for the best barge-in experience. Echo cancellation works best when Juny's voice isn't bleeding into your mic.

---

## Deploying to Google Cloud Run

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

gcloud run deploy juny \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ASSEMBLYAI_API_KEY=...,ANTHROPIC_API_KEY=...,GOOGLE_MAPS_API_KEY=..."
```

---

Built for the AssemblyAI Hackathon.
