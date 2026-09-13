# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Tạ Việt Cường 
> **Mã Sinh Viên / Mã Học viên:** 2A202602560 
> **Chủ đề Lựa chọn:** Hanoi Heart Hospital Assistant  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | **4** / 5 | Bài toán yêu cầu chuỗi suy luận liên hoàn: nhận diện mã bệnh nhân -> gọi Tool tra cứu hồ sơ để lấy thông tin bác sĩ điều trị và tiền sử bệnh lý -> tiếp tục sử dụng thông tin bác sĩ đó để gọi Tool đặt lịch thăm khám phù hợp. |
| **2. Tool Interaction** | **5** / 5 | Bắt buộc phải tương tác với MCP Server bên ngoài để truy xuất cơ sở dữ liệu hồ sơ bệnh án nội bộ (BHYT, tiền sử tăng huyết áp, hở van tim...) và hệ thống đặt lịch khám thời gian thực. Dữ liệu y tế là dữ liệu động, LLM tĩnh không thể tự suy diễn. |
| **3. Dynamic Decision** | **5** / 5 | Hành động của Agent thay đổi linh hoạt theo kết quả Observation: Nếu hồ sơ hợp lệ thì trích xuất thông tin điều trị; nếu Tool trả về `NOT_FOUND` thì kích hoạt nhánh xử lý an toàn (Anti-Hallucination), hướng dẫn bệnh nhân liên hệ lễ tân; nếu người dùng hỏi chung thì trả lời trực tiếp không gọi Tool. |
| **4. Long Horizon Goal** | **4** / 5 | Hệ thống cần duy trì mục tiêu chăm sóc bệnh nhân xuyên suốt chuỗi hội thoại (ReAct Loop), lưu giữ ngữ cảnh về mã bệnh nhân và lịch hẹn để đảm bảo trải nghiệm liền mạch từ lúc tra cứu đến khi đặt lịch thành công. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | *Kết luận: Đạt 18/20 điểm (> 12/20), bài toán Hanoi Heart Hospital Assistant hoàn toàn phù hợp và cần thiết để triển khai theo kiến trúc ReAct Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật (minh chứng quy trình Tool Calling và Final Answer trên ca thử nghiệm TC02 - Tra cứu hồ sơ bệnh nhân):

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu hồ sơ bệnh nhân BN2026001 giúp tôi.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "patient_lookup",
    "arguments": {
      "patient_id": "BN2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "patient_id": "BN2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "birth_year": 1975,
        "medical_record": "Tăng huyết áp độ 2, đã ổn định",
        "insurance": "BHYT hạn đến 12/2026",
        "status": "Đang điều trị ngoại trú",
        "attending_doctor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 2141.03
  },
  {
    "step": 2,
    "query": "Hãy tra cứu hồ sơ bệnh nhân BN2026001 giúp tôi.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Dưới đây là thông tin hồ sơ bệnh nhân BN2026001:\n*   **Họ và tên:** Nguyễn Văn An\n*   **Năm sinh:** 1975\n*   **Hồ sơ bệnh án:** Tăng huyết áp độ 2, đã ổn định\n*   **Bảo hiểm y tế:** BHYT hạn đến 12/2026\n*   **Tình trạng:** Đang điều trị ngoại trú\n*   **Bác sĩ điều trị:** PGS.TS Nguyễn Văn A",
    "latency_ms": 3643.84
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Google Gemini API).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases (TC01: Direct Query, TC02: Single Tool Lookup, TC03: Appointment Booking, TC04: Multi-step Reasoning, TC05: Edge-case Handling).
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt gọi (`patient_lookup` và `book_appointment`).
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
> 🔗 **Repository URL:** `https://github.com/ratrichero/K4-DAY03-TaVietCuong-2A202602560`

