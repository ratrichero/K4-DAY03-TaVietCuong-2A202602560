"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""

    @staticmethod
    def _build_prompt_with_history(prompt: str, conversation_history: List[Dict[str, Any]] = None) -> str:
        """Nạp các Observation đã thu thập vào prompt để LLM suy luận đa bước (ReAct)"""
        if not conversation_history:
            return prompt
        lines = [
            f"CÂU HỎI CỦA NGƯỜI DÙNG: {prompt}",
            "",
            "DỮ LIỆU ĐÃ THU THẬP TỪ CÁC LẦN GỌI TOOL TRƯỚC (Observation):"
        ]
        for i, h in enumerate(conversation_history, 1):
            args_str = json.dumps(h.get("arguments", {}), ensure_ascii=False)
            obs_str = json.dumps(h.get("observation", {}), ensure_ascii=False)
            lines.append(f"- Lần {i}: gọi tool '{h.get('tool_name')}' với tham số {args_str}")
            lines.append(f"  Observation: {obs_str}")
        lines.append("")
        lines.append("NHIỆM VỤ BÂY GIỜ: Nếu đã đủ dữ liệu để trả lời, hãy tổng hợp câu trả lời cuối cùng cho người dùng (không gọi tool nữa). Nếu chưa đủ dữ liệu cho bước kế tiếp, hãy gọi tool tương ứng.")
        return "\n".join(lines)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "", conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "", conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Nếu đã có Observation trong lịch sử -> tổng hợp câu trả lời trực tiếp (ReAct)
        if conversation_history:
            last_obs = conversation_history[-1].get("observation", {})
            if last_obs.get("status") == "NOT_FOUND":
                return {
                    "type": "text",
                    "content": f"[Mock Agent Response]: Rất tiếc, {last_obs.get('message', 'không tìm thấy hồ sơ bệnh nhân')}. Vui lòng kiểm tra lại mã bệnh nhân hoặc liên hệ lễ tân Bệnh viện Tim Hà Nội.",
                    "thought": "Tool trả về NOT_FOUND, phản hồi lịch sự không bịa đặt dữ liệu."
                }
            if last_obs.get("status") == "SUCCESS" and "booking_id" in last_obs:
                return {
                    "type": "text",
                    "content": f"[Mock Agent Response]: {last_obs.get('message')} (Mã lịch hẹn: {last_obs.get('booking_id')})",
                    "thought": "Đã đặt lịch thăm khám thành công, tổng hợp kết quả phản hồi."
                }
            if last_obs.get("status") == "SUCCESS" and "data" in last_obs:
                d = last_obs.get("data", {})
                return {
                    "type": "text",
                    "content": f"[Mock Agent Response]: Bệnh nhân {d.get('full_name')} ({last_obs.get('patient_id')}), hồ sơ: {d.get('medical_record')}, bác sĩ điều trị: {d.get('attending_doctor')}, trạng thái: {d.get('status')}.",
                    "thought": "Đã nhận được dữ liệu hồ sơ bệnh nhân từ MCP Server, tổng hợp câu trả lời."
                }
        prompt_lower = prompt.lower()
        
        # Mô phỏng nhận diện intent gọi Tool (đề tài: Bệnh viện Tim Hà Nội)
        if "đặt lịch" in prompt_lower or "book_appointment" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "book_appointment",
                "arguments": {"patient_id": "BN2026001", "datetime_str": "14:00 20/09/2026", "doctor_name": "PGS.TS Nguyễn Văn A"},
                "thought": "Người dùng yêu cầu đặt lịch thăm khám. Tôi sẽ gọi tool book_appointment."
            }
        elif "bn2026001" in prompt_lower or "bn2026002" in prompt_lower or "tra cứu" in prompt_lower or "hồ sơ" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "patient_lookup",
                "arguments": {"patient_id": "BN2026001" if "bn2026002" not in prompt_lower else "BN2026002"},
                "thought": "Người dùng muốn tra cứu hồ sơ bệnh nhân. Tôi sẽ gọi tool patient_lookup."
            }
        else:
            return {
                "type": "text",
                "content": "[Mock Agent Response]: Xin chào! Bệnh viện Tim Hà Nội nhận bệnh từ 7:00 đến 17:00 các ngày trong tuần. Vui lòng cung cấp mã bệnh nhân (ví dụ BN2026001) để tôi tra cứu hồ sơ hoặc đặt lịch thăm khám.",
                "thought": "Câu hỏi chung về quy trình khám chữa bệnh, trả lời trực tiếp không cần gọi Tool."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "", conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, conversation_history)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            # Nạp Observation vào prompt cho suy luận đa bước + retry khi hết hạn mức free tier (429)
            contents = self._build_prompt_with_history(prompt, conversation_history)
            response = None
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=config
                    )
                    break
                except Exception as api_err:
                    err_str = str(api_err)
                    if attempt == 0 and "429" in err_str:
                        wait_s = 30
                        m = re.search(r"retry in ([\d.]+)", err_str)
                        if m:
                            wait_s = min(int(float(m.group(1))) + 2, 60)
                        print(f"⏳ [Gemini Rate Limit]: Vượt hạn mức free tier (5 req/phút). Chờ {wait_s}s rồi thử lại...")
                        time.sleep(wait_s)
                        continue
                    raise

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                text_content = response.text or ""
                thought_text = "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                # Tách dòng "Thought:" do LLM tự thêm vào đầu câu trả lời (nếu có)
                if text_content.strip().startswith("Thought:"):
                    first_line, _, rest = text_content.strip().partition("\n")
                    thought_text = first_line.replace("Thought:", "").strip() or thought_text
                    text_content = rest.strip()
                return {
                    "type": "text",
                    "content": text_content,
                    "thought": thought_text
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, conversation_history)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "", conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, conversation_history)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": self._build_prompt_with_history(prompt, conversation_history)})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, conversation_history)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
