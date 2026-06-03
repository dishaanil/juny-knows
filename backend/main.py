import os
from pathlib import Path

import httpx
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from knowledge import get_knowledge, PROFILE_LABELS, nearest_location, LOCATION_DISPLAY

load_dotenv()

ASSEMBLYAI_API_KEY  = os.environ["ASSEMBLYAI_API_KEY"]
GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]
anthropic = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

SYSTEM_PROMPT = """You are Juny, a voice guide who speaks like a local friend — not a tour guide, not a travel blogger. You know the hacks, the history, and the vibe of NYC.

You will be given:
- A user profile (college_student / family_kids / adult_explorer)
- A location in NYC
- Relevant local knowledge for that profile + location
- What the user just asked

Rules:
- Respond in 3-4 sentences maximum. This is a voice agent — brevity is everything.
- Sound like a friend texting you insider info, not a Wikipedia article
- Tailor everything to the profile. A college student and a 55-year-old should feel like they're talking to a completely different Juny.
- Lead with the most surprising or useful thing first
- Never say "as a local" or "hidden gem" — show don't tell
- Never use bullet points or lists — flowing speech only"""


# ── Models ────────────────────────────────────────────────────────────────────
class HistoryEntry(BaseModel):
    role: str       # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    profile: str
    location: str
    transcript: str
    history: list[HistoryEntry] = []


class GreetRequest(BaseModel):
    profile: str
    location_key: str   # e.g. "high_line"
    location_name: str  # e.g. "the High Line"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/token")
async def get_token():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://streaming.assemblyai.com/v3/token?expires_in_seconds=60",
            headers={"Authorization": ASSEMBLYAI_API_KEY},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to mint AssemblyAI token")
    return resp.json()


@app.get("/locate")
async def locate(lat: float, lng: float):
    """
    1. Find nearest known Juny location by distance.
    2. Call Google Maps Reverse Geocoding for a human-readable address.
    Returns { location_key, location_name, address, found }
    found=False means user is >1km from any known spot.
    """
    match = nearest_location(lat, lng)

    # Google Maps reverse geocode for display address
    address = ""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"latlng": f"{lat},{lng}", "key": GOOGLE_MAPS_API_KEY},
            )
        data = resp.json()
        if data.get("results"):
            address = data["results"][0].get("formatted_address", "")
    except Exception:
        pass  # address is cosmetic — don't fail the whole request

    if match:
        return {
            "found": True,
            "location_key":  match["key"],
            "location_name": match["name"],
            "address":       address,
            "distance_km":   match["distance_km"],
        }
    else:
        return {
            "found": False,
            "location_key":  None,
            "location_name": None,
            "address":       address,
        }


@app.post("/greet")
async def greet(req: GreetRequest):
    """Generate Juny's opening greeting for a detected location."""
    knowledge = get_knowledge(req.location_key, req.profile)

    if knowledge:
        knowledge_block = f"""Location: {knowledge['location_name']}
Hook fact: {knowledge['hook']}
Practical hack: {knowledge['hack']}
Only locals know: {knowledge['locals_only']}"""
    else:
        knowledge_block = f"Location: {req.location_name}"

    prompt = f"""Profile: {req.profile}
{knowledge_block}

Generate a short opening greeting (1-2 sentences max) that:
- Confirms you know the user is at {req.location_name}
- Sounds like a friend who's excited to tell them something, not a tour guide
- Ends with a natural invite to ask questions or just explore together
- Is tailored to the profile — a college student greeting feels totally different from an adult explorer greeting
Example style (do NOT copy verbatim): "Hey! You picked a good one — Grand Central has more going on than most people realise. Ask me anything or just tell me what you're into."
"""

    message = await anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=120,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"greeting": message.content[0].text}


@app.post("/chat")
async def chat(req: ChatRequest):
    if req.profile not in PROFILE_LABELS:
        raise HTTPException(status_code=400, detail="Unknown profile")

    knowledge = get_knowledge(req.location or req.transcript, req.profile)

    if knowledge:
        knowledge_block = f"""Location: {knowledge['location_name']}
Hook fact: {knowledge['hook']}
Practical hack: {knowledge['hack']}
Only locals know: {knowledge['locals_only']}"""
    else:
        knowledge_block = f"Location mentioned: {req.location or 'not specified'}\nNo specific local knowledge stored for this location — use your general NYC knowledge."

    first_user_content = f"""Profile: {req.profile}
{knowledge_block}

User asked: {req.transcript}"""

    if req.history:
        messages = []
        for entry in req.history:
            messages.append({"role": entry.role, "content": entry.content})
        messages.append({"role": "user", "content": f"Profile: {req.profile}\n{knowledge_block}\n\nUser said: {req.transcript}"})
    else:
        messages = [{"role": "user", "content": first_user_content}]

    message = await anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    return {"response": message.content[0].text}


# Serve frontend static files
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
