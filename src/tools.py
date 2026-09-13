"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND — BỆNH VIỆN TIM HÀ NỘI (HANOI HEART HOSPITAL)
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.

Đề tài: Trợ lý Bệnh viện Tim Hà Nội — tra cứu hồ sơ bệnh nhân & đặt lịch thăm khám.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu hồ sơ bệnh nhân (mẫu chuẩn)
    {
        "name": "patient_lookup",
        "description": "Tra cứu hồ sơ bệnh nhân của Bệnh viện Tim Hà Nội bằng mã bệnh nhân.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Mã bệnh nhân cần tra cứu (ví dụ: 'BN2026001')"
                }
            },
            "required": ["patient_id"]
        }
    },

    # --------------------------------------------------------------------------
    # TODO 1.2: TOOL SCHEMA CHO 'book_appointment' — HOÀN THIỆN THEO ĐỀ TÀI
    # 🎯 Thiết kế chuẩn JSON Schema Standard:
    # 1. Tool dùng để đặt lịch thăm khám/tư vấn với bác sĩ chuyên khoa Tim mạch.
    # 2. Tham số (properties) để LLM trích xuất:
    #    - patient_id (string): Mã bệnh nhân cần đặt lịch (ví dụ: 'BN2026001')
    #    - datetime_str (string): Thời gian hẹn (ví dụ: '14:00 20/09/2026')
    #    - doctor_name (string): Tên bác sĩ chuyên khoa Tim mạch
    # 3. Khai báo danh sách các trường bắt buộc (required).
    # --------------------------------------------------------------------------
    {
        "name": "book_appointment",
        "description": "Đặt lịch thăm khám/tư vấn với bác sĩ chuyên khoa tại Bệnh viện Tim Hà Nội.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Mã bệnh nhân cần đặt lịch (ví dụ: 'BN2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn thăm khám (ví dụ: '14:00 20/09/2026')"
                },
                "doctor_name": {
                    "type": "string",
                    "description": "Tên bác sĩ chuyên khoa Tim mạch (ví dụ: 'PGS.TS Nguyễn Văn A')"
                }
            },
            "required": ["patient_id", "datetime_str", "doctor_name"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "BN2026001": {
        "full_name": "Nguyễn Văn An",
        "birth_year": 1975,
        "medical_record": "Tăng huyết áp độ 2, đã ổn định",
        "insurance": "BHYT hạn đến 12/2026",
        "status": "Đang điều trị ngoại trú",
        "attending_doctor": "PGS.TS Nguyễn Văn A"
    },
    "BN2026002": {
        "full_name": "Trần Thị Bình",
        "birth_year": 1982,
        "medical_record": "Hở van tim 2 lá nhẹ, tái khám định kỳ 6 tháng",
        "insurance": "BHYT hạn đến 08/2026",
        "status": "Tái khám định kỳ",
        "attending_doctor": "TS. Lê Thị B"
    }
}


def execute_patient_lookup(patient_id: str) -> str:
    """Thực thi tra cứu hồ sơ bệnh nhân theo mã"""
    patient = MOCK_DATABASE.get(patient_id.strip().upper())
    if patient:
        return json.dumps({
            "status": "SUCCESS",
            "patient_id": patient_id,
            "data": patient
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy hồ sơ bệnh nhân có mã '{patient_id}'"
        }, ensure_ascii=False)


def execute_book_appointment(patient_id: str, datetime_str: str, doctor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch thăm khám tại Bệnh viện Tim Hà Nội"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"APPT-{patient_id}-99",
        "patient_id": patient_id,
        "datetime": datetime_str,
        "doctor": doctor_name,
        "message": f"Đặt lịch thăm khám thành công cho bệnh nhân {patient_id} với bác sĩ {doctor_name} vào lúc {datetime_str} tại Bệnh viện Tim Hà Nội."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "patient_lookup": execute_patient_lookup,
    "book_appointment": execute_book_appointment
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
