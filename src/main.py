from sentence_transformers import SentenceTransformer

# Load the model directly from Hugging Face
model = SentenceTransformer("BAAI/bge-small-en")
 
# Define your sentences 
sentences = [
    "This is the first sentence.",
    "Here is another sentence to embed.",
]

# Generate embeddings
embeddings = model.encode(sentences)
print(embeddings)