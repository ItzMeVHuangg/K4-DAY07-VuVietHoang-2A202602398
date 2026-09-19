"""Benchmark retrieval trên corpus data/university — Lab 07 K4-L3A.

Chạy:  python bench.py
Kết quả in ra màn hình và ghi vào ket_qua_benchmark.txt.

Mỗi thành viên CHỈ đổi dòng `CHUNKER = ...` sang chiến lược của mình;
mọi thứ khác giữ nguyên để so sánh công bằng trong nhóm.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

DATA_DIR = Path("data/university")
OUTPUT_FILE = Path("ket_qua_benchmark.txt")
TOP_K = 3


class HeadingChunker:
    """Chunk theo tiêu đề Markdown: mỗi section (## / ###) là một chunk.

    Lý do: thông báo học bổng được biên soạn theo mục (Đối tượng, Giá trị, Hồ sơ, Thời hạn...),
    mỗi mục đã là một đơn vị ngữ nghĩa trọn vẹn. Section dài quá ngưỡng thì hạ xuống
    RecursiveChunker và gắn lại tiêu đề vào đầu từng mảnh con để không mất ngữ cảnh.

    prepend_title=True: gắn thêm tiêu đề tài liệu (dòng '# ...') vào đầu MỌI chunk. Section
    như "## 2. Giá trị học bổng" không nhắc tên học bổng/tên trường, nên nếu thiếu tiêu đề
    thì embedding không biết chunk đó thuộc học bổng nào.
    """

    def __init__(self, max_chunk_size: int = 800, prepend_title: bool = False) -> None:
        self.max_chunk_size = max_chunk_size
        self.prepend_title = prepend_title
        self._fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        chunks = self._chunk_sections(text)
        title_match = re.match(r"# (.+)", text.strip())
        if not self.prepend_title or not title_match:
            return chunks
        title = f"[{title_match.group(1).strip()}]"
        return [chunk if chunk.startswith("# ") else f"{title}\n{chunk}" for chunk in chunks]

    def _chunk_sections(self, text: str) -> list[str]:
        sections = re.split(r"\n(?=#{1,6} )", text.strip())
        chunks: list[str] = []
        pending_heading = ""
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if pending_heading:
                section = f"{pending_heading}\n{section}"
                pending_heading = ""
            if section.startswith("#") and "\n" not in section:
                # Heading cha không có nội dung riêng -> gộp vào section con kế tiếp
                pending_heading = section
                continue
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
                continue
            heading = section.splitlines()[0] if section.startswith("#") else ""
            body = section[len(heading):].strip() if heading else section
            for piece in self._fallback.chunk(body):
                chunks.append(f"{heading}\n{piece}" if heading else piece)
        if pending_heading:
            chunks.append(pending_heading)
        return chunks


# ===== MỖI THÀNH VIÊN CHỈ ĐỔI DÒNG NÀY =====
CHUNKER = HeadingChunker(max_chunk_size=250, prepend_title=True)
# CHUNKER = FixedSizeChunker(chunk_size=500, overlap=100)
# CHUNKER = RecursiveChunker(chunk_size=500)
# CHUNKER = SentenceChunker(max_sentences_per_chunk=3)
# ============================================

# 5 câu hỏi benchmark chung của nhóm.
#   gold_doc : doc_id của tài liệu chứa đáp án
#   key      : chuỗi đặc trưng PHẢI xuất hiện trong ngữ cảnh truy xuất được (chấm mức nội dung)
#   filter   : metadata_filter dùng khi chạy; câu có filter sẽ được chạy A/B (có / không filter)
QUERIES = [
    {
        "query": "Học bổng Vallet sau đại học năm 2026 có bao nhiêu suất và mỗi suất trị giá bao nhiêu?",
        "gold": "42 suất, mỗi suất 34.000.000 VNĐ",
        "gold_doc": "vallet-hoc-bong-sau-dai-hoc",
        "key": "34.000.000",
        "filter": None,
    },
    {
        "query": "Học bổng Vững tương lai loại A trị giá bao nhiêu và dành cho ai?",
        "gold": "130 suất, 20.000.000 VNĐ/suất; HSSV đạt chuẩn loại B và có thành tích xuất sắc, tiêu biểu / thủ khoa đầu vào / hoàn cảnh đặc biệt khó khăn",
        "gold_doc": "neu-hoc-bong-vung-tuong-lai-2025-2026",
        "key": "20.000.000",
        "filter": None,
    },
    {
        "query": "Điều kiện điểm học tập để xét học bổng TOTO ở Đại học Ngoại thương là gì?",
        "gold": "Điểm TBC năm học 2025-2026 từ 7.0/10 hoặc 2.8/4 trở lên; tích lũy tối thiểu 28 tín chỉ/năm học",
        "gold_doc": "ftu-hoc-bong-toto-2026",
        "key": "28 tín chỉ",
        "filter": None,
    },
    {
        "query": "Khi nào UEH ra quyết định cấp học bổng khuyến khích học tập học kỳ đầu năm 2026?",
        "gold": "18/5/2026 (học kỳ cuối năm 2026: 10/11/2026)",
        "gold_doc": "ueh-ke-hoach-xet-hoc-bong-2026",
        "key": "18/5/2026",
        "filter": None,
    },
    {
        "query": "Học bổng khuyến khích học tập ở VIMARU được xét như thế nào?",
        "gold": "Loại Khá: 2.50 ≤ ĐTBHB < 3.20, rèn luyện từ 70; Giỏi: 3.20 ≤ ĐTBHB < 3.60, từ 80; Xuất sắc: ĐTBHB ≥ 3.60, từ 90 đến 100",
        "gold_doc": "vimaru-hbkkht-tieu-chuan-sinh-vien",
        "key": "3.20",
        "filter": {"audience": "student"},
    },
]


class Tee:
    """In ra màn hình đồng thời ghi vào file kết quả."""

    def __init__(self, path: Path) -> None:
        self.file = path.open("w", encoding="utf-8")

    def __call__(self, text: str = "") -> None:
        print(text)
        self.file.write(text + "\n")

    def close(self) -> None:
        self.file.close()


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    """Tách YAML frontmatter thành metadata, phần còn lại là nội dung."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    _, raw_meta, body = text.split("---", 2)
    metadata = {}
    for key, value in re.findall(r"^(\w+):\s*(.+)$", raw_meta, re.M):
        metadata[key] = re.sub(r"\s+#.*$", "", value).strip().strip('"').strip("'")
    return metadata, body.strip()


def load_documents(chunker) -> list[Document]:
    documents = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, body = parse_markdown(path)
        for index, chunk in enumerate(chunker.chunk(body)):
            documents.append(
                Document(
                    id=f"{path.stem}#{index}",
                    content=chunk,
                    # frontmatter trải vào MỌI chunk để search_with_filter có cái mà lọc
                    metadata={**metadata, "doc_id": path.stem, "chunk_index": index},
                )
            )
    return documents


def build_embedder():
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    try:
        if provider == "local":
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        if provider == "openai":
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        if provider == "gemini":
            return GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
    except Exception as error:  # noqa: BLE001 - thiếu thư viện/key thì quay về mock
        print(f"Không khởi tạo được embedder '{provider}' ({error}); dùng mock.")
    return _mock_embed


def build_llm():
    """LLM thật nếu có key trong .env; không có thì dùng LLM giả trả về ngữ cảnh top-1."""
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        try:
            from google import genai

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
            model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
            return lambda prompt: client.models.generate_content(model=model, contents=prompt).text, f"gemini:{model}"
        except Exception as error:  # noqa: BLE001
            print(f"Không khởi tạo được Gemini ({error}); dùng LLM giả.")
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI

            client = OpenAI()
            model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

            def openai_llm(prompt: str) -> str:
                response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
                return response.choices[0].message.content

            return openai_llm, f"openai:{model}"
        except Exception as error:  # noqa: BLE001
            print(f"Không khởi tạo được OpenAI ({error}); dùng LLM giả.")

    def extractive_llm(prompt: str) -> str:
        context = prompt.split("NGỮ CẢNH:", 1)[-1].split("CÂU HỎI:", 1)[0].strip()
        first_block = context.split("\n\n[2]", 1)[0]
        return "[LLM giả — trích ngữ cảnh top-1] " + " ".join(first_block.split())[:300]

    return extractive_llm, "extractive-demo"


class FilteredStore:
    """Cho KnowledgeBaseAgent dùng search_with_filter mà không phải sửa agent."""

    def __init__(self, store: EmbeddingStore, metadata_filter: dict | None) -> None:
        self.store = store
        self.metadata_filter = metadata_filter

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        return self.store.search_with_filter(query, top_k=top_k, metadata_filter=self.metadata_filter)


def score_query(results: list[dict], gold_doc: str, key: str) -> tuple[int, bool, bool]:
    """2đ: gold ở top-1 và ngữ cảnh chứa đáp án; 1đ: ngữ cảnh chứa đáp án nhưng gold không ở top-1; 0đ: không."""
    doc_hit = any(r["metadata"]["doc_id"] == gold_doc for r in results)
    content_hit = any(key in r["content"] for r in results)
    if not content_hit:
        return 0, doc_hit, content_hit
    top1_ok = bool(results) and results[0]["metadata"]["doc_id"] == gold_doc and key in results[0]["content"]
    return (2 if top1_ok else 1), doc_hit, content_hit


def print_results(out: Tee, results: list[dict]) -> None:
    for rank, result in enumerate(results, start=1):
        preview = " ".join(result["content"].split())[:140]
        out(f"    {rank}. score={result['score']:.3f}  doc_id={result['metadata']['doc_id']}  ({result['id']})")
        out(f"       {preview}...")


def main() -> int:
    load_dotenv(override=False)
    if not DATA_DIR.is_dir():
        print(f"Không thấy thư mục {DATA_DIR}")
        return 1

    out = Tee(OUTPUT_FILE)
    embedder = build_embedder()
    llm_fn, llm_name = build_llm()
    documents = load_documents(CHUNKER)
    store = EmbeddingStore(collection_name="bench", embedding_fn=embedder)
    store.add_documents(documents)

    lengths = [len(d.content) for d in documents]
    params = {k: v for k, v in vars(CHUNKER).items() if not k.startswith("_")}
    out(f"Chunker          : {CHUNKER.__class__.__name__} {params}")
    out(f"Embedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")
    out(f"LLM              : {llm_name}")
    out(f"Corpus           : {DATA_DIR} — {len(set(d.metadata['doc_id'] for d in documents))} tài liệu, {store.get_collection_size()} chunk, độ dài TB {sum(lengths) / max(len(lengths), 1):.0f} ký tự")

    total = doc_level = content_level = 0
    for number, item in enumerate(QUERIES, start=1):
        out(f"\n=== Q{number}: {item['query']}")
        out(f"    Gold: {item['gold']}  [doc: {item['gold_doc']}, key: '{item['key']}']")
        out(f"    Filter: {item['filter']}")
        results = store.search_with_filter(item["query"], top_k=TOP_K, metadata_filter=item["filter"])
        print_results(out, results)
        points, doc_hit, content_hit = score_query(results, item["gold_doc"], item["key"])
        total += points
        doc_level += doc_hit
        content_level += content_hit
        out(f"    -> gold doc trong top-3: {'CÓ' if doc_hit else 'KHÔNG'} | đáp án trong ngữ cảnh: {'CÓ' if content_hit else 'KHÔNG'} | điểm: {points}/2")

        answer = KnowledgeBaseAgent(store=FilteredStore(store, item["filter"]), llm_fn=llm_fn).answer(item["query"], top_k=TOP_K)
        out(f"    Agent: {' '.join(answer.split())[:400]}")

        if item["filter"]:
            out("\n    --- A/B: cùng câu hỏi, KHÔNG filter ---")
            unfiltered = store.search(item["query"], top_k=TOP_K)
            print_results(out, unfiltered)
            points_nf, doc_nf, content_nf = score_query(unfiltered, item["gold_doc"], item["key"])
            out(f"    -> không filter: gold doc trong top-3: {'CÓ' if doc_nf else 'KHÔNG'} | đáp án trong ngữ cảnh: {'CÓ' if content_nf else 'KHÔNG'} | điểm: {points_nf}/2")
            same = [r["id"] for r in results] == [r["id"] for r in unfiltered]
            out(f"    -> top-3 có filter và không filter {'GIỐNG HỆT (câu hỏi chưa thực sự cần filter)' if same else 'KHÁC NHAU'}")

    out("\n=== TỔNG KẾT")
    out(f"    Chấm theo doc_id (gold doc trong top-3)   : {doc_level}/{len(QUERIES)}")
    out(f"    Chấm theo nội dung (đáp án trong ngữ cảnh): {content_level}/{len(QUERIES)}")
    out(f"    Điểm retrieval (thang 2đ/câu)             : {total}/{2 * len(QUERIES)}")
    if embedder is _mock_embed:
        out("    LƯU Ý: đang dùng MockEmbedder (không có ngữ nghĩa) — số liệu retrieval chỉ là nhiễu.")
    out.close()
    print(f"\nĐã ghi kết quả vào {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
