
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.graph import graph

app = FastAPI(
    title="Niyam AI Chatbot API",
    description="RAG Based AI Chatbot",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development only
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Schema
class ChatRequest(BaseModel):
    query: str
    thread_id: str = "abc123"


# Chat API
@app.post("/chat")
async def chat(request: ChatRequest):

    try:
        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }

        response = await graph.ainvoke(
            {
                "original_question": request.query
            },
            config=config
        )

        # Extract only PDF name and page number
        sources = [
            {
                "pdf_name": source.source.split("\\")[-1].split("/")[-1],
                "page": source.page
            }
            for source in response.get("source", [])
        ]

        return {
            "original_question":response.get("original_question",""),
            "rewritted_question":response.get("question",""),
            "category":response.get("categories",[]),
            "answer": response.get("generated_answer", ""),
            "sources": sources,
            "grades":response.get("grades", []),
            "relavance_score":response.get("relavance_score",0.0),
            "overall_score": response.get("overall_score", 0.0),
            "evaluation":response.get("evaluation",[]),
            "retry":response.get("retry",0)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# Health Check
@app.get("/")
async def home():
    return {
        "message": "Niyam AI Chatbot API is running"
    }
