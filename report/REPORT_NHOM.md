# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học bổng đại học — thông báo, tiêu chuẩn và quy trình xét học bổng của các trường/quỹ tại Việt Nam (thuộc mảng "dịch vụ/quy định đại học" bắt buộc của lớp L3A).

**Tại sao nhóm chọn chủ đề này?**
> Học bổng là câu hỏi sinh viên tra cứu nhiều nhất và đáp án luôn là con số, mốc thời gian hoặc điều kiện cụ thể — dễ viết gold answer kiểm chứng được. Các thông báo học bổng có cấu trúc theo mục rõ ràng (Đối tượng, Giá trị, Hồ sơ, Thời hạn), phù hợp để so sánh chunk theo tiêu đề với các chiến lược khác. Bộ tài liệu gồm nhiều trường khác nhau nên có sẵn thử thách truy xuất: cùng từ vựng "học bổng" nhưng đáp án khác nhau theo từng trường và từng đối tượng.

### Danh sách tài liệu (Data Inventory)

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

Tài liệu 7 và 8 lấy từ **cùng một trang** VIMARU nhưng được tách theo đối tượng (phần tiêu chuẩn cho sinh viên / phần các bước xét duyệt cho cán bộ), để `metadata_filter={"audience": "student"}` có việc thật để lọc.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string (`student`/`faculty`/`staff`/`all`) | `student` | Loại tài liệu dành cho đối tượng khác (quy trình cho cán bộ, học bổng cho giảng viên) khi sinh viên hỏi — dùng trong câu Q5. |
| `student_level` | string | `undergraduate`, `graduate`, `prospective` | Tách học bổng sau đại học (Vallet) và học bổng tân sinh viên (HSB) khỏi học bổng cho sinh viên đang học. |
| `institution` | string | `ueh`, `ftu`, `vimaru` | Corpus nhiều trường dùng chung từ vựng "học bổng"; lọc theo trường tránh trả lời bằng quy định của trường khác. |
| `category` | string | `scholarship` | Chuẩn bị cho việc mở rộng corpus sang học phí, thư viện… mà vẫn lọc được theo mảng. |
| `department` | string | `ueh-student-affairs` | Truy vết đơn vị ban hành để sinh viên biết liên hệ ở đâu. |
| `source_url`, `retrieved_at`, `document_version`, `published_at` | string / ngày | `2026-09-19`, `02-2026/TB-HBSĐHMB` | Kiểm tra độ mới và truy vết câu trả lời về đúng văn bản gốc. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(body, chunk_size=500)` trên 3 tài liệu (đã bỏ frontmatter):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| vallet-hoc-bong-sau-dai-hoc | FixedSizeChunker (`fixed_size`) | 15 | 493 | Kém — cắt ngang câu và ngang bảng điểm thành tích |
| vallet-hoc-bong-sau-dai-hoc | SentenceChunker (`by_sentences`) | 25 | 266 | Trung bình — câu trọn vẹn nhưng tách rời các gạch đầu dòng của cùng một mục |
| vallet-hoc-bong-sau-dai-hoc | RecursiveChunker (`recursive`) | 21 | 317 | Khá — cắt theo đoạn/dòng nên phần lớn giữ trọn mục |
| ueh-ke-hoach-xet-hoc-bong-2026 | FixedSizeChunker (`fixed_size`) | 12 | 465 | Kém — cắt ngang bảng mốc thời gian |
| ueh-ke-hoach-xet-hoc-bong-2026 | SentenceChunker (`by_sentences`) | 10 | 501 | Kém — bảng không có dấu chấm câu nên nhiều dòng bị gộp thành chunk dài |
| ueh-ke-hoach-xet-hoc-bong-2026 | RecursiveChunker (`recursive`) | 16 | 313 | Khá — tách theo dòng bảng, mỗi chunk còn đủ vài mốc |
| vimaru-hbkkht-tieu-chuan-sinh-vien | FixedSizeChunker (`fixed_size`) | 6 | 439 | Kém — bảng mức học bổng bị chia đôi |
| vimaru-hbkkht-tieu-chuan-sinh-vien | SentenceChunker (`by_sentences`) | 4 | 593 | Trung bình — ít chunk, mỗi chunk trộn nhiều mục |
| vimaru-hbkkht-tieu-chuan-sinh-vien | RecursiveChunker (`recursive`) | 7 | 339 | Khá — bảng mức học bổng nằm trọn trong một chunk |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người). Cả nhóm dùng chung `bench.py`, chỉ đổi dòng `CHUNKER = ...`.

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** custom — `HeadingChunker(max_chunk_size=250, prepend_title=True)` (chunk theo heading/section, chiến lược bắt buộc của L3A)
- **Mô tả & lý do chọn cho chủ đề này:** Thông báo học bổng được viết theo mục (Đối tượng, Giá trị, Hồ sơ, Thời hạn), mỗi mục là một đơn vị ngữ nghĩa trọn vẹn nên tách tại mỗi heading `##`/`###`; mục dài quá 250 ký tự thì hạ xuống `RecursiveChunker` và gắn lại heading vào từng mảnh con. Ngoài ra gắn **tiêu đề tài liệu** vào đầu mọi chunk: bản đầu không gắn tiêu đề thì section "Giá trị và số lượng học bổng" của Vallet thắng câu hỏi về học bổng NEU vì section không nhắc tên học bổng. Ngưỡng 250 ký tự được chọn vì embedder `paraphrase-multilingual-MiniLM-L12-v2` chỉ đọc 128 token: với ngưỡng 800, 45/80 chunk bị cắt khi embed; với 250 chỉ còn 1/202.
- **Code snippet (nếu custom):**
```python
class HeadingChunker:
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

**Thành viên 2 — [Tên]**
- **Loại chiến lược:** FixedSize — `FixedSizeChunker(chunk_size=500, overlap=100)`
- **Mô tả & lý do chọn:** [Thành viên 2 điền — gợi ý: overlap 100 để thông tin nằm ở biên chunk có hai cơ hội lọt top-k.]
- **Code snippet (nếu custom):** không (built-in)

**Thành viên 3 — [Tên]**
- **Loại chiến lược:** Recursive — `RecursiveChunker(chunk_size=500)`
- **Mô tả & lý do chọn:** [Thành viên 3 điền — gợi ý: cắt theo ranh giới đoạn/dòng trước nên giữ được bảng và danh sách.]
- **Code snippet (nếu custom):** không (built-in)

### So Sánh Giữa Các Thành Viên

> Cùng `bench.py`, cùng 5 câu hỏi, embedder `paraphrase-multilingual-MiniLM-L12-v2`, top-3. Điểm retrieval theo thang 2đ/câu (2đ: gold top-1 và ngữ cảnh chứa đáp án; 1đ: ngữ cảnh chứa đáp án nhưng không ở top-1; 0đ: ngữ cảnh không chứa đáp án). Dòng của thành viên 2, 3 là **kết quả tham chiếu** — thay bằng lần chạy của chính thành viên đó.

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Thành viên 1 | HeadingChunker(250) + tiêu đề tài liệu (202 chunk) | 2 | Đúng tài liệu 5/5 câu; Q1 đạt 2/2; chunk tự mang ngữ cảnh "thuộc học bổng nào" | Nhiều chunk ngắn; bảng số liệu (Q4, Q5) vẫn thua đoạn mở đầu |
| Thành viên 2 | FixedSize(500, overlap=100) (89 chunk) | 0 | Đơn giản, đều kích thước | Cắt ngang câu và bảng; đúng tài liệu 4/5 nhưng không chunk nào chứa đáp án |
| Thành viên 3 | Recursive(500) (109 chunk) | 0 | Giữ bảng/danh sách trọn hơn FixedSize | Chunk không mang tên học bổng nên lẫn giữa các trường; 0/5 ngữ cảnh chứa đáp án |

Các cấu hình tham khảo thêm (cùng điều kiện): `Sentence(3)` 1/10; `HeadingChunker(800)` không gắn tiêu đề 1/10; `HeadingChunker(800)` + tiêu đề 2/10; `Recursive(500)` + tiêu đề 2/10.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chunk theo heading **kèm tiêu đề tài liệu** tốt nhất (2/10, đúng tài liệu 5/5), nhưng yếu tố quyết định là **gắn tiêu đề** chứ không phải cách cắt: gắn tiêu đề vào `Recursive(500)` cũng nâng từ 0 lên 2/10. Lý do: corpus gồm nhiều thông báo học bổng dùng chung từ vựng, section như "Giá trị học bổng" không tự nói nó thuộc trường/quỹ nào, nên embedding cần tiêu đề để phân biệt. Điểm tuyệt đối vẫn thấp vì đáp án của 4/5 câu nằm trong bảng/danh sách con số — thứ mà model nhỏ 128 token mã hoá kém — nên đoạn mở đầu nhiều từ khoá luôn thắng chunk chứa đáp án.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học bổng Vallet sau đại học năm 2026 có bao nhiêu suất và mỗi suất trị giá bao nhiêu? | 42 suất, mỗi suất 34.000.000 VNĐ | `vallet-hoc-bong-sau-dai-hoc` — mục "2. Giá trị và số lượng học bổng" |
| 2 | Học bổng Vững tương lai loại A trị giá bao nhiêu và dành cho ai? | 130 suất, 20.000.000 VNĐ/suất; HSSV đạt chuẩn loại B và có thành tích xuất sắc, tiêu biểu / thủ khoa đầu vào / hoàn cảnh đặc biệt khó khăn | `neu-hoc-bong-vung-tuong-lai-2025-2026` — mục "Hạng mục và giá trị học bổng (810 suất)" |
| 3 | Điều kiện điểm học tập để xét học bổng TOTO ở Đại học Ngoại thương là gì? | Điểm TBC năm học 2025-2026 từ 7.0/10 hoặc 2.8/4 trở lên; tích lũy tối thiểu 28 tín chỉ/năm học | `ftu-hoc-bong-toto-2026` — mục "Tiêu chí" |
| 4 | Khi nào UEH ra quyết định cấp học bổng khuyến khích học tập học kỳ đầu năm 2026? | 18/5/2026 (học kỳ cuối năm 2026: 10/11/2026) | `ueh-ke-hoach-xet-hoc-bong-2026` — bảng "1.2. Các mốc thời gian thực hiện" |
| 5 | Học bổng khuyến khích học tập ở VIMARU được xét như thế nào? *(cần `metadata_filter={"audience": "student"}`)* | Loại Khá: 2.50 ≤ ĐTBHB < 3.20, rèn luyện từ 70; Giỏi: 3.20 ≤ ĐTBHB < 3.60, từ 80; Xuất sắc: ĐTBHB ≥ 3.60, từ 90 đến 100 | `vimaru-hbkkht-tieu-chuan-sinh-vien` — mục "Tiêu chuẩn cụ thể cho các mức học bổng" |

Dạng câu hỏi: tra số liệu (Q1), giá trị + đối tượng (Q2), điều kiện (Q3), mốc thời gian (Q4), câu hỏi không nêu người hỏi là ai nên cần lọc đối tượng (Q5).

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Học bổng Vallet: số suất, giá trị | HeadingChunker(250) + tiêu đề | Có — top-1 chứa đáp án (2/2) | Không gắn tiêu đề: đúng tài liệu nhưng chunk đáp án chỉ ở top-3 (1/2) |
| 2 | Vững tương lai loại A | — (không chiến lược nào lấy được đáp án) | Đúng tài liệu, không có đáp án | Mảnh chứa "Loại A - 130 suất, 20.000.000" thua mảnh "590 suất thường niên"; không gắn tiêu đề thì còn lấy nhầm section "Giá trị" của Vallet |
| 3 | Điều kiện điểm học bổng TOTO | Sentence(3) (1/2) | Đúng tài liệu; chỉ Sentence(3) có đáp án trong top-3 | Heading/Recursive trả về mục "Đối tượng" thay vì "Tiêu chí" — hai mục cùng nói về điều kiện |
| 4 | Ngày quyết định cấp HB KKHT của UEH | Recursive(500) + tiêu đề (2/2) | Đúng tài liệu; chỉ cấu hình này có đáp án | Ngày nằm trong bảng mốc thời gian; đoạn mở đầu kế hoạch thắng ở các chiến lược khác |
| 5 | Xét HBKKHT ở VIMARU (có filter) | — (không chiến lược nào lấy được bảng mức điểm) | Đúng tài liệu sinh viên, không có đáp án | Đoạn mở đầu "Tiêu chuẩn xét HBKKHT…" thắng bảng mức học bổng |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, ở Q5. Không filter, top-1 là tài liệu **dành cho cán bộ** (`vimaru-hbkkht-quy-trinh-xet-duyet`, score 0.739 — bằng đúng điểm tài liệu sinh viên), tức agent sẽ trả lời bằng các bước "Cố vấn học tập họp lớp xét phân loại…" — sai đối tượng. Có `audience=student`, tài liệu cán bộ bị loại và top-1 chuyển về tài liệu tiêu chuẩn cho sinh viên. Filter sửa được lỗi **sai đối tượng**, nhưng không sửa được việc chọn sai chunk bên trong tài liệu đúng; và nếu lọc quá chặt (ví dụ thêm `student_level=undergraduate`) sẽ loại mất học bổng sau đại học Vallet khi học viên cao học hỏi.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Chấm theo `doc_id` thổi phồng kết quả:** mọi chiến lược đều tìm đúng tài liệu 4–5/5 câu, nhưng chunk thực sự chứa đáp án chỉ lọt top-3 ở 0–1/5 câu.
> 2. **Chunk phải tự mang ngữ cảnh:** gắn tiêu đề tài liệu vào mọi chunk là thay đổi hiệu quả nhất (Recursive 0 → 2/10, Heading 1 → 2/10) vì corpus nhiều trường dùng chung từ vựng.
> 3. **Giới hạn 128 token của model:** với chunk 800 ký tự + tiêu đề, 45/80 chunk bị cắt khi embed — độ dài chunk phải chọn theo cửa sổ của embedder, không chỉ theo cấu trúc văn bản.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng tài liệu nhưng chiến lược khác nhau cho kết quả khác nhau theo từng câu: Sentence(3) là cấu hình duy nhất lấy được tiêu chí TOTO (Q3), Recursive + tiêu đề là cấu hình duy nhất lấy được ngày của UEH (Q4), còn Heading + tiêu đề thắng ở Q1. Không có chiến lược nào thắng tuyệt đối; cách cắt ảnh hưởng ít hơn việc chunk có mang đủ ngữ cảnh để phân biệt với tài liệu khác hay không.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Khi làm sạch dữ liệu, viết lại các bảng mốc thời gian/mức điểm thành câu văn đầy đủ ("Quyết định cấp học bổng KKHT học kỳ đầu năm 2026 của UEH: 18/5/2026") để embedding hiểu được; tách thêm tài liệu theo `audience` cho nhiều trường hơn (hiện chỉ VIMARU có cặp student/staff) để phép thử filter có nhiều câu hỏi hơn; và dùng embedder có cửa sổ dài hơn hoặc thêm bước rerank thay vì chỉ lấy top-3 theo cosine.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 4 / 10 |
| Thuyết trình (Demo) | [sau buổi demo] / 5 |
| **Tổng phần nhóm** | **[tổng] / 40** |
