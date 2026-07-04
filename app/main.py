import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb

from app.ingest import ingest_pdf
from app.retrieve import query_chunks
from app.generate import generate_related_work
from app.config import RELEVANCE_THRESHOLD

chroma_client = chromadb.PersistentClient(path="data/chroma_db")
collection = chroma_client.get_or_create_collection(name="research_papers")

app = FastAPI(
    title="RAG Research Citation Assistant",
    description="Upload papers, ask questions, get cited Related Work summaries.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def health_check():
    return {"status": "ok", "message": "RAG Research Citation Assistant API is running"}


@app.get("/papers")
def list_papers():
    results = collection.get()
    metadatas = results["metadatas"]

    if not metadatas:
        return {"total_papers": 0, "papers": []}

    papers_dict = {}
    for meta in metadatas:
        title = meta["paper_title"]
        if title not in papers_dict:
            papers_dict[title] = {
                "paper_title": title,
                "source_file": meta["source_file"],
                "chunk_count": 0
            }
        papers_dict[title]["chunk_count"] += 1

    papers_list = list(papers_dict.values())
    return {"total_papers": len(papers_list), "papers": papers_list}


@app.post("/upload")
async def upload_paper(
    file: UploadFile = File(...),
    paper_title: str = Form(...)
):
    if not paper_title or not paper_title.strip():
        raise HTTPException(status_code=400, detail="paper_title cannot be empty.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs("data/uploads", exist_ok=True)

    # Never trust file.filename directly: FastAPI/Starlette does not sanitize
    # it, so a crafted name containing "../" could write outside
    # data/uploads (path traversal), and two unrelated uploads sharing the
    # same client-supplied filename would collide on the same on-disk path
    # and on the ChromaDB chunk IDs derived from it. A random UUID name
    # sidesteps both problems.
    safe_filename = f"{uuid.uuid4().hex}.pdf"
    save_path = os.path.join("data/uploads", safe_filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if os.path.getsize(save_path) == 0:
        os.remove(save_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = ingest_pdf(pdf_path=save_path, paper_title=paper_title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    return {
        "status": "success",
        "paper_title": result["paper_title"],
        "chunks_stored": result["chunks_stored"]
    }


@app.post("/query")
def query_papers(request: QueryRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty.")

    try:
        chunks = query_chunks(query_text=request.query, top_k=5)

        for chunk in chunks:
            paper_title = chunk["metadata"]["paper_title"]
            chunk_index = chunk["metadata"]["chunk_index"]
            print(f"[DEBUG] Retrieved: {paper_title} - chunk {chunk_index}")

        summary = generate_related_work(query=request.query, chunks=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

    source_papers = []
    if chunks and chunks[0]["distance"] <= RELEVANCE_THRESHOLD:
        seen = set()
        for chunk in chunks:
            title = chunk["metadata"]["paper_title"]
            if title not in seen:
                seen.add(title)
                source_papers.append(title)

    return {
        "query": request.query,
        "summary": summary,
        "source_papers": source_papers
    }


@app.delete("/papers/{paper_title}")
def delete_paper(paper_title: str):
    # Rule 4: reject empty/whitespace-only paper_title (e.g. someone hitting /papers/ with nothing).
    if not paper_title or not paper_title.strip():
        raise HTTPException(status_code=400, detail="paper_title cannot be empty.")

    # Check the paper actually exists BEFORE attempting to delete anything.
    # This prevents a silent no-op and gives the professor a clear error
    # if they mistype a title or the paper was already removed.
    existing = collection.get(where={"paper_title": paper_title})

    if not existing["ids"]:
        raise HTTPException(
            status_code=404,
            detail=f"No paper found with title '{paper_title}'."
        )

    chunks_to_delete = len(existing["ids"])

    # ChromaDB's where filter deletes every chunk whose metadata
    # matches this paper_title in one call - no manual ID looping needed.
    collection.delete(where={"paper_title": paper_title})

    return {
        "status": "success",
        "paper_title": paper_title,
        "chunks_deleted": chunks_to_delete
    }
