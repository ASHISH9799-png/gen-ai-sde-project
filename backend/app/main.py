from app.vector_store import query_rules
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RBI Banking Law Compliance AI Agent")


# Configures security permissions so UI can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# this defines the structural layout of data our API expects to recieve
class ChatRequest(BaseModel):
    question: str


@app.get("/api/health")
def health_check():
    return {"status": "active", "system": "RBI Compliance Core Ready"}


@app.post("/api/chat")
def compliance_chat(payload: ChatRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # 1. query your database using the question sent by user
        search_results = query_rules(payload.question)

        # 2. Extract the text chunks that matched
        documents = search_results.get("documents", [[]])
        metadatas = search_results.get("metadatas", [[]])

        # Fallback check if nothing matched in the database
        if documents and len(documents[0]) > 0:
            matched_text = documents[0][0]
            source_info = (
                metadatas[0][0] if (metadatas and len(metadatas[0]) > 0) else {}
            )

        else:
            matched_text = "NO diect regulatory text found in vector database match."
            source_info = {"doc_name": "N/A", "section": "N/A"}

        # 3. Return the real data back to the user
        return {
            "answer": matched_text,
            "citations": [
                {
                    "source": source_info.get("doc_name", "RBI Database"),
                    "section": source_info.get("section", "General Compliance"),
                    "link": "https://rbi.org.in",
                }
            ],
        }

    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail="Complaince database engine failure: " + str(e)
        )
