# app/retrieve.py

import chromadb

from app.embedder import embedding_model

# --- Setup: connect to the SAME model and SAME database ingest.py used ---
# PersistentClient means "read from disk", not "start fresh in memory".
# This MUST be the same path as ingest.py, or we'll be looking at an empty cabinet.
chroma_client = chromadb.PersistentClient(path="data/chroma_db")

# get_or_create_collection is safe to call again here - it just opens the
# existing "research_papers" drawer that ingest.py already filled.
collection = chroma_client.get_or_create_collection(name="research_papers")


def query_chunks(query_text: str, top_k: int = 5):
    """
    Takes a professor's typed research question and returns the top_k
    most semantically similar chunks stored in ChromaDB.

    Args:
        query_text: the professor's query, e.g. "transformer architectures
                     for low-resource language translation"
        top_k: how many chunks to retrieve (default 5, per the task brief)

    Returns:
        A list of dicts, each with: chunk text, paper title, chunk index,
        and a distance score (lower = more similar).
    """

    # Step 1: turn the query into the same kind of "meaning coordinate"
    # (embedding) that every stored chunk already has.
    # .tolist() converts it from a numpy array to a plain Python list,
    # which is the format ChromaDB expects.
    query_embedding = embedding_model.encode(query_text).tolist()

    # Step 2: ask ChromaDB - "which stored chunks sit closest to this
    # coordinate?" This is the actual semantic search step.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Step 3: ChromaDB returns results in parallel lists (all documents,
    # all metadatas, all distances - matched by position). We reshape
    # this into a clean list of dicts, which is much easier to work with
    # later in the Generation Layer.
    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return chunks


# --- Quick manual test when running this file directly ---
# sys.argv lets us pass the query straight from the terminal command,
# instead of editing this file every time we want to test something new.
import sys

if __name__ == "__main__":
    # If a query was typed after the filename, use it. Otherwise fall back
    # to a default so the script never crashes from a missing argument.
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    else:
        test_query = "transformer architectures for low-resource language translation"

    found_chunks = query_chunks(test_query, top_k=5)

    print(f"\nQuery: {test_query}")
    print(f"Found {len(found_chunks)} chunks:\n")

    for idx, chunk in enumerate(found_chunks, start=1):
        print(f"--- Result {idx} (distance: {chunk['distance']:.4f}) ---")
        print(f"Paper: {chunk['metadata']}")
        print(f"Text preview: {chunk['text'][:150]}...\n")