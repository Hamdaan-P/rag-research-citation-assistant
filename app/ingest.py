"""
ingest.py
Phase 1 - Step 4 (final): Extract, chunk, embed, and store chunks in ChromaDB —
persisted to disk so the data survives a server restart.

Why this matters in the RAG pipeline:
This is the step that makes everything "permanent" and searchable later.
Each chunk is stored along with:
  - its embedding (the meaning-vector, for semantic search)
  - its raw text (so we can show/use it later)
  - metadata: which paper it came from + its position in that paper
    (so we can cite the correct source later — never fabricate citations)
"""

import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb

from app.embedder import embedding_model

# Create a persistent ChromaDB client.
# "persistent" means it writes to disk at this path — NOT just kept in memory.
# This satisfies the task brief's hard requirement: data must survive a restart.
chroma_client = chromadb.PersistentClient(path="data/chroma_db")

# get_or_create_collection: like "get this filing cabinet drawer, or make it
# if it doesn't exist yet." A "collection" is ChromaDB's term for a named
# group of stored chunks — we'll use one collection for all papers.
collection = chroma_client.get_or_create_collection(name="research_papers")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Opens a PDF file and extracts all text from every page."""
    doc = fitz.open(pdf_path)
    all_text = []
    for page in doc:
        all_text.append(page.get_text())
    doc.close()
    return "\n".join(all_text)


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """Splits a long string of text into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Converts a list of text chunks into a list of embedding vectors."""
    embeddings = embedding_model.encode(chunks)
    return embeddings.tolist()


def ingest_pdf(pdf_path: str, paper_title: str):
    """
    Full pipeline for one PDF: extract -> chunk -> embed -> store in ChromaDB.

    Args:
        pdf_path: path to the PDF file on disk.
        paper_title: human-readable title, used later for citations.
                     (For now we pass it in manually; later we could try to
                     auto-detect it from the PDF itself.)
    """
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    embeddings = embed_chunks(chunks)

    # ChromaDB needs a unique ID for every chunk we store.
    # We build IDs like "attention_is_all_you_need_chunk_0", "..._chunk_1", etc.
    # Using the filename (without extension) keeps IDs unique across papers.
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    ids = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]

    # Metadata: one dictionary per chunk, storing facts we'll need later
    # (paper title for citations, chunk index for ordering/debugging).
    metadatas = [
        {"paper_title": paper_title, "chunk_index": i, "source_file": file_name}
        for i in range(len(chunks))
    ]

    # This is the actual "save to disk" step.
    # documents = the raw text of each chunk (so we can read/display it later)
    # embeddings = the meaning-vectors (so we can semantically search later)
    # metadatas = the source info (so we can cite correctly later)
    # ids = unique identifiers (so ChromaDB can update/delete specific chunks later)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )

    print(f"Stored {len(chunks)} chunks from '{paper_title}' into ChromaDB.")

    # Return a small summary so callers (like the FastAPI upload route)
    # can report back to the user what actually happened.
    return {"paper_title": paper_title, "chunks_stored": len(chunks)}


if __name__ == "__main__":
    # A simple list of (file path, human-readable title) pairs.
    # Later, in the FastAPI upload route, the title will come from the
    # professor's upload form instead of being hardcoded like this.
    papers_to_ingest = [
        ("data/uploads/attention_is_all_you_need.pdf", "Attention Is All You Need"),
        ("data/uploads/bert.pdf", "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding"),
        ("data/uploads/bahdanau_attention.pdf", "Neural Machine Translation by Jointly Learning to Align and Translate"),
    ]

    for pdf_path, paper_title in papers_to_ingest:
        ingest_pdf(pdf_path=pdf_path, paper_title=paper_title)

    print(f"\nTotal chunks in ChromaDB collection: {collection.count()}")
