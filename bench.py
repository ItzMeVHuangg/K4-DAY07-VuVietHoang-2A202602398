"""Benchmark retrieval trên corpus data/hoc-bong — Lab 07 K4-L3A, nhóm Violet.

Cách chạy:
    python bench.py                      # chạy chiến lược ở dòng STRATEGY bên dưới
    python bench.py --strategy heading   # chạy một chiến lược bất kỳ
    python bench.py --strategy all       # chạy cả 4 chiến lược + bảng tổng hợp
    python bench.py --baseline           # bảng baseline ChunkingStrategyComparator (+ heading)

Kết quả:
    ket_qua_benchmark.txt                        # lần chạy chiến lược của mình (deliverable)
    results/ket_qua_benchmark_<chiến lược>.txt   # output đầy đủ từng chiến lược
    results/ket_qua_benchmark_tong_hop.txt       # bảng tổng hợp khi chạy --strategy all

Mỗi thành viên CHỈ đổi dòng `STRATEGY = ...`; mọi thứ khác giữ nguyên để so sánh công bằng.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    ChunkingStrategyComparator,
    FixedSizeChunker,
    HeadingChunker,
    RecursiveChunker,
    SentenceChunker,
)
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

DATA_DIR = Path("data/hoc-bong")
RESULTS_DIR = Path("results")
OUTPUT_FILE = Path("ket_qua_benchmark.txt")
CHUNK_SIZE = 500
TOP_K = 3

# ===== MỖI THÀNH VIÊN CHỈ ĐỔI DÒNG NÀY =====
# "heading" (Nguyễn Văn Quốc Việt) | "recursive" (Nguyễn Phát Thịnh)
# "fixed_size" (Lê Nguyễn Thái Dương) | "by_sentences" (Vũ Việt Hoàng)
STRATEGY = "by_sentences"
# ============================================

STRATEGIES = {
    "fixed_size": lambda: FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=50),
    "by_sentences": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda: RecursiveChunker(chunk_size=CHUNK_SIZE),
    "heading": lambda: HeadingChunker(chunk_size=CHUNK_SIZE),
}

# 5 câu hỏi benchmark chung của nhóm (REPORT_NHOM mục 3).
#   gold_doc : tài liệu chứa đáp án
#   evidence : câu bằng chứng lấy từ đoạn gold — chunk "liên quan" = đúng gold_doc VÀ chứa câu này
#   filter   : metadata_filter; câu có filter được chạy thêm bản không filter để A/B
QUERIES = [
    {
        "id": "Q1",
        "query": "Học bổng khuyến khích học tập ở Viện Cơ khí VIMARU được xét như thế nào?",
        "gold": "Loại Khá 2.50 ≤ ĐTBHB < 3.20 và rèn luyện từ 70; Giỏi 3.20 ≤ ĐTBHB < 3.60 và từ 80; "
        "Xuất sắc ĐTBHB ≥ 3.60 và từ 90 đến 100 (kèm điều kiện vào diện xét).",
        "gold_doc": "vimaru-hbkkht-tieu-chuan-sinh-vien",
        "evidence": "3.20 ≤ ĐTBHB < 3.60",
        "filter": {"audience": "student"},
    },
    {
        "id": "Q2",
        "query": "Học bổng Vallet dành cho học viên sau đại học năm 2026 có bao nhiêu suất và mỗi suất trị giá bao nhiêu?",
        "gold": "42 suất dành cho học viên cao học và nghiên cứu sinh; mỗi suất 34.000.000 VNĐ.",
        "gold_doc": "vallet-hoc-bong-sau-dai-hoc",
        "evidence": "42 suất",
        "filter": None,
    },
    {
        "id": "Q3",
        "query": "Quy trình xét học bổng hỗ trợ đột xuất của UEH gồm những bước nào và mất bao lâu?",
        "gold": "4 bước: tiếp nhận yêu cầu; kiểm tra, yêu cầu bổ sung minh chứng (03–05 ngày làm việc); "
        "trình xin ý kiến Ban Giám đốc (01–03 ngày làm việc); chi trả, cấn trừ học phí (05–10 ngày làm việc).",
        "gold_doc": "ueh-ke-hoach-xet-hoc-bong-2026",
        "evidence": "Trình xin ý kiến Ban Giám đốc",
        "filter": None,
    },
    {
        "id": "Q4",
        "query": "Hồ sơ đăng ký học bổng K-T của ULIS gồm những giấy tờ gì?",
        "gold": "Bản tự giới thiệu; bảng điểm 2024-2025; minh chứng hoàn cảnh khó khăn; bài viết tìm hiểu Quỹ K-T; "
        "bài phát biểu cảm tưởng; bản photo giấy chứng nhận thành tích (nếu có); kèm bản mềm 1 file pdf.",
        "gold_doc": "ulis-hoc-bong-kt-2025-2026",
        "evidence": "Bài phát biểu cảm tưởng",
        "filter": None,
    },
    {
        "id": "Q5",
        "query": "Tân sinh viên HSB muốn được tài trợ 100% học phí có điều kiện thì cần điểm thi bao nhiêu và phải hoàn trả thế nào?",
        "gold": "Điểm tổ hợp THPT từ 24/30 (không môn nào dưới 7) hoặc ĐGNL ĐHQGHN từ 90/150; "
        "trả lại học phí cho Quỹ Học bổng HSB trong vòng 10 năm kể từ khi ra trường.",
        "gold_doc": "hsb-hoc-bong-tan-sinh-vien-2026",
        "evidence": "24/30",
        "filter": None,
    },
]


class Tee:
    """In ra màn hình đồng thời ghi vào một hoặc nhiều file."""

    def __init__(self, *paths: Path) -> None:
        self.files = [path.open("w", encoding="utf-8") for path in paths]

    def __call__(self, text: str = "") -> None:
        print(text)
        for file in self.files:
            file.write(text + "\n")

    def close(self) -> None:
        for file in self.files:
            file.close()


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


def gold_rank(results: list[dict], gold_doc: str) -> int | None:
    return next((rank for rank, r in enumerate(results, start=1) if r["metadata"]["doc_id"] == gold_doc), None)


def score_doc_level(top: list[dict], gold_doc: str) -> int:
    """Chấm theo doc_id (dễ dãi): tài liệu gold ở top-1 = 2đ, ở top-2/3 = 1đ, không có = 0đ."""
    rank = gold_rank(top, gold_doc)
    return 0 if rank is None else (2 if rank == 1 else 1)


def score_content_level(top: list[dict], gold_doc: str, evidence: str) -> int:
    """Chấm theo nội dung: như doc_id NHƯNG top-3 phải có chunk của tài liệu gold chứa câu bằng chứng."""
    relevant = any(r["metadata"]["doc_id"] == gold_doc and evidence in r["content"] for r in top)
    return score_doc_level(top, gold_doc) if relevant else 0


def evidence_rank(ranking: list[dict], gold_doc: str, evidence: str) -> int | None:
    """Hạng của chunk chứa câu bằng chứng trong toàn bộ bảng xếp hạng (để biết trượt xa cỡ nào)."""
    return next(
        (rank for rank, r in enumerate(ranking, start=1) if r["metadata"]["doc_id"] == gold_doc and evidence in r["content"]),
        None,
    )


def print_top(out: Tee, results: list[dict]) -> None:
    for rank, result in enumerate(results, start=1):
        preview = " ".join(result["content"].split())[:140]
        out(f"    {rank}. score={result['score']:.3f}  {result['id']}  [audience={result['metadata'].get('audience')}]")
        out(f"       {preview}...")


def run_query(out: Tee, store: EmbeddingStore, item: dict, metadata_filter: dict | None, label: str) -> tuple[int, int]:
    ranking = store.search_with_filter(item["query"], top_k=store.get_collection_size(), metadata_filter=metadata_filter)
    top = ranking[:TOP_K]
    out(f"\n=== {label}: {item['query']}")
    out(f"    Filter: {metadata_filter}")
    print_top(out, top)
    doc_pts = score_doc_level(top, item["gold_doc"])
    content_pts = score_content_level(top, item["gold_doc"], item["evidence"])
    rank = evidence_rank(ranking, item["gold_doc"], item["evidence"])
    out(f"    -> chấm theo doc_id: {doc_pts}/2 | chấm theo nội dung: {content_pts}/2 | chunk chứa '{item['evidence']}' ở hạng {rank}")
    return doc_pts, content_pts


def run_strategy(name: str, embedder, llm_fn, llm_name: str, output_paths: list[Path]) -> dict:
    chunker = STRATEGIES[name]()
    documents = load_documents(chunker)
    store = EmbeddingStore(collection_name=f"bench-{name}", embedding_fn=embedder)
    store.add_documents(documents)
    lengths = [len(d.content) for d in documents]

    out = Tee(*output_paths)
    out(f"Chiến lược       : {name} ({chunker.__class__.__name__})")
    out(f"Embedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")
    out(f"LLM              : {llm_name}")
    out(f"Corpus           : {DATA_DIR} — {len(set(d.metadata['doc_id'] for d in documents))} tài liệu, "
        f"{store.get_collection_size()} chunk, độ dài TB {sum(lengths) / max(len(lengths), 1):.0f} ký tự, top_k={TOP_K}")

    row = {"strategy": name, "chunks": len(documents), "avg_len": sum(lengths) / max(len(lengths), 1), "cells": {}}
    doc_total = content_total = 0
    for item in QUERIES:
        out(f"\n    Gold ({item['id']}): {item['gold']}  [doc: {item['gold_doc']}]")
        doc_pts, content_pts = run_query(out, store, item, item["filter"], item["id"])
        doc_total += doc_pts
        content_total += content_pts
        row["cells"][item["id"]] = (doc_pts, content_pts)
        answer = KnowledgeBaseAgent(store=FilteredStore(store, item["filter"]), llm_fn=llm_fn).answer(item["query"], top_k=TOP_K)
        out(f"    Agent: {' '.join(answer.split())[:500]}")
        if item["filter"]:
            out(f"\n    --- A/B: {item['id']} KHÔNG filter ---")
            row["cells"][f"{item['id']} không filter"] = run_query(out, store, item, None, f"{item['id']} không filter")
            answer_nf = KnowledgeBaseAgent(store=store, llm_fn=llm_fn).answer(item["query"], top_k=TOP_K)
            out(f"    Agent (không filter): {' '.join(answer_nf.split())[:500]}")

    out("\n=== TỔNG KẾT")
    out(f"    Chấm theo doc_id   : {doc_total}/{2 * len(QUERIES)}")
    out(f"    Chấm theo nội dung : {content_total}/{2 * len(QUERIES)}   <- điểm dùng để chấm")
    if embedder is _mock_embed:
        out("    LƯU Ý: đang dùng MockEmbedder (không có ngữ nghĩa) — số liệu retrieval chỉ là nhiễu.")
    out.close()
    row["doc_total"], row["content_total"] = doc_total, content_total
    return row


def write_summary(rows: list[dict], embedder) -> None:
    columns = [q["id"] for q in QUERIES] + [f"{q['id']} không filter" for q in QUERIES if q["filter"]]
    out = Tee(RESULTS_DIR / "ket_qua_benchmark_tong_hop.txt")
    out(f"Bảng tổng hợp — embedder {getattr(embedder, '_backend_name', embedder.__class__.__name__)}, "
        f"chunk_size={CHUNK_SIZE}, top_k={TOP_K}. Mỗi ô: theo doc_id / theo nội dung.")
    out("| Chiến lược | Số chunk / dài TB | " + " | ".join(columns) + " | Tổng doc_id | Tổng nội dung |")
    out("|" + "---|" * (len(columns) + 4))
    for row in rows:
        cells = " | ".join(f"{row['cells'][c][0]}/{row['cells'][c][1]}" for c in columns)
        out(f"| {row['strategy']} | {row['chunks']} / {row['avg_len']:.0f} | {cells} | "
            f"{row['doc_total']}/{2 * len(QUERIES)} | {row['content_total']}/{2 * len(QUERIES)} |")
    out.close()


def run_baseline() -> None:
    """Bảng baseline: ChunkingStrategyComparator (chunk_size=500) + dòng heading để so sánh."""
    documents = ["hsb-hoc-bong-tan-sinh-vien-2026", "ueh-ke-hoach-xet-hoc-bong-2026", "vimaru-hbkkht-tieu-chuan-sinh-vien"]
    print("| Tài liệu | Chiến lược | Số chunk | Độ dài TB (min–max) |")
    print("|---|---|---|---|")
    for doc_id in documents:
        _, body = parse_markdown(DATA_DIR / f"{doc_id}.md")
        results = ChunkingStrategyComparator().compare(body, chunk_size=CHUNK_SIZE)
        results["heading"] = {"chunks": HeadingChunker(chunk_size=CHUNK_SIZE).chunk(body)}
        for strategy, stats in results.items():
            lengths = [len(c) for c in stats["chunks"]]
            print(f"| `{doc_id}` | {strategy} | {len(lengths)} | {sum(lengths) / len(lengths):.1f} ({min(lengths)}–{max(lengths)}) |")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark retrieval trên corpus học bổng.")
    parser.add_argument("--strategy", choices=[*STRATEGIES, "all"], default=STRATEGY)
    parser.add_argument("--baseline", action="store_true", help="In bảng baseline rồi thoát")
    args = parser.parse_args()

    if not DATA_DIR.is_dir():
        print(f"Không thấy thư mục {DATA_DIR}")
        return 1
    if args.baseline:
        run_baseline()
        return 0

    load_dotenv(override=False)
    RESULTS_DIR.mkdir(exist_ok=True)
    embedder = build_embedder()
    llm_fn, llm_name = build_llm()

    names = list(STRATEGIES) if args.strategy == "all" else [args.strategy]
    rows = []
    for name in names:
        outputs = [RESULTS_DIR / f"ket_qua_benchmark_{name}.txt"]
        if name == STRATEGY:
            outputs.append(OUTPUT_FILE)  # chiến lược của mình -> deliverable ket_qua_benchmark.txt
        rows.append(run_strategy(name, embedder, llm_fn, llm_name, outputs))
        print()
    if len(rows) > 1:
        write_summary(rows, embedder)
    print(f"Đã ghi kết quả vào {RESULTS_DIR}/" + (f" và {OUTPUT_FILE}" if STRATEGY in names else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
