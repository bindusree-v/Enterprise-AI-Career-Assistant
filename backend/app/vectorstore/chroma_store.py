"""
ChromaDB vector store integration.

Uses ChromaDB's built-in local embedding function (all-MiniLM-L6-v2)
so NO OpenAI API call is needed for embeddings.
OpenAI quota is preserved entirely for AI analysis (ATS, skill-gap, etc.)
"""
import os
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "/tmp/st_models"
from pathlib import Path
from typing import List, Optional, Tuple

# # Force HuggingFace cache into writable folder
# os.environ["HF_HOME"] = "data/hf_cache"
# os.environ["TRANSFORMERS_CACHE"] = "data/hf_cache"

# Path("data/hf_cache").mkdir(parents=True, exist_ok=True)

# FORCE ALL ML + CHROMA CACHE TO WRITABLE DIR
os.environ["HOME"] = "/tmp"
os.environ["XDG_CACHE_HOME"] = "/tmp/.cache"
# os.environ["HF_HOME"] = "/tmp/hf_cache"
# os.environ["TRANSFORMERS_CACHE"] = "/tmp/hf_cache"
# os.environ["SENTENCE_TRANSFORMERS_HOME"] = "/tmp/st_models"
# os.environ["CHROMA_CACHE"] = "/tmp/chroma_cache"

# Create directories
Path("/tmp/hf_cache").mkdir(parents=True, exist_ok=True)
Path("/tmp/st_models").mkdir(parents=True, exist_ok=True)
Path("/tmp/.cache").mkdir(parents=True, exist_ok=True)
Path("/tmp/chroma_cache").mkdir(parents=True, exist_ok=True)

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

COLLECTION_PREFIX = "resume_"


class ChromaVectorStore:
    """
    Manages per-resume ChromaDB collections using local embeddings.
    Zero OpenAI calls — fast and free.
    """

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[chromadb.ClientAPI] = None
        self._embed_fn = DefaultEmbeddingFunction()
        # Built-in local embedding function (downloads ~90MB model once)
        # from langchain_community.embeddings import HuggingFaceEmbeddings

        # self._embed_fn = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-MiniLM-L6-v2"
        # )

        # try:
        #     from langchain_huggingface import HuggingFaceEmbeddings

        #     self._embed_fn = HuggingFaceEmbeddings(
        #         model_name="sentence-transformers/all-MiniLM-L6-v2"
        #     )

        # except Exception as e:
        #     logger.error(f"Embedding load failed: {e}")
        #     self._embed_fn = None

        # self._embed_fn = DefaultEmbeddingFunction()
        # from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        # self._embed_fn = SentenceTransformerEmbeddingFunction(
        #     model_name="all-MiniLM-L6-v2",
        #     device="cpu"
        # )
        # self._embed_fn = SentenceTransformerEmbeddingFunction(
        #     model_name="all-MiniLM-L6-v2"
        # )
        # try:
        #     from langchain_community.embeddings import HuggingFaceEmbeddings

        #     self._embed_fn = HuggingFaceEmbeddings(
        #         model_name="all-MiniLM-L6-v2"
        #     )

        # except Exception as e:
        #     logger.warning(f"HuggingFaceEmbeddings failed: {e}")

        #     from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        #     self._embed_fn = SentenceTransformerEmbeddingFunction(
        #         model_name="all-MiniLM-L6-v2",
        #         device="cpu"
        #     )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            persist_dir = Path(self.settings.chroma_persist_dir)
            persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("ChromaDB client initialized", path=str(persist_dir))
        return self._client

    def get_collection_name(self, resume_id: str) -> str:
        safe_id = resume_id.replace("-", "_")
        return f"{COLLECTION_PREFIX}{safe_id}"

    async def embed_resume(
        self, resume_id: str, text: str, metadata: Optional[dict] = None
    ) -> Tuple[str, int]:
        """Chunk text and store with local embeddings. No API calls."""
        # if self._embed_fn is None:
        #     raise RuntimeError("Embedding model not initialized")
        # if self._embed_fn is None:
        #     logger.error("Embedding service unavailable")
        #     self._embed_fn = DefaultEmbeddingFunction()
    
        collection_name = self.get_collection_name(resume_id)
        chunks = self.text_splitter.split_text(text)

        logger.info("Embedding resume locally", resume_id=resume_id, chunks=len(chunks))

        base_meta = metadata or {}
        base_meta["resume_id"] = resume_id

        # Delete existing collection if any
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass

        # Create collection with local embedding function
        # collection = self.client.create_collection(
        #     name=collection_name,
        #     metadata={"hnsw:space": "cosine"}
        # )
        # collection = self.client.get_or_create_collection(
        #     name=collection_name,
        #     embedding_function=DefaultEmbeddingFunction()
        # )

        collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embed_fn
        )
        
        # collection = self.client.get_collection(name=collection_name)

        # collection = self.client.get_collection(name=collection_name)

        # results = collection.query(
        #     query_texts=[query],
        #     n_results=k
        # )

        # Add documents in batches
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ids = [f"{resume_id}_chunk_{i + j}" for j in range(len(batch))]
            metadatas = [
                {**base_meta, "chunk_index": i + j, "chunk_total": len(chunks)}
                for j in range(len(batch))
            ]
            metadatas = [
                {
                    **base_meta,
                    "chunk_index": i + j,
                    "chunk_total": len(chunks)
                }
                for j in range(len(batch))
            ]

            collection.add(
                documents=batch,
                metadatas=metadatas,
                ids=ids
            )

            # embeddings = self._embed_fn.embed_documents(batch)

            # embeddings = self._embed_fn(batch).tolist()
            # embeddings = self._embed_fn(batch)
            # embeddings = self._embed_fn.embed_documents(batch)

            # collection.add(
            #     documents=batch,
            #     # embeddings=embeddings,
            #     metadatas=metadatas,
            #     ids=ids
            # )
            # collection.add(documents=batch, metadatas=metadatas, ids=ids)

        logger.info("Local embeddings stored", collection=collection_name, chunks=len(chunks))
        return collection_name, len(chunks)

    async def similarity_search(
        self, resume_id: str, query: str, k: int = 5
    ) -> List[Document]:
        """Semantic search using local embeddings — no API call."""
        collection_name = self.get_collection_name(resume_id)
        try:
            collection = self.client.get_collection(
                name=collection_name
            )
            results = collection.query(query_texts=[query], n_results=min(k, collection.count()))
            docs = []
            for i, doc_text in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                docs.append(Document(page_content=doc_text, metadata=meta))
            return docs
        except Exception as e:
            logger.warning("Similarity search failed", error=str(e))
            return []

    def get_retriever(self, resume_id: str, k: int = 5):
        """Simple wrapper that returns self for compatibility."""
        return self  # agents call similarity_search directly

    def collection_exists(self, resume_id: str) -> bool:
        collection_name = self.get_collection_name(resume_id)
        try:
            collections = self.client.list_collections()
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False


_chroma_store: Optional[ChromaVectorStore] = None


def get_chroma_store() -> ChromaVectorStore:
    global _chroma_store
    if _chroma_store is None:
        _chroma_store = ChromaVectorStore()
    return _chroma_store
