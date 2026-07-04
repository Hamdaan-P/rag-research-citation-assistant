# app/generate.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

from app.config import RELEVANCE_THRESHOLD

# Load API key from .env, same pattern as our test script
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def build_context_block(chunks: list) -> str:
    """
    Takes the list of chunks returned by query_chunks() and turns them
    into a clearly labeled text block for the LLM to read from.

    Why this matters: the LLM should NEVER guess which paper a piece of
    text came from. By labeling every chunk with its paper title, we make
    it easy for the LLM to cite correctly (Rule 3 of the task brief:
    never fabricate citations).
    """
    labeled_chunks = []

    for idx, chunk in enumerate(chunks, start=1):
        title = chunk["metadata"]["paper_title"]
        text = chunk["text"]
        # Each chunk gets a numbered label + its source paper title
        labeled_chunks.append(f"[Source {idx}: \"{title}\"]\n{text}")

    # Join all labeled chunks with a blank line between them
    return "\n\n".join(labeled_chunks)

def generate_related_work(query: str, chunks: list) -> str:
    """
    Takes the professor's query + the retrieved chunks, and asks Gemini
    to write a 2-3 paragraph Related Work summary — citing ONLY the
    papers present in the retrieved chunks (never fabricated).
    """
    # Step 0: relevance check — if even the BEST match is too "far" in
    # meaning-space, the library likely has nothing genuinely relevant.
    # Distance is a measure of semantic closeness: smaller = more similar.
    if not chunks or chunks[0]["distance"] > RELEVANCE_THRESHOLD:
        return ("No sufficiently relevant papers were found in your library "
                "for this topic. Try rephrasing your query, or upload papers "
                "related to this subject.")
    # Step 1: build the labeled context block from retrieved chunks
    context_block = build_context_block(chunks)

    # Step 2: build the instruction prompt
    # We explicitly tell the model to ONLY use what's given — this is
    # the core RAG safety rule from the task brief.
    prompt = f"""You are an academic writing assistant helping a researcher write a Related Work section.

The researcher's topic is:
"{query}"

Below are excerpts retrieved from their personal paper library. Each excerpt is labeled with its source paper title.

{context_block}

Instructions:
- Write a 2-3 paragraph "Related Work" summary describing how these papers relate to the researcher's topic.
- You MUST cite papers ONLY by the titles shown above in the [Source X: "..."] labels.
- Do NOT cite, reference, or mention any paper that is not shown above.
- Do NOT invent, guess, or hallucinate any paper titles, authors, or facts not present in the excerpts.
- Write in a formal academic tone.
"""

    # Step 3: call Gemini with this prompt
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text

# --- Quick manual test when running this file directly ---
# sys.argv lets us pass the query straight from the terminal command,
# same pattern as retrieve.py, so we don't have to edit this file every time.
import sys

if __name__ == "__main__":
    from retrieve import query_chunks

    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    else:
        test_query = "transformer architectures for low-resource language translation"

    print(f"Query: {test_query}\n")
    print("Retrieving relevant chunks...")
    chunks = query_chunks(test_query, top_k=5)

    print(f"Found {len(chunks)} chunks. Generating Related Work summary...\n")
    summary = generate_related_work(test_query, chunks)

    print("=" * 60)
    print("RELATED WORK SUMMARY:")
    print("=" * 60)
    print(summary)