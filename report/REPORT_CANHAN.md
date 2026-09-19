# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Việt Hoàng
**Nhóm:** [Violet]
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding gần như cùng hướng trong không gian ngữ nghĩa, tức là hai đoạn văn nói về cùng một ý, kể cả khi dùng từ ngữ khác nhau. Giá trị gần 1 là rất giống nghĩa, gần 0 là không liên quan.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Hạn nộp hồ sơ học bổng là ngày 30/06/2026."
- Câu B: "Hồ sơ xin học bổng phải gửi trước cuối tháng 6 năm 2026."
- Tại sao tương đồng: cùng nói về một thời hạn nộp hồ sơ, dù hai câu gần như không chung từ vựng ("hạn nộp" ↔ "phải gửi trước", "30/06" ↔ "cuối tháng 6"). Điểm thực tế đo được: **0.805**.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Điểm trung bình từ 3.20 trở lên."
- Câu B: "Chó mèo là vật nuôi phổ biến."
- Tại sao khác: hai chủ đề hoàn toàn không liên quan (điều kiện học tập và vật nuôi). Điểm thực tế đo được: **0.016**.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo góc giữa hai vector, không phụ thuộc độ dài vector, nên một đoạn văn dài và một câu ngắn cùng ý vẫn được đánh giá là giống nhau. Khoảng cách Euclid bị ảnh hưởng bởi độ lớn vector nên dễ đánh giá sai; với vector đã chuẩn hoá (‖v‖ = 1) thì cosine chính là tích vô hướng, tính rất rẻ.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* số chunk = ⌈(10000 − 50) / (500 − 50)⌉ = ⌈9950 / 450⌉ = ⌈22.11⌉
> *Đáp án:* **23 chunks** (đã kiểm lại bằng `FixedSizeChunker(500, 50).chunk('a'*10000)` → 23).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng lên ⌈9900 / 400⌉ = **25** (kiểm lại bằng code cũng ra 25), vì mỗi bước trượt ngắn hơn. Overlap lớn hơn giúp một câu/ý nằm ở biên giữa hai chunk vẫn xuất hiện trọn vẹn trong ít nhất một chunk, nên thông tin có nhiều hơn một cơ hội lọt vào top-k khi truy xuất — đổi lại tốn thêm chunk và embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tách câu bằng regex lookbehind `(?<=[.!?])\s+`: cắt tại khoảng trắng đứng **sau** dấu câu nên dấu `.`, `!`, `?` vẫn nằm lại cuối câu (nếu dùng `[.!?]\s+` thì dấu câu bị nuốt mất). Sau đó bỏ câu rỗng, gom mỗi `max_sentences_per_chunk` câu thành một chunk và strip khoảng trắng; text rỗng trả về `[]`. Edge case chưa xử lý: chữ viết tắt (`TS.`, `v.v.`) và số thập phân có dấu chấm theo sau là khoảng trắng sẽ bị cắt sai.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thử separator theo thứ tự `["\n\n", "\n", ". ", " ", ""]`. Thuật toán chạy hai chiều: **đệ quy xuống** — mảnh nào vẫn dài hơn `chunk_size` thì gọi lại `_split` với danh sách separator còn lại; **gom lên** — các mảnh nhỏ liền kề được nối lại (kèm separator) tới sát `chunk_size` để không sinh chunk vụn. Có ba base case: đoạn đã ≤ `chunk_size` thì trả về luôn; hết separator (`[]`) thì cắt cứng theo `chunk_size`; separator rỗng `""` cũng cắt cứng theo ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu in-memory: mỗi `Document` thành một record `{id, content, metadata, embedding}` qua `_make_record` (copy metadata và luôn bảo đảm có `doc_id`). `add_documents` không tự chunk — 1 Document = 1 record. `search` nhúng câu hỏi một lần rồi tính tích vô hướng với từng embedding (vector đã chuẩn hoá nên dot = cosine), sắp xếp giảm dần và lấy `top_k`; kết quả trả về bỏ trường `embedding` cho gọn. Nhánh ChromaDB được giữ tắt (`_use_chroma = False`) vì không test nào cần và nhánh đó chưa được cài.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước**, search **sau**: chọn các record có metadata khớp toàn bộ `metadata_filter`, rồi mới chạy similarity search trên tập đã lọc. Nếu lấy top-k trước rồi mới lọc thì k slot có thể bị tài liệu sai đối tượng chiếm hết và còn lại 0 kết quả. `search` và `search_with_filter` dùng chung `_search_records` nên không filter thì hai hàm cho kết quả giống hệt nhau. `delete_document` giữ lại các record có `metadata['doc_id']` khác `doc_id` cần xoá và trả `True` nếu số record giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ba nhịp: truy xuất top-k → dựng prompt → gọi `llm_fn`. Ngữ cảnh được đánh số `[1] [2] [3]` kèm nguồn (`doc_id`), prompt yêu cầu model chỉ dùng ngữ cảnh, trích dẫn số `[n]` sau mỗi ý và nói rõ "Không tìm thấy thông tin trong tài liệu" nếu ngữ cảnh không có — để câu trả lời truy vết được về đúng chunk. Nếu store rỗng thì trả thông báo luôn, không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\vieth\OneDrive\Desktop\ItzMeHuangg\Vinno\Day09\Lab07\K4-L3A-Data-Foundations\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\vieth\OneDrive\Desktop\ItzMeHuangg\Vinno\Day09\Lab07\K4-L3A-Data-Foundations
plugins: anyio-4.15.1
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Embedder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Dự đoán được ghi trước khi chạy `compute_similarity`.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên được nhận học bổng khuyến khích học tập. | Người học đạt thành tích tốt sẽ được cấp tiền thưởng học tập. | cao | 0.733 | Đúng |
| 2 | Hạn nộp hồ sơ học bổng là ngày 30/06/2026. | Hồ sơ xin học bổng phải gửi trước cuối tháng 6 năm 2026. | cao | 0.805 | Đúng |
| 3 | Mỗi suất học bổng trị giá 5 triệu đồng. | Thư viện mở cửa từ 7 giờ sáng. | thấp | 0.167 | Đúng |
| 4 | Học bổng dành cho sinh viên có hoàn cảnh khó khăn. | Học bổng không dành cho sinh viên có hoàn cảnh khó khăn. | thấp | 0.773 | Sai |
| 5 | Điểm trung bình từ 3.20 trở lên. | Chó mèo là vật nuôi phổ biến. | thấp | 0.016 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 bất ngờ nhất: hai câu mang nghĩa **ngược nhau** (thêm chữ "không") nhưng vẫn đạt 0.773 — cao hơn cả cặp 1 vốn đồng nghĩa. Embedding chủ yếu mã hoá **chủ đề và từ vựng chung** (học bổng, sinh viên, hoàn cảnh khó khăn) chứ không nắm được logic phủ định. Hệ quả cho RAG: retrieval chỉ tìm được đoạn "cùng chủ đề", còn việc đoạn đó khẳng định hay phủ định điều kiện phải để LLM đọc kỹ ngữ cảnh, không thể tin vào điểm similarity.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chiến lược của tôi: `HeadingChunker(max_chunk_size=250, prepend_title=True)` — tách theo tiêu đề `##`/`###`, section dài hơn 250 ký tự thì hạ xuống `RecursiveChunker`, và gắn tiêu đề tài liệu vào đầu mọi chunk. Embedder `paraphrase-multilingual-MiniLM-L12-v2`, top-3, corpus `data/university` (9 tài liệu → 202 chunk). Agent chạy với LLM giả trích ngữ cảnh top-1 (nhóm không có API key LLM), nên cột "Câu trả lời" phản ánh đúng những gì agent nhận được làm căn cứ. Chi tiết đầy đủ: `ket_qua_benchmark.txt`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Học bổng Vallet sau đại học 2026 có bao nhiêu suất, mỗi suất bao nhiêu? | Vallet — "## 2. Giá trị và số lượng học bổng: 42 suất… 34.000.000 VNĐ/suất" | 0.861 | Có — chứa đáp án | Đúng: 42 suất, 34.000.000 VNĐ/suất |
| 2 | Học bổng Vững tương lai loại A trị giá bao nhiêu, dành cho ai? | NEU — "Hạng mục và giá trị học bổng: 590 suất học bổng thường niên…" (mảnh bị cắt trước dòng Loại A) | 0.838 | Đúng tài liệu, **thiếu đáp án** | Chỉ nêu 590 suất thường niên, không có 20.000.000 VNĐ |
| 3 | Điều kiện điểm học tập để xét học bổng TOTO ở FTU? | FTU — "## Đối tượng: sinh viên chính quy, hoàn cảnh khó khăn…" | 0.694 | Đúng tài liệu, **sai section** (đáp án ở "Tiêu chí") | Nêu đối tượng, không có mức 7.0/10, 28 tín chỉ |
| 4 | Khi nào UEH ra quyết định cấp học bổng KKHT học kỳ đầu 2026? | UEH — đoạn mở đầu "Căn cứ khung thời gian đào tạo năm 2026…" | 0.811 | Đúng tài liệu, **thiếu đáp án** (18/5/2026 nằm trong bảng) | Chỉ nêu UEH ban hành kế hoạch, không có ngày |
| 5 | Học bổng KKHT ở VIMARU được xét như thế nào? *(filter `audience=student`)* | VIMARU sinh viên — đoạn mở đầu "Tiêu chuẩn xét HBKKHT cho sinh viên…" | 0.739 | Đúng tài liệu và đúng đối tượng, **thiếu bảng mức điểm** | Nêu nguồn/phạm vi, không có ngưỡng 2.50/3.20/3.60 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 nếu chấm theo tài liệu (`doc_id` gold có trong top-3); chỉ **1 / 5** nếu chấm theo nội dung (chunk trong top-3 thực sự chứa đáp án). Điểm retrieval theo thang 2đ/câu: **2 / 10**.

Chênh lệch 5/5 và 1/5 là phát hiện chính: chấm theo `doc_id` thổi phồng kết quả. Ba nguyên nhân tôi tìm được khi phân tích:
- **Chunk mở đầu thắng chunk có đáp án** (Q4, Q5): đoạn mở đầu chứa tên trường + tên học bổng nên giống câu hỏi nhất, còn chunk chứa đáp án là bảng số liệu/ngày tháng, ít từ vựng chung với câu hỏi.
- **Section không tự mang ngữ cảnh**: ở bản đầu (`HeadingChunker(800)` không gắn tiêu đề), Q2 lấy nhầm section "Giá trị và số lượng học bổng" của **Vallet** vì section đó không nhắc tên học bổng. Gắn tiêu đề tài liệu vào mọi chunk sửa được lỗi này (Q2 quay về đúng tài liệu NEU) và nâng điểm từ 1/10 lên 2/10.
- **Giới hạn 128 token của model**: `paraphrase-multilingual-MiniLM-L12-v2` chỉ đọc 128 token đầu; với `HeadingChunker(800)+title`, 45/80 chunk dài hơn giới hạn nên phần cuối (thường là con số) bị cắt khi embed. Giảm xuống 250 ký tự còn 1/202 chunk bị cắt — nhưng điểm không tăng thêm, nên nút thắt chính vẫn là model nhỏ mã hoá bảng số liệu kém.

A/B với câu cần filter (Q5): không filter, top-1 là tài liệu **dành cho cán bộ** (`vimaru-hbkkht-quy-trinh-xet-duyet`, score 0.739 — bằng điểm tài liệu sinh viên); có `audience=student`, tài liệu cán bộ bị loại và top-1 chuyển về đúng tài liệu sinh viên. Filter sửa được **sai đối tượng**, nhưng không sửa được việc chọn sai chunk trong tài liệu.

Đề xuất cải thiện: dùng embedder mạnh hơn và có cửa sổ dài hơn (ví dụ `text-embedding-3-small`/`gemini-embedding-001`), tăng top-k rồi rerank, hoặc chuyển bảng số liệu thành câu văn đầy đủ ("Quyết định cấp học bổng KKHT học kỳ đầu năm 2026: 18/5/2026") trước khi embed.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> [Điền sau buổi demo.]

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
