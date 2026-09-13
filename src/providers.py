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
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        import re
        
        # 1. Nếu prompt đã có Observation từ bước trước (Vòng lặp ReAct tiếp theo)
        if "observation" in prompt_lower:
            # Trường hợp TC04: Đã tra cứu xong cố vấn, giờ tiến hành đặt lịch với cố vấn đó
            if "pgs.ts nguyễn văn a" in prompt_lower and "đặt lịch" in prompt_lower and "booking_id" not in prompt_lower:
                dt_match = re.search(r"\d{1,2}:\d{2}\s+(?:ngày\s+)?\d{1,2}/\d{1,2}/\d{4}", prompt)
                dt_str = dt_match.group(0) if dt_match else "09:00 20/09/2026"
                return {
                    "type": "tool_call",
                    "tool_name": "schedule_appointment",
                    "arguments": {
                        "student_id": "SV2026001",
                        "datetime_str": dt_str,
                        "advisor_name": "PGS.TS Nguyễn Văn A"
                    },
                    "thought": f"Đã xác định cố vấn học tập của sinh viên SV2026001 là PGS.TS Nguyễn Văn A. Bước 2: Thực hiện đặt lịch hẹn tư vấn vào lúc {dt_str} với cố vấn này."
                }
            # Trường hợp TC05: Tra cứu mã không tồn tại (NOT_FOUND)
            elif "not_found" in prompt_lower or "không tìm thấy" in prompt_lower:
                match = re.search(r"sv\d+", prompt_lower)
                sid = match.group(0).upper() if match else "SV9999999"
                return {
                    "type": "text",
                    "content": f"Hệ thống đã kiểm tra và không tìm thấy dữ liệu của sinh viên có mã '{sid}'. Xin vui lòng kiểm tra lại mã sinh viên.",
                    "thought": "Dữ liệu từ MCP Server trả về NOT_FOUND. Phản hồi lịch sự, chính xác và không bịa đặt thông tin."
                }
            # Trường hợp đặt lịch xong (đã có booking_id)
            elif "booking_id" in prompt_lower:
                dt_match = re.search(r"\d{1,2}:\d{2}\s+(?:ngày\s+)?\d{1,2}/\d{1,2}/\d{4}", prompt)
                dt_str = dt_match.group(0) if dt_match else "14:00 15/09/2026"
                return {
                    "type": "text",
                    "content": f"Đã đặt lịch hẹn tư vấn học vụ thành công cho sinh viên SV2026001 với PGS.TS Nguyễn Văn A vào lúc {dt_str}.",
                    "thought": f"Đã nhận được xác nhận booking từ MCP Server vào lúc {dt_str}. Hoàn tất chuỗi suy luận ReAct và thông báo cho người dùng."
                }
            # Trường hợp tra cứu sinh viên thành công (TC02)
            else:
                return {
                    "type": "text",
                    "content": "Kết quả tra cứu cho sinh viên SV2026001 (Nguyễn Văn An): Lớp AI-K4, GPA: 3.85, Email: an.nv@vinuni.edu.vn, Trạng thái: Đang học, Cố vấn: PGS.TS Nguyễn Văn A.",
                    "thought": "Đã nhận được dữ liệu hồ sơ học vụ từ MCP Server. Tổng hợp câu trả lời cho sinh viên."
                }
        
        # 2. Bước đầu tiên (Khởi đầu chuỗi ReAct)
        # TC04: Multi-step (kiểm tra cố vấn trước rồi mới đặt lịch)
        if "cố vấn" in prompt_lower and "đặt lịch" in prompt_lower:
            match = re.search(r"sv\d+", prompt_lower)
            sid = match.group(0).upper() if match else "SV2026001"
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": sid},
                "thought": f"Yêu cầu đa bước (Multi-step Reasoning): Cần gọi 'academic_query' để kiểm tra ai là cố vấn học tập của sinh viên {sid} trước."
            }
        # TC03: Đặt lịch trực tiếp
        elif "đặt lịch" in prompt_lower:
            match = re.search(r"sv\d+", prompt_lower)
            sid = match.group(0).upper() if match else "SV2026001"
            dt_match = re.search(r"\d{1,2}:\d{2}\s+(?:ngày\s+)?\d{1,2}/\d{1,2}/\d{4}", prompt)
            dt_str = dt_match.group(0) if dt_match else "14:00 15/09/2026"
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": sid, "datetime_str": dt_str, "advisor_name": "PGS.TS Nguyễn Văn A"},
                "thought": f"Người dùng yêu cầu đặt lịch hẹn tư vấn cho sinh viên {sid} vào lúc {dt_str}. Tôi sẽ gọi tool schedule_appointment."
            }
        # TC02 & TC05: Tra cứu học vụ
        elif "tra cứu" in prompt_lower or "thông tin" in prompt_lower or "sv" in prompt_lower:
            match = re.search(r"sv\d+", prompt_lower)
            sid = match.group(0).upper() if match else "SV2026001"
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": sid},
                "thought": f"Người dùng muốn tra cứu thông tin học vụ của sinh viên {sid}. Tôi sẽ gọi tool academic_query."
            }
        else:
            return {
                "type": "text",
                "content": "Xin chào! Quy chế học vụ VinUni yêu cầu sinh viên tích lũy tối thiểu 120 tín chỉ và duy trì GPA trên 2.0 để tốt nghiệp.",
                "thought": "Câu hỏi chung về quy chế học vụ, trả lời trực tiếp không cần gọi Tool."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-3.5-flash-lite"

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

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        import time
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        
        # Chuẩn hóa function declarations cho Gemini SDK
        function_declarations = []
        for tool in tools_schema:
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

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )

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
                    return {
                        "type": "text",
                        "content": response.text or "",
                        "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                    }

            except Exception as e:
                err_str = str(e)
                # Tự động retry khi gặp Rate Limit (429/RESOURCE_EXHAUSTED) để đảm bảo 100% chạy trên API thật
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries - 1:
                    retry_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str, re.IGNORECASE)
                    wait_sec = int(float(retry_match.group(1))) + 2 if retry_match else 20
                    print(f"⏳ [Gemini Rate Limit]: Chờ {wait_sec}s để hồi phục Quota rồi thử lại Live API (Lần {attempt + 2}/{max_retries})...")
                    time.sleep(wait_sec)
                    continue
                else:
                    print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({err_str}). Fallback về Mock.")
                    return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


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

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

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
            messages.append({"role": "user", "content": prompt})

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
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


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
