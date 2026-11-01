class RAGService:
    """RAG extension point. Retrieval is not implemented without a vector store."""

    async def retrieve_context(self, query: str) -> list[str]:
        del query
        return []
