from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

        context_blocks = []
        for number, result in enumerate(results, start=1):
            source = result["metadata"].get("doc_id") or result["metadata"].get("source") or result.get("id")
            context_blocks.append(f"[{number}] (nguồn: {source})\n{result['content']}")
        context = "\n\n".join(context_blocks)

        prompt = (
            "Bạn là trợ lý trả lời câu hỏi dựa trên tài liệu được cung cấp.\n"
            "Quy tắc:\n"
            "- Chỉ sử dụng thông tin trong NGỮ CẢNH, không suy đoán thêm.\n"
            "- Trích dẫn số [n] của đoạn ngữ cảnh đã dùng sau mỗi ý.\n"
            '- Nếu ngữ cảnh không có thông tin, trả lời: "Không tìm thấy thông tin trong tài liệu."\n\n'
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )
        return self.llm_fn(prompt)
