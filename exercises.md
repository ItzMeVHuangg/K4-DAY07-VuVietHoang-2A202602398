# Ngày 7 — Bài tập
## Nền tảng Dữ liệu: Embedding & Vector Store | Bài tập thực hành

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity (Độ tương tự Cosine) bằng ngôn ngữ đời thường

Không yêu cầu toán học — hãy giải thích về mặt khái niệm:

- Điều gì xảy ra khi hai đoạn văn bản có độ tương tự cosine cao?
- Đưa ra một ví dụ cụ thể về hai câu sẽ có độ tương tự CAO và hai câu sẽ có độ tương tự THẤP.
- Tại sao độ tương tự cosine lại được ưu tiên hơn khoảng cách Euclid (Euclidean distance) đối với text embeddings?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)

**Trả lời:**

- **Cosine cao nghĩa là gì:** hai vector embedding gần như cùng hướng trong không gian ngữ nghĩa, tức hai đoạn văn nói về cùng một ý — kể cả khi dùng từ ngữ khác nhau. Giá trị gần 1 là rất giống nghĩa, gần 0 là không liên quan.
- **Ví dụ CAO:** "Hạn nộp hồ sơ học bổng là ngày 30/06/2026." và "Hồ sơ xin học bổng phải gửi trước cuối tháng 6 năm 2026." — cùng một thời hạn dù gần như không chung từ vựng. Đo thực tế: **0.805**.
- **Ví dụ THẤP:** "Điểm trung bình từ 3.20 trở lên." và "Chó mèo là vật nuôi phổ biến." — hai chủ đề không liên quan. Đo thực tế: **0.016**.
- **Vì sao cosine hợp hơn Euclid:** cosine chỉ đo góc giữa hai vector, không phụ thuộc độ dài, nên một đoạn dài và một câu ngắn cùng ý vẫn được đánh giá là giống nhau; khoảng cách Euclid bị ảnh hưởng bởi độ lớn vector. Với vector đã chuẩn hoá (‖v‖ = 1), cosine chính là tích vô hướng nên tính rất rẻ.

(Đo bằng embedder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.)

---

### Bài tập 1.2 — Bài toán tính toán Chunking

- Một tài liệu có độ dài 10,000 ký tự. Bạn tiến hành chia nhỏ (chunk) với `chunk_size=500` (kích thước chunk), `overlap=50` (độ chồng chéo). Bạn dự kiến sẽ có bao nhiêu chunks?
- Công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
- Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk sẽ thay đổi như thế nào? Tại sao bạn lại muốn tăng độ chồng chéo?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)

**Trả lời:**

- `overlap=50`: ⌈(10000 − 50) / (500 − 50)⌉ = ⌈9950 / 450⌉ = ⌈22.11⌉ = **23 chunks**.
- `overlap=100`: ⌈(10000 − 100) / (500 − 100)⌉ = ⌈9900 / 400⌉ = ⌈24.75⌉ = **25 chunks** — tăng thêm 2 chunk vì mỗi bước trượt ngắn hơn.
- Kiểm chứng bằng `FixedSizeChunker` có sẵn trong repo:

  ```bash
  python -c "from src.chunking import FixedSizeChunker as F; print(len(F(500,50).chunk('a'*10000)), len(F(500,100).chunk('a'*10000)))"
  # 23 25
  ```

- **Vì sao muốn overlap lớn hơn:** một câu/ý nằm ở biên giữa hai chunk vẫn xuất hiện trọn vẹn trong ít nhất một chunk, nên thông tin có nhiều hơn một cơ hội lọt vào top-k khi truy xuất. Đổi lại tốn thêm chunk, thêm embedding và dữ liệu trùng lặp trong ngữ cảnh.

---

## Phần 2 — Lập trình cốt lõi (Cá nhân)

Hoàn thành tất cả các TODOs trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. `Document` dataclass và `FixedSizeChunker` đã được triển khai sẵn làm ví dụ — hãy đọc kỹ để hiểu cấu trúc trước khi lập trình phần còn lại.

Chạy `pytest tests/` để kiểm tra tiến độ.

### Danh sách cần làm (Checklist)
- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [x] `SentenceChunker` — tách dựa trên ranh giới câu, nhóm lại thành các chunks
- [x] `RecursiveChunker` — thử nghiệm các dấu phân cách (separators) theo thứ tự, thực hiện đệ quy trên các đoạn có kích thước quá lớn
- [x] `compute_similarity` — công thức tính độ tương tự cosine kèm cơ chế bảo vệ chia cho 0
- [x] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính toán các chỉ số thống kê
- [x] `EmbeddingStore.__init__` — khởi tạo store (lưu trữ trong bộ nhớ hoặc ChromaDB)
- [x] `EmbeddingStore.add_documents` — nhúng (embed) và lưu trữ từng tài liệu
- [x] `EmbeddingStore.search` — nhúng truy vấn, xếp hạng theo tích vô hướng (dot product)
- [x] `EmbeddingStore.get_collection_size` — trả về số lượng
- [x] `EmbeddingStore.search_with_filter` — lọc theo siêu dữ liệu (metadata), sau đó tìm kiếm
- [x] `EmbeddingStore.delete_document` — xóa tất cả các chunks của một doc_id
- [x] `KnowledgeBaseAgent.answer` — truy xuất (retrieve) + tạo prompt + gọi LLM

> **Nộp code:** thư mục `src/`
> **Ghi lại hướng tiếp cận vào:** Báo cáo — Phần 4 (Hướng tiếp cận của tôi)

**Kết quả:** `pytest tests/ -v` → **42 passed**; `src/` không còn `NotImplementedError`/`TODO`.

**Hướng tiếp cận (tóm tắt — chi tiết trong `report/REPORT_CANHAN.md` mục 2):**

| Thành phần | Cách làm |
|---|---|
| `SentenceChunker` | Regex lookbehind `(?<=[.!?])\s+` — cắt **sau** dấu câu nên dấu câu không bị mất; gom `max_sentences_per_chunk` câu/chunk; text rỗng → `[]`. Chưa xử lý: viết tắt (`TS.`, `v.v.`), số thập phân. |
| `RecursiveChunker` | Thử separator `["\n\n", "\n", ". ", " ", ""]`; **đệ quy xuống** với mảnh quá dài, **gom lên** các mảnh nhỏ liền kề tới sát `chunk_size`. Ba base case: đã đủ nhỏ, hết separator (`[]`), separator rỗng → cắt cứng. |
| `compute_similarity` | `dot(a, b) / (‖a‖·‖b‖)`, dùng lại `_dot`; vector độ dài 0 → `0.0`. |
| `ChunkingStrategyComparator` | Chạy 3 chunker trên cùng text, trả `fixed_size` / `by_sentences` / `recursive`, mỗi key có `count`, `avg_length`, `chunks`; chặn chia 0 khi text rỗng. |
| `EmbeddingStore` | In-memory, `_use_chroma = False`. `_make_record` copy metadata và bảo đảm có `doc_id`; `_search_records` dùng chung cho `search` và `search_with_filter`, score = dot product (vector đã chuẩn hoá), bỏ `embedding` khỏi kết quả; `search_with_filter` **lọc trước rồi mới search**; `delete_document` xoá mọi record cùng `doc_id`. |
| `KnowledgeBaseAgent.answer` | Top-k → ngữ cảnh đánh số `[1] [2] [3]` kèm nguồn → prompt yêu cầu chỉ dùng ngữ cảnh, trích dẫn `[n]`, không có thì nói không tìm thấy; store rỗng thì không gọi LLM. |

---

## Phần 3 — So Sánh Chiến Lược Truy Xuất (Nhóm)

### Bài tập 3.0 — Chuẩn Bị Tài Liệu (Giờ đầu tiên)

Mỗi nhóm chọn một chủ đề (domain) và chuẩn bị bộ tài liệu:

**Bước 1 — Chọn chủ đề:** FAQ (Câu hỏi thường gặp), SOP (Quy trình chuẩn), chính sách, tài liệu kỹ thuật, công thức nấu ăn, luật, y tế, v.v.

**Bước 2 — Thu thập 5-10 tài liệu.** Chỉ dùng nguồn công khai hoặc nguồn nhóm có quyền sử dụng; lưu dưới dạng `.txt` hoặc `.md` vào thư mục `data/`.

**Quy tắc dữ liệu bắt buộc:**
- Không đưa dữ liệu cá nhân, thông tin đăng nhập, hồ sơ nội bộ hoặc nội dung có quyền sử dụng không rõ ràng vào repo.
- Với mỗi tài liệu, ghi `source_url`, `retrieved_at` (ngày lấy) và `document_version` hoặc ngày hiệu lực nếu nguồn có nêu.
- Đưa ba trường trên vào siêu dữ liệu (metadata) khi nạp (ingest); chúng giúp kiểm tra độ mới và truy vết câu trả lời.

> **Mẹo chuyển PDF sang Markdown:**
> - `pip install marker-pdf` → `marker_single input.pdf output/` (chất lượng cao, giữ cấu trúc)
> - `pip install pymupdf4llm` → `pymupdf4llm.to_markdown("input.pdf")` (nhanh, đơn giản)
> - Hoặc sao chép-dán (copy-paste) nội dung từ PDF/web vào file `.txt`

**Chủ đề nhóm chọn:** Học bổng đại học (mảng "dịch vụ/quy định đại học" của L3A). Bộ tài liệu: `data/university/` — 9 file `.md` + `sources.csv`.

Ghi vào bảng:

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | FTU - Học bổng Công ty TNHH TOTO Việt Nam 2026 | https://qldt.ftu.edu.vn/thong-bao-xet-chon-hoc-bong-cong-ty-tnhh-toto-viet-nam-nam-2026/ | 2026-09-19 / đăng 2026-08-18 | 5,209 | audience=student, student_level=undergraduate, institution=ftu, category=scholarship |
| 2 | HSB - Học bổng cho các chương trình đại học 2026 | https://www.hsb.edu.vn/news/undergraduate-incoming-scholarship-2026 | 2026-09-19 / đăng 2026-03-03 | 9,292 | audience=student, student_level=prospective, institution=hsb, category=scholarship |
| 3 | NEU - Học bổng Vững tương lai năm học 2025-2026 | https://mis.neu.edu.vn/vi/tin-tuc-khoa-htttql/trien-khai-va-thu-ho-so-hoc-bong-vung-tuong-lai-nam-hoc-2025-2026 | 2026-09-19 / đăng 2026-08-13 | 2,148 | audience=student, student_level=undergraduate, institution=neu, category=scholarship |
| 4 | UEH - Kế hoạch triển khai công tác xét học bổng năm 2026 | https://dsa.ueh.edu.vn/tin-tuc/kh-xet-hb-ueh-2026/ | 2026-09-19 / đăng 2026-02-23 | 6,405 | audience=student, student_level=undergraduate, institution=ueh, category=scholarship |
| 5 | ULIS - Chương trình học bổng K-T năm học 2025-2026 | https://student.ulis.vnu.edu.vn/thong-bao-chuong-trinh-hoc-bong-k-t-nam-hoc-2025-2026/ | 2026-09-19 / not-stated | 2,746 | audience=student, student_level=undergraduate, institution=ulis, category=scholarship |
| 6 | Học bổng Vallet khối sau đại học miền Bắc 2026 | https://rvn-vallet.org/hoc-bong-khoi-sau-dai-hoc/ | 2026-09-19 / 02-2026/TB-HBSĐHMB (26/05/2026) | 8,661 | audience=student, student_level=graduate, institution=vallet, category=scholarship |
| 7 | VIMARU - Quy trình xét duyệt HBKKHT (dành cho cán bộ) | https://sme.vimaru.edu.vn/ctsv/quy-trinh-cap-hoc-bong-khuyen-khich-hoc-tap-cho-sinh-vien | 2026-09-19 / not-stated | 4,083 | audience=staff, institution=vimaru, category=scholarship |
| 8 | VIMARU - Tiêu chuẩn xét HBKKHT cho sinh viên | https://sme.vimaru.edu.vn/ctsv/quy-trinh-cap-hoc-bong-khuyen-khich-hoc-tap-cho-sinh-vien | 2026-09-19 / not-stated | 3,094 | audience=student, student_level=undergraduate, institution=vimaru, category=scholarship |
| 9 | VTTU - Học bổng Học giả Fulbright Việt Nam và Học giả Hoa Kỳ - ASEAN 2025-2026 | https://vttu.edu.vn/thong-bao-ve-chuong-trinh-hoc-bong-hoc-gia-fulbright-viet-nam-va-hoc-gia-hoa-ky-asean-nam-hoc-2025-2026/ | 2026-09-19 / not-stated | 3,319 | audience=faculty, institution=vttu, category=scholarship |

Tài liệu 7 và 8 lấy từ cùng một trang nhưng tách theo đối tượng (tiêu chuẩn cho sinh viên / các bước xét duyệt cho cán bộ) để `metadata_filter={"audience": "student"}` có việc thật để lọc.

**Bước 3 — Thiết kế cấu trúc metadata (metadata schema):** Mỗi tài liệu cần `source_url`, `retrieved_at`, `document_version` và ít nhất 2 trường hữu ích cho việc truy xuất (ví dụ: `audience`, `department`, `category`, `language`, `difficulty`).

**Metadata schema của nhóm:**

| Trường | Ví dụ | Dùng để |
|---|---|---|
| `doc_id`, `title` | `ueh-ke-hoach-xet-hoc-bong-2026` | Định danh, trùng tên file; `delete_document` và chấm benchmark dựa vào `doc_id` |
| `source_url`, `retrieved_at`, `document_version`, `published_at` | `2026-09-19`, `02-2026/TB-HBSĐHMB` | Truy vết nguồn và kiểm tra độ mới; không có phiên bản thì ghi `not-stated` |
| `audience` | `student` / `faculty` / `staff` | Loại tài liệu dành cho đối tượng khác (dùng trong câu Q5) |
| `student_level` | `undergraduate` / `graduate` / `prospective` | Tách học bổng sau đại học, tân sinh viên khỏi học bổng cho sinh viên đang học |
| `institution` | `ftu`, `ueh`, `vimaru` | Corpus nhiều trường dùng chung từ vựng "học bổng" — lọc theo trường |
| `department`, `category`, `language` | `ueh-student-affairs`, `scholarship`, `vi` | Đơn vị ban hành, mảng nội dung, ngôn ngữ |

> **Ghi kết quả vào:** Báo cáo — Phần 2 (Lựa chọn tài liệu)

---

### Bài tập 3.1 — Thiết Kế Chiến Lược Truy Xuất (Mỗi người thử riêng)

Mỗi thành viên **tự chọn chiến lược riêng** để thử nghiệm trên cùng bộ tài liệu của nhóm.

**Bước 1 — Đường cơ sở (Baseline):** Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu. Ghi lại kết quả.

**Kết quả baseline** (`compare(body, chunk_size=500)`, đã bỏ frontmatter):

| Tài liệu | `fixed_size` (count / avg) | `by_sentences` (count / avg) | `recursive` (count / avg) |
|---|---|---|---|
| vallet-hoc-bong-sau-dai-hoc | 15 / 493 | 25 / 266 | 21 / 317 |
| ueh-ke-hoach-xet-hoc-bong-2026 | 12 / 465 | 10 / 501 | 16 / 313 |
| vimaru-hbkkht-tieu-chuan-sinh-vien | 6 / 439 | 4 / 593 | 7 / 339 |

Nhận xét: `fixed_size` cắt ngang câu và ngang bảng; `by_sentences` gộp các dòng bảng không có dấu chấm câu thành chunk dài (UEH, VIMARU); `recursive` cắt theo đoạn/dòng nên giữ bảng và danh sách trọn vẹn nhất.

**Bước 2 — Chọn hoặc thiết kế chiến lược của bạn:**
- Dùng 1 trong 3 chiến lược có sẵn (built-in strategies) với tham số tối ưu, HOẶC
- Thiết kế chiến lược tùy chỉnh cho chủ đề của bạn (ví dụ: chia nhỏ theo cặp Câu hỏi-Đáp án, theo các phần (sections), theo tiêu đề (headers))
- Mỗi thành viên nên thử một chiến lược **khác nhau** để có cơ sở so sánh

**Chiến lược của tôi — chunk theo tiêu đề, gắn tiêu đề tài liệu** (code đầy đủ trong `bench.py`, cấu hình chốt `HeadingChunker(max_chunk_size=250, prepend_title=True)`):

```python
class HeadingChunker:
    """Chiến lược chia nhỏ tùy chỉnh cho thông báo/quy định học bổng.

    Lý do thiết kế: thông báo học bổng được viết theo mục (Đối tượng, Giá trị, Hồ sơ,
    Thời hạn) — mỗi mục là một đơn vị ngữ nghĩa trọn vẹn nên tách tại mỗi heading.
    Mục dài quá ngưỡng thì hạ xuống RecursiveChunker và gắn lại heading vào từng mảnh con.
    prepend_title=True gắn tiêu đề tài liệu vào đầu mọi chunk, vì section như
    "## 2. Giá trị học bổng" không tự nói nó thuộc học bổng/trường nào.
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
        chunks, pending_heading = [], ""
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if pending_heading:
                section = f"{pending_heading}\n{section}"
                pending_heading = ""
            if section.startswith("#") and "\n" not in section:
                pending_heading = section  # heading cha rỗng -> gộp vào section con
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
```

**Bước 3 — So sánh:** So sánh chiến lược tùy chỉnh/được tinh chỉnh (custom/tuned strategy) với đường cơ sở (baseline) trên cùng tài liệu.

**Kết quả so sánh** (cùng `bench.py`, 5 câu hỏi, embedder `paraphrase-multilingual-MiniLM-L12-v2`, top-3):

| Chiến lược | Số chunk | Đúng tài liệu (top-3) | Ngữ cảnh chứa đáp án | Điểm /10 |
|---|---|---|---|---|
| FixedSize(500, overlap=100) — baseline | 89 | 4/5 | 0/5 | 0 |
| Sentence(3) — baseline | 90 | 4/5 | 1/5 | 1 |
| Recursive(500) — baseline | 109 | 4/5 | 0/5 | 0 |
| Heading(800), không gắn tiêu đề | 80 | 4/5 | 1/5 | 1 |
| Heading(800) + tiêu đề | 80 | 4/5 | 1/5 | 2 |
| **Heading(250) + tiêu đề — chốt** | **202** | **5/5** | **1/5** | **2** |

Gắn tiêu đề tài liệu là thay đổi có tác dụng nhất (Heading 1 → 2/10; thử gắn vào `Recursive(500)` cũng 0 → 2/10). Ngưỡng 250 ký tự được chọn vì model chỉ đọc 128 token: với ngưỡng 800 + tiêu đề, 45/80 chunk bị cắt khi embed; với 250 chỉ còn 1/202 và tìm đúng tài liệu 5/5.

> **Ghi kết quả vào:** Báo cáo — Phần 3 (Chiến lược chia nhỏ - Chunking Strategy)

---

### Bài tập 3.2 — Chuẩn Bị Câu Hỏi Đánh Giá (Benchmark Queries)

Mỗi nhóm viết **đúng 5 câu hỏi đánh giá** kèm theo **câu trả lời chuẩn (gold answers)**.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học bổng Vallet sau đại học năm 2026 có bao nhiêu suất và mỗi suất trị giá bao nhiêu? | 42 suất, mỗi suất 34.000.000 VNĐ | `vallet-hoc-bong-sau-dai-hoc` — mục "2. Giá trị và số lượng học bổng" |
| 2 | Học bổng Vững tương lai loại A trị giá bao nhiêu và dành cho ai? | 130 suất, 20.000.000 VNĐ/suất; HSSV đạt chuẩn loại B và có thành tích xuất sắc, tiêu biểu / thủ khoa đầu vào / hoàn cảnh đặc biệt khó khăn | `neu-hoc-bong-vung-tuong-lai-2025-2026` — mục "Hạng mục và giá trị học bổng (810 suất)" |
| 3 | Điều kiện điểm học tập để xét học bổng TOTO ở Đại học Ngoại thương là gì? | Điểm TBC năm học 2025-2026 từ 7.0/10 hoặc 2.8/4 trở lên; tích lũy tối thiểu 28 tín chỉ/năm học | `ftu-hoc-bong-toto-2026` — mục "Tiêu chí" |
| 4 | Khi nào UEH ra quyết định cấp học bổng khuyến khích học tập học kỳ đầu năm 2026? | 18/5/2026 (học kỳ cuối năm 2026: 10/11/2026) | `ueh-ke-hoach-xet-hoc-bong-2026` — bảng "1.2. Các mốc thời gian thực hiện" |
| 5 | Học bổng khuyến khích học tập ở VIMARU được xét như thế nào? *(cần `metadata_filter={"audience": "student"}`)* | Loại Khá: 2.50 ≤ ĐTBHB < 3.20, rèn luyện từ 70; Giỏi: 3.20 ≤ ĐTBHB < 3.60, từ 80; Xuất sắc: ĐTBHB ≥ 3.60, từ 90 đến 100 | `vimaru-hbkkht-tieu-chuan-sinh-vien` — mục "Tiêu chuẩn cụ thể cho các mức học bổng" |

**Yêu cầu:**
- Câu hỏi phải đa dạng (không hỏi 5 câu có nội dung/cấu trúc giống hệt nhau)
- Câu trả lời chuẩn phải cụ thể và có thể kiểm chứng (verify) từ tài liệu
- Ít nhất 1 câu hỏi yêu cầu lọc bằng metadata (metadata filtering) để trả lời tốt

**Đối chiếu yêu cầu:** 5 dạng hỏi khác nhau (tra số liệu, giá trị + đối tượng, điều kiện, mốc thời gian, quy trình không nêu người hỏi); mọi gold answer trích nguyên văn từ tài liệu trong `data/university/`; Q5 cần filter vì cùng một trang VIMARU có hai tài liệu cùng chủ đề nhưng khác đối tượng (sinh viên / cán bộ).

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả — Câu hỏi đánh giá & Câu trả lời chuẩn)

---

### Bài tập 3.3 — Dự Đoán Độ Tương Tự Cosine (Cá nhân)

Gọi hàm `compute_similarity()` trên 5 cặp câu. **Trước khi chạy**, hãy dự đoán xem cặp câu nào sẽ có độ tương tự cao nhất/thấp nhất. Ghi lại các dự đoán của bạn và kết quả thực tế. Suy ngẫm xem điều gì khiến bạn ngạc nhiên nhất.

**Kết quả** (embedder `paraphrase-multilingual-MiniLM-L12-v2`):

| Cặp | Câu A | Câu B | Dự đoán | Thực tế | Đúng? |
|---|---|---|---|---|---|
| 1 | Sinh viên được nhận học bổng khuyến khích học tập. | Người học đạt thành tích tốt sẽ được cấp tiền thưởng học tập. | cao | 0.733 | Đúng |
| 2 | Hạn nộp hồ sơ học bổng là ngày 30/06/2026. | Hồ sơ xin học bổng phải gửi trước cuối tháng 6 năm 2026. | cao (cao nhất) | 0.805 | Đúng |
| 3 | Mỗi suất học bổng trị giá 5 triệu đồng. | Thư viện mở cửa từ 7 giờ sáng. | thấp | 0.167 | Đúng |
| 4 | Học bổng dành cho sinh viên có hoàn cảnh khó khăn. | Học bổng không dành cho sinh viên có hoàn cảnh khó khăn. | thấp | 0.773 | **Sai** |
| 5 | Điểm trung bình từ 3.20 trở lên. | Chó mèo là vật nuôi phổ biến. | thấp (thấp nhất) | 0.016 | Đúng |

**Điều ngạc nhiên nhất:** cặp 4 — hai câu nghĩa **ngược nhau** chỉ vì thêm chữ "không" nhưng vẫn đạt 0.773, cao hơn cả cặp 1 vốn đồng nghĩa. Embedding mã hoá chủ yếu **chủ đề và từ vựng chung**, không nắm được phủ định; vì vậy retrieval chỉ tìm được đoạn "cùng chủ đề", còn việc đoạn đó khẳng định hay phủ định điều kiện phải để LLM đọc kỹ ngữ cảnh.

> **Ghi kết quả vào:** Báo cáo — Phần 5 (Dự đoán độ tương tự)

---

### Bài tập 3.4 — Chạy Đánh Giá & So Sánh Trong Nhóm

**Bước 1:** Mỗi thành viên chạy 5 câu hỏi đánh giá với chiến lược riêng. Ghi lại kết quả top-3 cho mỗi câu hỏi.

**Kết quả top-3 của tôi** — `HeadingChunker(250, prepend_title=True)`, 202 chunk (đầy đủ trong `ket_qua_benchmark.txt`):

| # | Top-1 (score) | Top-2 | Top-3 | Đúng tài liệu? | Ngữ cảnh chứa đáp án? | Điểm |
|---|---|---|---|---|---|---|
| 1 | vallet #9 "Giá trị và số lượng học bổng" (0.861) | vallet #14 (0.853) | vallet #3 (0.849) | Có | Có | 2/2 |
| 2 | neu #5 "590 suất học bổng thường niên…" (0.838) | hsb #3 (0.814) | hsb #12 (0.798) | Có | Không | 0/2 |
| 3 | ftu #4 "Đối tượng" (0.694) | hsb #15 (0.662) | hsb #12 (0.655) | Có | Không | 0/2 |
| 4 | ueh #1 đoạn mở đầu kế hoạch (0.811) | ueh #19 (0.800) | ueh #17 (0.777) | Có | Không | 0/2 |
| 5 (filter `student`) | vimaru-sinh-vien #0 đoạn mở đầu (0.739) | hsb #12 (0.685) | vimaru-sinh-vien #4 (0.678) | Có | Không | 0/2 |

**Tổng:** đúng tài liệu 5/5 · ngữ cảnh chứa đáp án 1/5 · điểm retrieval **2/10**.

**Bước 2:** So sánh kết quả trong nhóm:
- Chiến lược nào cho việc truy xuất tốt nhất? Tại sao?
- Có câu hỏi nào mà chiến lược A tốt hơn B nhưng lại ngược lại ở câu hỏi khác không?
- Lọc bằng metadata (Metadata filtering) có giúp ích không?

**Trả lời:**
- **Tốt nhất:** chunk theo heading **kèm tiêu đề tài liệu** (2/10, đúng tài liệu 5/5). Yếu tố quyết định là gắn tiêu đề chứ không phải cách cắt: corpus nhiều trường dùng chung từ vựng "học bổng", và các section như "Giá trị học bổng" không tự nói mình thuộc trường/quỹ nào.
- **Có đảo chiều giữa các câu:** Heading + tiêu đề thắng Q1 (2/2) nhưng thua Q3; `Sentence(3)` là cấu hình duy nhất lấy được tiêu chí TOTO (Q3, 1/2); `Recursive(500)` + tiêu đề là cấu hình duy nhất lấy được ngày của UEH (Q4, 2/2). Không chiến lược nào thắng tuyệt đối.
- **Filter có giúp:** ở Q5, không filter thì top-1 là tài liệu **dành cho cán bộ** (`vimaru-hbkkht-quy-trinh-xet-duyet`, 0.739 — bằng đúng điểm tài liệu sinh viên); có `audience=student` thì tài liệu cán bộ bị loại, top-1 về đúng tài liệu sinh viên. Filter sửa được lỗi **sai đối tượng**, nhưng không sửa được việc chọn sai chunk bên trong tài liệu đúng.

**Bước 3:** Thảo luận và rút ra bài học — chuẩn bị cho phần demo (thuyết trình) với các nhóm khác.

**Bài học chính cho demo:**
1. Chấm theo `doc_id` thổi phồng kết quả: 5/5 đúng tài liệu nhưng chỉ 1/5 thực sự có đáp án trong ngữ cảnh.
2. Chunk phải tự mang ngữ cảnh — gắn tiêu đề tài liệu là cải tiến rẻ nhất và hiệu quả nhất.
3. Độ dài chunk phải chọn theo cửa sổ của embedder (128 token), không chỉ theo cấu trúc văn bản.

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả)
> **Gợi ý đánh giá:** xem danh sách kiểm tra ngắn trong `README.md` mục **Cách Tự Đánh Giá Kết Quả Retrieval** hoặc chi tiết hơn trong file `docs/EVALUATION.md`.

---

### Bài tập 3.5 — Phân Tích Lỗi (Failure Analysis)

Tìm ít nhất **1 trường hợp lỗi (failure case)** trong quá trình so sánh. Mô tả:
- Câu hỏi nào mà quá trình truy xuất gặp thất bại?
- Tại sao? (do chunk quá nhỏ/quá lớn, thiếu metadata, câu hỏi mơ hồ, v.v.)
- Đề xuất cải thiện?

**Failure case 1 — Q2 (học bổng Vững tương lai loại A) lấy nhầm tài liệu của trường khác**
- **Câu hỏi thất bại:** Q2. Với `HeadingChunker(800)` không gắn tiêu đề, top-1 là section "## 2. Giá trị và số lượng học bổng" của **Vallet** (score 0.780) thay vì tài liệu NEU.
- **Tại sao:** section đó không nhắc tên học bổng — nó chỉ có "Số lượng… Giá trị mỗi suất… VNĐ", rất giống câu hỏi "trị giá bao nhiêu". Chunk thiếu ngữ cảnh tài liệu nên embedding không phân biệt được học bổng của trường nào (*precision* thấp, *chunk coherence* ở mức tài liệu bị mất).
- **Cải thiện:** gắn tiêu đề tài liệu vào đầu mọi chunk → Q2 quay về đúng tài liệu NEU. Thêm filter `institution` khi câu hỏi nêu tên trường cũng loại được lỗi này. Tuy vậy Q2 vẫn 0/2 vì mảnh chứa "Loại A - 130 suất, 20.000.000" bị tách khỏi mảnh "590 suất thường niên" — cần overlap hoặc giữ cả danh sách hạng mục trong một chunk.

**Failure case 2 — Q4, Q5: đúng tài liệu nhưng đáp án nằm trong bảng**
- **Câu hỏi thất bại:** Q4 (ngày 18/5/2026 của UEH) và Q5 (bảng mức điểm VIMARU): top-1 là **đoạn mở đầu** của đúng tài liệu, không phải chunk chứa đáp án.
- **Tại sao:** đoạn mở đầu chứa tên trường + tên học bổng nên trùng nhiều từ với câu hỏi; chunk đáp án là dòng bảng toàn con số/ngày tháng, ít từ vựng chung — cosine đo độ giống chủ đề, không đo mật độ thông tin trả lời được. Thêm vào đó, model chỉ đọc 128 token: ở cấu hình `Heading(800)` + tiêu đề, 45/80 chunk bị cắt, phần cuối (thường là con số) không được mã hoá.
- **Cải thiện:** khi làm sạch dữ liệu, viết lại bảng thành câu văn đầy đủ ("Quyết định cấp học bổng KKHT học kỳ đầu năm 2026 của UEH: 18/5/2026"); giữ chunk dưới cửa sổ 128 token; dùng embedder mạnh hơn / cửa sổ dài hơn, hoặc lấy top-k lớn hơn rồi rerank.

> **Ghi kết quả vào:** Báo cáo — Phần 7 (Những gì tôi học được)
> **Gợi ý:** phân tích lỗi nên tham chiếu từ các góc nhìn như độ chính xác (precision), tính mạch lạc của chunk (chunk coherence), tính hữu dụng của metadata, và chất lượng thông tin nền (grounding quality).

---

## Danh Sách Kiểm Tra Nộp Bài (Submission Checklist)

- [x] Vượt qua tất cả các bài kiểm thử (tests): `pytest tests/ -v` — 42 passed
- [x] Cập nhật thư mục `src/` (cá nhân)
- [ ] Hoàn thành báo cáo nhóm (`report/REPORT_NHOM.md` — 1 file/nhóm) — còn tên nhóm/thành viên, mô tả chiến lược của thành viên 2–3 và điểm demo
- [ ] Hoàn thành báo cáo cá nhân (`report/REPORT_CANHAN.md` — 1 file/sinh viên) — còn mục "Điều hay nhất học được" (điền sau buổi demo)
