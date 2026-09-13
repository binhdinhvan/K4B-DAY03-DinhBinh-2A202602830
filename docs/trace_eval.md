# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đinh Văn Bình  
> **Mã Sinh Viên / Mã Học viên:** 2A202602830  
> **Chủ đề Lựa chọn:** Trợ lý Học vụ & Đặt lịch tư vấn VinUni (Gợi ý 1.1)

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Bài toán cần suy luận nhiều bước: Tra cứu sinh viên để biết Cố vấn học tập phụ trách trước, sau đó mới tiến hành đặt lịch hẹn với đúng cố vấn đó. |
| **2. Tool Interaction** | 5 / 5 | Bắt buộc phải kết nối cơ sở dữ liệu học vụ qua MCP Server để tra cứu hồ sơ thật (GPA, lớp, trạng thái) và ghi nhận lịch hẹn; LLM không thể tự bịa dữ liệu sinh viên. |
| **3. Dynamic Decision** | 4 / 5 | Quyết định bước tiếp theo phụ thuộc vào kết quả quan sát từ bước trước: Nếu tra cứu sinh viên trả về NOT_FOUND thì phải dừng và báo lỗi, nếu SUCCESS mới tiếp tục xử lý. |
| **4. Long Horizon Goal** | 4 / 5 | Giữ mục tiêu hoàn tất thủ tục tư vấn học vụ xuyên suốt phiên hội thoại, ghi nhận thông tin xác nhận và mã booking cho sinh viên. |
| **TỔNG ĐIỂM AGENTIC FIT** | **17 / 20** | *Tổng điểm 17/20 (> 12/20): Bài toán hoàn toàn phù hợp để triển khai ReAct Agent.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 500.88
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
