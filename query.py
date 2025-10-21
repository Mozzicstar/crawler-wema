import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

# Load index and embeddings
index = faiss.read_index("wema_index_faiss/index.faiss")
with open("data/wema_embedded.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "How can I avoid phishing scams?"
query_vector = model.encode(query).astype("float32")

D, I = index.search(np.array([query_vector]), k=3)

print("🔎 Top matches:")
for rank, idx in enumerate(I[0]):
    print(f"\n#{rank+1}: {chunks[idx]['source']}")
    print(chunks[idx]['text'][:300], "...")
faiss.write_index(index, "wema_index.faiss")