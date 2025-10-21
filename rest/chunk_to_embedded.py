"""
RAG Data Prep for Wema Bank
---------------------------
This script takes your cleaned JSON (wema_cleaned.json),
splits the text into chunks, generates embeddings using
a local sentence-transformers model, and builds a FAISS index.
"""

import json
import numpy as np
from textwrap import wrap
from sentence_transformers import SentenceTransformer
import faiss
import os

# ---------- STEP 1: CONFIG ----------
INPUT_FILE = "wema_cleaned.json"
CHUNK_FILE = "wema_chunks.json"
EMBEDDED_FILE = "wema_embedded.json"
FAISS_INDEX_FILE = "wema_index.faiss"

CHUNK_SIZE = 800  # characters per chunk (~120–150 tokens)
MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, reliable

# ---------- STEP 2: LOAD CLEANED DATA ----------
if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"❌ Could not find {INPUT_FILE}. Make sure you’ve cleaned your data first.")

print(f"📂 Loading data from {INPUT_FILE}...")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    docs = json.load(f)

# ---------- STEP 3: CHUNK TEXT ----------
print("✂️ Splitting text into chunks...")
chunks = []
for doc in docs:
    text = doc.get("text", "").strip()
    if not text:
        continue

    parts = wrap(text, CHUNK_SIZE)
    for i, part in enumerate(parts):
        chunks.append({
            "id": f"{doc['url']}#chunk-{i}",
            "source": doc["url"],
            "title": doc.get("title", ""),
            "chunk_index": i,
            "text": part
        })

with open(CHUNK_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)
print(f"✅ Created {len(chunks)} chunks → saved to {CHUNK_FILE}")

# ---------- STEP 4: GENERATE EMBEDDINGS ----------
print(f"🧠 Loading embedding model: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

print("⚙️ Generating embeddings...")
for c in chunks:
    c["embedding"] = model.encode(c["text"]).tolist()

with open(EMBEDDED_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"✅ Embeddings generated and saved to {EMBEDDED_FILE}")

# ---------- STEP 5: BUILD FAISS INDEX ----------
print("💾 Creating FAISS index...")
embeddings = np.array([c["embedding"] for c in chunks], dtype="float32")
dimension = len(embeddings[0])

index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

faiss.write_index(index, FAISS_INDEX_FILE)
print(f"✅ FAISS index built and saved to {FAISS_INDEX_FILE}")

print("\n🎉 All done! Your RAG data is ready.")
print(f"Total chunks indexed: {len(chunks)}")
print(f"Index dimension: {dimension}")
print(f"FAISS index file size: {os.path.getsize(FAISS_INDEX_FILE) / 1024:.2f} KB")