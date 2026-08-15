import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from google import genai
from pydantic import BaseModel

from backend.app.vector_store import query_rules

# Load secrets from your .env file
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in .env")

# Instantiate our persistent client exactly once globally at boot time
client = genai.Client(api_key=GEMINI_KEY)

app = FastAPI(title="NitiMitra AI: Compliance Agent")

# Configure security permissions so UI can talk to this API backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Structure layout of data our API expects to receive
class ChatRequest(BaseModel):
    question: str


@app.get("/api/health")
def heatlth_check():
    return {"status": "active", "system": "RBI Compliance Core Ready"}


@app.post("/api/chat")
async def compliance_chat(payload: ChatRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # 1. Query your database using the question sent by user
        search_results = query_rules(payload.question)
        documents = search_results.get("documents", [[]])

        # Fallback check if nothing matched in the database
        matched_text = "No direct matching circular found."
        if documents and len(documents[0]) > 0:
            matched_text = documents[0][0]

        # 2. create the multi-agent auditor system prompt for NitiMitra Ai
        auditor_prompt = f"""
        You are an expert RBI Compliance Auditor assistant.
        Evaluate the User Question strictly against the provided regulatory text, laws, policy, scheme rules.


        CRITICAL LAWS:
        - Answer using ONLY the facts inside the Context block below.
        - if the context does not contain the answer, say 'Data not found'.
        - Do not hallucinate or make up any sections, rules, laws, policy or scheme rules.

        [Regulatory Context]
        {matched_text}

        [User Question]
        {payload.question}
        """

        # 3. Define a generator function to yield tokens as they arrive from LLM
        def response_generator():
            # Use generate_content_stream instead of generate_content
            response_stream = client.models.generate_content_stream(
                model="gemini-3.6-flash",
                contents=auditor_prompt,
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text  # Safely stream word tokens out to the client browser

        # 4. Return a live streaming media connection channel instead of a rigid JSON object
        return StreamingResponse(response_generator(), media_type="text/plain")

    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
