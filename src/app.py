"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    current_prompt = user_query
    
    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(current_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        
        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break
            
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")
            
            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            
            if not obs_data:
                obs_str = "{}"
                print(f"👁️ [Observation từ MCP Server]: {{}}")
            else:
                obs_str = json.dumps(obs_data, ensure_ascii=False)
                print(f"👁️ [Observation từ MCP Server]: {obs_str}")
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            
            # Nạp Observation vào ngữ cảnh để tiếp tục vòng lặp ReAct cho bước tiếp theo
            current_prompt += (
                f"\n\n[Observation Step {step}]: {obs_str}\n"
                f"(Từ kết quả quan sát trên, hãy suy luận bước tiếp theo: nếu cần gọi thêm công cụ thì đề xuất gọi, "
                f"nếu đã có đủ thông tin thì trả lời kết luận cuối cùng cho sinh viên)."
            )
            
            # Nếu đạt tối đa số vòng lặp mà chưa hoàn tất, xuất kết luận fallback
            if step >= MAX_ITERATIONS:
                fallback_msg = f"Đã kết thúc sau {step} bước suy luận ReAct: {obs_str}"
                print(f"🏁 [Final Answer]: {fallback_msg}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "Đạt giới hạn số bước ReAct tối đa, tổng kết phản hồi.",
                    "output": fallback_msg,
                    "latency_ms": 10.0
                })
                break

    return trace_logs


def verify_test_case(tc: dict, logs: list) -> tuple:
    """Kiểm tra logic đúng/sai của Test Case theo expected_behavior"""
    tc_id = tc.get("id")
    tool_calls = [l for l in logs if l.get("action_type") == "TOOL_EXECUTION"]
    final_answers = [l for l in logs if l.get("action_type") == "FINAL_ANSWER"]
    
    if not final_answers:
        return False, "Thiếu bước xuất Final Answer."
        
    if tc_id == "TC01":
        # Không được gọi bất kỳ Tool nào
        if len(tool_calls) == 0 and final_answers[0].get("output"):
            return True, "Trả lời trực tiếp từ System Prompt/Kiến thức chung, không kích hoạt Tool."
        return False, f"TC01 yêu cầu không gọi Tool nhưng đã kích hoạt {len(tool_calls)} Tool."
        
    elif tc_id == "TC02":
        # Phải gọi academic_query với SV2026001
        if len(tool_calls) >= 1:
            first_call = tool_calls[0]
            if first_call.get("tool_name") == "academic_query" and first_call.get("arguments", {}).get("student_id") == "SV2026001":
                if first_call.get("observation", {}).get("status") == "SUCCESS":
                    return True, "Gọi đúng 'academic_query' với SV2026001 và nhận dữ liệu thành công."
        return False, "Không gọi đúng tool 'academic_query' hoặc sai mã sinh viên SV2026001."
        
    elif tc_id == "TC03":
        # Phải gọi schedule_appointment với SV2026001 và ngày 15/09/2026
        for call in tool_calls:
            if call.get("tool_name") == "schedule_appointment":
                args = call.get("arguments", {})
                if args.get("student_id") == "SV2026001" and "15/09/2026" in str(args.get("datetime_str", "")):
                    if call.get("observation", {}).get("status") == "SUCCESS":
                        return True, "Gọi đúng 'schedule_appointment' cho SV2026001 vào 14:00 15/09/2026."
        return False, "Không gọi đúng 'schedule_appointment' hoặc sai thời gian 14:00 15/09/2026."
        
    elif tc_id == "TC04":
        # Chuỗi ReAct đa bước: academic_query -> schedule_appointment (với 09:00 20/09/2026)
        names = [c.get("tool_name") for c in tool_calls]
        if "academic_query" in names and "schedule_appointment" in names:
            sched_call = next(c for c in tool_calls if c.get("tool_name") == "schedule_appointment")
            args = sched_call.get("arguments", {})
            if "20/09/2026" in str(args.get("datetime_str", "")) and "Nguyễn Văn A" in str(args.get("advisor_name", "")):
                return True, "Thực hiện chuỗi ReAct đa bước chuẩn xác (Tra cứu cố vấn -> Đặt lịch đúng 09:00 20/09/2026)."
        return False, "Chưa thực hiện đủ chuỗi đa bước (Tra cứu cố vấn -> Đặt lịch 09:00 20/09/2026)."
        
    elif tc_id == "TC05":
        # Phải gọi academic_query với SV9999999 và nhận NOT_FOUND
        for call in tool_calls:
            if call.get("tool_name") == "academic_query" and call.get("arguments", {}).get("student_id") == "SV9999999":
                if call.get("observation", {}).get("status") == "NOT_FOUND":
                    return True, "Tra cứu đúng mã SV9999999 và xử lý chuẩn kết quả NOT_FOUND từ Tool."
        return False, "Không gọi academic_query với đúng mã SV9999999 hoặc không nhận diện NOT_FOUND."
        
    return True, "Hoàn tất xử lý ReAct."


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        passed_count = 0
        todo_count = 0
        all_traces = []
        test_eval_results = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
                # Đánh giá đúng/sai theo tiêu chí kiểm thử
                is_pass, reason = verify_test_case(tc, logs)
                if is_pass:
                    passed_count += 1
                    test_eval_results.append(f"  ✅ [{tc['id']} - PASS]: {reason}")
                    print(f"🎯 [KẾT QUẢ ĐÁNH GIÁ]: PASS — {reason}")
                else:
                    test_eval_results.append(f"  ❌ [{tc['id']} - FAIL]: {reason}")
                    print(f"⚠️ [KẾT QUẢ ĐÁNH GIÁ]: FAIL — {reason}")
                    
                if completed_count < len(tests):
                    print("⏳ Đang chờ 10s giữa các test cases để tuân thủ Rate Limit của Gemini API Free Tier...")
                    time.sleep(10)
                
        print(f"\n==================================================")
        print(f"📋 BÁO CÁO NGHIỆM THU KIỂM THỬ (TEST ASSERTIONS REPORT):")
        for res in test_eval_results:
            print(res)
        print(f"\n📊 [KẾT QUẢ TEST SUITE]: {passed_count}/{len(tests)} PASSED ({round(passed_count/len(tests)*100)}%) | {completed_count}/{len(tests)} Đã thực thi | {todo_count} TODO")
        if passed_count == len(tests):
            print("🏆 [NGHIỆM THU XUẤT SẮC 100%]: Toàn bộ 5/5 Test Cases đã vượt qua kiểm tra logic và hành vi kỳ vọng!")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
