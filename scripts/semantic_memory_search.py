#!/usr/bin/env python3
"""
Semantic Memory Search for OpenClaw
Vector-powered semantic search for markdown memory files
"""
import os
import glob
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import re

class SemanticMemorySearch:
    def __init__(self, memory_dir="/Users/geon/.openclaw/workspace/memory"):
        self.memory_dir = memory_dir
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=os.path.join(memory_dir, ".chroma")
        ))
        
        self.collection = self.client.get_or_create_collection(
            name="memory_search",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.indexed = False
    
    def chunk_text(self, text, chunk_size=500, overlap=100):
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks
    
    def index_memories(self):
        """Index all markdown files in memory directory"""
        print("🔄 Indexing memory files...")
        
        memory_files = glob.glob(os.path.join(self.memory_dir, "*.md"))
        
        documents = []
        metadatas = []
        ids = []
        
        for file_path in memory_files:
            file_name = os.path.basename(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if file hasn't changed
            file_stat = os.stat(file_path)
            file_id = f"{file_name}_{file_stat.st_mtime}"
            
            # Split into chunks
            chunks = self.chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "file": file_name,
                    "chunk": i,
                    "path": file_path
                })
                ids.append(f"{file_name}_chunk_{i}")
        
        # Clear existing and add new
        if documents:
            self.collection.delete(where={})
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            self.indexed = True
            print(f"✅ Indexed {len(documents)} chunks from {len(memory_files)} files")
        else:
            print("⚠️  No memory files found")
    
    def search(self, query, n_results=5):
        """Semantic search over memories"""
        if not self.indexed:
            self.index_memories()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return results
    
    def format_results(self, results):
        """Format search results for display"""
        formatted = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            relevance = (1 - distance) * 100
            formatted.append({
                'content': doc[:300] + "..." if len(doc) > 300 else doc,
                'file': metadata['file'],
                'relevance': f"{relevance:.1f}%",
                'chunk': metadata['chunk']
            })
        
        return formatted

def main():
    """CLI interface"""
    import sys
    
    search_engine = SemanticMemorySearch()
    
    if len(sys.argv) > 1 and sys.argv[1] == "index":
        # Just index
        search_engine.index_memories()
    elif len(sys.argv) > 1:
        # Search
        query = " ".join(sys.argv[1:])
        results = search_engine.search(query)
        formatted = search_engine.format_results(results)
        
        print(f"\n🔍 Search results for: '{query}'\n")
        print("=" * 60)
        
        for i, result in enumerate(formatted, 1):
            print(f"\n{i}. 📄 {result['file']} (Relevance: {result['relevance']})")
            print(f"   {result['content']}")
        
        print("\n" + "=" * 60)
    else:
        print("Usage:")
        print("  python3 semantic_memory_search.py index")
        print("  python3 semantic_memory_search.py <query>")

if __name__ == "__main__":
    main()
