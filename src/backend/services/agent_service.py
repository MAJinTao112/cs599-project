import asyncio
import json
import os
import sys
import tempfile
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*LangChainDeprecationWarning.*")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTIC_RAG_ROOT = PROJECT_ROOT / "aggentic_RAG"
if str(AGENTIC_RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTIC_RAG_ROOT))

load_dotenv(dotenv_path=AGENTIC_RAG_ROOT / ".env", override=True)

asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
_mcp_loop = asyncio.new_event_loop()
_mcp_manager = None


def detect_multi_destination(user_query: str, extraction: dict) -> dict:
    roundtrip_keywords = ["往返", "来回", "回程", "返程", "返回"]
    if any(kw in user_query for kw in roundtrip_keywords):
        return {
            "is_multi_destination": False,
            "detected_keywords": [],
            "raw_destination_text": extraction.get("destination", ""),
            "detection_method": "roundtrip_excluded",
        }

    multi_dest_keywords = [
        "再去",
        "然后去",
        "接着去",
        "顺便去",
        "再到",
        "然后到",
        "接着到",
        "再去看看",
        "再看看",
        "之后去",
        "之后到",
    ]
    detected_keywords = [kw for kw in multi_dest_keywords if kw in user_query]
    if detected_keywords:
        return {
            "is_multi_destination": True,
            "detected_keywords": detected_keywords,
            "raw_destination_text": extraction.get("destination", ""),
            "detection_method": "keyword",
        }

    destination = extraction.get("destination", "") or ""
    origin = extraction.get("origin", "") or ""
    norm = destination.replace(",", "，").replace("、", "，").replace("和", "，")
    cities = [c.strip() for c in norm.split("，") if c.strip()]
    unique_cities = []
    for city in cities:
        if city not in unique_cities:
            unique_cities.append(city)

    if len(unique_cities) >= 3:
        return {
            "is_multi_destination": True,
            "detected_keywords": [],
            "raw_destination_text": destination,
            "detection_method": "comma_separated_3plus",
        }

    if len(unique_cities) == 2:
        if origin and origin in unique_cities:
            return {
                "is_multi_destination": False,
                "detected_keywords": [],
                "raw_destination_text": destination,
                "detection_method": "origin_pair_excluded",
            }
        return {
            "is_multi_destination": True,
            "detected_keywords": [],
            "raw_destination_text": destination,
            "detection_method": "comma_separated_2",
        }

    return {
        "is_multi_destination": False,
        "detected_keywords": [],
        "raw_destination_text": destination,
    }


class AgentService:
    def __init__(self) -> None:
        self.retriever = None
        self.last_uploaded_files: List[str] = []
        self.rag_stats: Dict[str, Any] = {"total": 0, "sources": []}
        self._llm: Optional[ChatOpenAI] = None
        self._tools: List[Tool] = []
        self._tools_loaded = False
        self.mcp_available = False

    def get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="qwen-plus",
                openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
                openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                temperature=0.7,
            )
        return self._llm

    def pre_analyze_query(self, user_query: str) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        extraction_prompt = f"""You are a travel planning assistant. Today's date is {today}.

Your task: Extract key information from the user query and determine if it needs deep analysis.

RULES:
- Output ONLY valid JSON. NO explanations, NO markdown code blocks.
- Date conversion: "今天"/"today" = {today}, "明天"/"tomorrow" = +1 day, etc.
- Use Chinese for city names.
- Set "needs_deep_analysis" to true if:
  * Complex multi-city routes (e.g., "A和B", "A再去B")
  * Budget optimization needed (tight budget with many requirements)
  * Multiple conflicting constraints (e.g., elderly + children, limited time + many places)
  * Special needs: 老人, 小孩, 儿童, 亲子, 残疾, etc.

Output this exact JSON structure:
{{
  "destination": "extracted destination city or cities (comma separated if multiple)",
  "origin": "extracted origin city",
  "travel_days": 0,
  "budget": 0,
  "travel_date": "YYYY-MM-DD",
  "preferences": ["preference1"],
  "needs_deep_analysis": false,
  "has_special_needs": false
}}

User query: {user_query}
"""
        try:
            response = self.get_llm().invoke(extraction_prompt)
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                if content.startswith("json"):
                    content = content[4:]
            extraction = json.loads(content)
        except Exception:
            extraction = {
                "destination": "",
                "origin": "",
                "travel_days": 0,
                "budget": 0,
                "travel_date": "",
                "preferences": [],
                "needs_deep_analysis": False,
                "has_special_needs": False,
            }

        multi_dest_info = detect_multi_destination(user_query, extraction)
        if multi_dest_info.get("is_multi_destination", False):
            scenario_type = "multi_destination"
            needs_r1 = True
        elif extraction.get("needs_deep_analysis", False) or extraction.get("has_special_needs", False):
            scenario_type = "complex"
            needs_r1 = True
        else:
            scenario_type = "simple"
            needs_r1 = False

        return {
            "scenario_type": scenario_type,
            "needs_deep_analysis": needs_r1,
            "extraction": extraction,
            "multi_dest_info": multi_dest_info,
        }

    def get_mcp_manager_sync(self):
        global _mcp_manager
        if _mcp_manager is None:
            from aggentic_RAG.travel_agent.tools.mcp_tools import MCPToolManager

            _mcp_manager = MCPToolManager()
            _mcp_loop.run_until_complete(_mcp_manager.initialize())
        return _mcp_manager

    def call_mcp_tool_sync(self, server_name: str, tool_name: str, **kwargs) -> str:
        manager = self.get_mcp_manager_sync()
        return _mcp_loop.run_until_complete(manager.call_tool(server_name, tool_name, **kwargs))

    def index_documents(self, files: Iterable[tuple[str, bytes]]) -> Dict[str, Any]:
        from aggentic_RAG.travel_agent.tools.rag_tool import get_rag_instance

        loaded_files: List[str] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for filename, content in files:
                suffix = Path(filename).suffix.lower()
                if suffix not in [".txt", ".md", ".pdf", ".csv"]:
                    continue
                safe_name = Path(filename).name
                temp_path = Path(temp_dir) / safe_name
                temp_path.write_bytes(content)
                loaded_files.append(filename)

            if not loaded_files:
                return {"uploaded": 0, "files": [], "message": "没有可索引的文档"}

            rag = get_rag_instance()
            rag.build_knowledge_base(temp_dir, file_type="directory", force_recreate=False)

        rag = get_rag_instance()
        self.retriever = rag.retriever
        self.last_uploaded_files = loaded_files
        self.rag_stats = rag.get_stats()
        self._tools_loaded = False
        return {
            "uploaded": len(loaded_files),
            "files": loaded_files,
            "message": f"已加载 {len(loaded_files)} 个文档",
        }

    def create_tools(self) -> List[Tool]:
        if self._tools_loaded:
            return self._tools

        from aggentic_RAG.travel_agent.tools.tool_registry import AVAILABLE_TOOLS

        tools: List[Tool] = []
        if self.retriever is not None:
            tools.append(
                create_retriever_tool(
                    retriever=self.retriever,
                    name="rag_search",
                    description="用于查询旅游攻略、景点信息、美食推荐等。输入城市名或景点名。",
                )
            )

        try:
            self.get_mcp_manager_sync()
            self.mcp_available = True
        except Exception:
            self.mcp_available = False

        def query_train_tickets(origin: str, destination: str, date: str) -> str:
            try:
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    if date_obj.year < datetime.now().year:
                        date = date.replace(str(date_obj.year), str(datetime.now().year))
                except Exception:
                    pass

                from_code = None
                to_code = None
                for city, is_origin in [(origin, True), (destination, False)]:
                    try:
                        codes_result = self.call_mcp_tool_sync(
                            "12306 Server",
                            "get-stations-code-in-city",
                            city=city,
                        )
                        if codes_result and "error" not in str(codes_result).lower():
                            codes_data = json.loads(codes_result) if isinstance(codes_result, str) else codes_result
                            if isinstance(codes_data, list):
                                chosen_code = None
                                for station in codes_data:
                                    name = station.get("station_name", "")
                                    if name == city:
                                        chosen_code = station.get("station_code") or station.get("code") or station.get("telecode")
                                        break
                                if not chosen_code:
                                    for station in codes_data:
                                        name = station.get("station_name", "")
                                        if city in name:
                                            chosen_code = station.get("station_code") or station.get("code") or station.get("telecode")
                                            break
                                if chosen_code and is_origin:
                                    from_code = chosen_code
                                elif chosen_code:
                                    to_code = chosen_code
                    except Exception:
                        continue

                if from_code and to_code:
                    train_result = self.call_mcp_tool_sync(
                        "12306 Server",
                        "get-tickets",
                        fromStation=from_code,
                        toStation=to_code,
                        date=date,
                    )
                else:
                    train_result = self.call_mcp_tool_sync(
                        "12306 Server",
                        "get-tickets",
                        fromStation=origin,
                        toStation=destination,
                        date=date,
                    )

                driving_result = None
                try:
                    origin_coords = self._lookup_coords(origin)
                    dest_coords = self._lookup_coords(destination)
                    if origin_coords and dest_coords:
                        driving_result = self.call_mcp_tool_sync(
                            "Gaode Server",
                            "maps_direction_driving",
                            origin=origin_coords,
                            destination=dest_coords,
                        )
                except Exception:
                    driving_result = None

                combined: Dict[str, Any] = {"train": train_result}
                if driving_result:
                    combined["driving"] = driving_result
                return json.dumps(combined, ensure_ascii=False)
            except Exception as exc:
                return f"交通查询失败: {exc}"

        for tool_def in AVAILABLE_TOOLS:
            if tool_def.tool_type == "mcp":
                if tool_def.name == "train_query":
                    def train_tool_func(tool_input: str) -> str:
                        try:
                            if not tool_input.strip().startswith("{"):
                                return "请提供JSON格式的参数"
                            kwargs = json.loads(tool_input)
                            origin = kwargs.get("origin") or kwargs.get("from") or kwargs.get("fromStation", "")
                            destination = kwargs.get("destination") or kwargs.get("to") or kwargs.get("toStation", "")
                            date = kwargs.get("date", "")
                            return query_train_tickets(origin, destination, date)
                        except Exception as exc:
                            return f"参数解析失败: {exc}"

                    tools.append(Tool(name=tool_def.name, description=tool_def.description, func=train_tool_func))
                    continue

                def make_sync_tool(server_name: str, mcp_tool_name: str, tool_name: str):
                    def call_tool(tool_input: str) -> str:
                        try:
                            kwargs = json.loads(tool_input) if tool_input.strip().startswith("{") else {"query": tool_input.strip()}
                            kwargs = self._normalize_tool_kwargs(tool_name, kwargs)
                            return self.call_mcp_tool_sync(server_name, mcp_tool_name, **kwargs)
                        except json.JSONDecodeError:
                            kwargs = self._normalize_tool_kwargs(tool_name, {"query": tool_input.strip()})
                            return self.call_mcp_tool_sync(server_name, mcp_tool_name, **kwargs)
                        except Exception as exc:
                            return f"工具调用失败: {exc}"

                    return call_tool

                tools.append(
                    Tool(
                        name=tool_def.name,
                        description=tool_def.description,
                        func=make_sync_tool(tool_def.server_name or "", tool_def.mcp_tool_name or "", tool_def.name),
                    )
                )

            elif tool_def.tool_type == "r1":
                tools.append(Tool(name=tool_def.name, description=tool_def.description, func=self._call_r1_analysis))

        self._tools = tools
        self._tools_loaded = True
        return tools

    def _lookup_coords(self, city: str) -> Optional[str]:
        geo = self.call_mcp_tool_sync("Gaode Server", "maps_geo", address=city)
        geo_data = json.loads(geo) if isinstance(geo, str) else geo
        if isinstance(geo_data, dict) and isinstance(geo_data.get("return"), list) and geo_data["return"]:
            return geo_data["return"][0].get("location")
        return None

    def _normalize_tool_kwargs(self, tool_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if "date" in kwargs:
            try:
                date_obj = datetime.strptime(str(kwargs["date"]).strip(), "%Y-%m-%d")
                if date_obj.year < datetime.now().year:
                    kwargs["date"] = str(kwargs["date"]).replace(str(date_obj.year), str(datetime.now().year))
            except Exception:
                pass

        if tool_name == "lucky_day":
            date_val = kwargs.pop("date", None) or kwargs.pop("query", "")
            return {"solarDatetime": f"{str(date_val).strip()}T12:00:00+08:00"}
        if tool_name == "flight_query":
            return {
                "dep": kwargs.pop("dep", None) or kwargs.pop("from", None) or kwargs.pop("origin", ""),
                "arr": kwargs.pop("arr", None) or kwargs.pop("to", None) or kwargs.pop("destination", ""),
                "date": kwargs.pop("date", ""),
            }
        if tool_name == "gaode_weather":
            city = kwargs.pop("city", None) or kwargs.pop("location", None) or kwargs.pop("query", "")
            return {"city": self._clean_city(city)}
        if tool_name == "gaode_geo":
            return {"address": kwargs.pop("address", None) or kwargs.pop("location", None) or kwargs.pop("query", "")}
        if tool_name == "gaode_hotel_search":
            keywords = kwargs.pop("keywords", None) or kwargs.pop("keyword", None) or kwargs.pop("query", "")
            city = kwargs.pop("city", None) or kwargs.pop("location", "")
            if keywords and "酒店" not in keywords and "民宿" not in keywords:
                keywords = f"{keywords} 酒店"
            return {"keywords": keywords, "city": city} if city else {"keywords": keywords}
        if tool_name == "gaode_poi_search":
            keywords = kwargs.pop("keywords", None) or kwargs.pop("keyword", None) or kwargs.pop("query", "")
            city = kwargs.pop("city", None) or kwargs.pop("location", "")
            return {"keywords": keywords, "city": city} if city else {"keywords": keywords}
        if tool_name == "gaode_driving":
            return {
                "origin": kwargs.pop("origin", None) or kwargs.pop("from", ""),
                "destination": kwargs.pop("destination", None) or kwargs.pop("to", ""),
            }
        return kwargs

    def _clean_city(self, value: Any) -> str:
        city = str(value or "").strip()
        for sep in [",", "，"]:
            if sep in city:
                city = city.split(sep)[0].strip()
        return city.replace("市", "")

    def _call_r1_analysis(self, tool_input: str) -> str:
        try:
            from aggentic_RAG.travel_agent.tools.r1_tool import get_r1_instance

            kwargs = json.loads(tool_input) if tool_input.strip().startswith("{") else {"problem": tool_input, "context": {}}
            if not os.getenv("DEEPSEEK_API_KEY", ""):
                return "深度分析不可用: 未配置 DEEPSEEK_API_KEY"

            problem = kwargs.get("problem", "")
            context = kwargs.get("context", {})
            return _mcp_loop.run_until_complete(get_r1_instance().analyze(problem, context))
        except Exception as exc:
            return f"深度分析暂时不可用: {exc}"

    def tool_status(self) -> Dict[str, Any]:
        tools = self.create_tools()
        return {
            "tools": [tool.name for tool in tools],
            "count": len(tools),
            "mcp_available": self.mcp_available,
            "uploaded_files": self.last_uploaded_files,
            "rag_total": int(self.rag_stats.get("total", 0) or 0),
        }

    def run_chat(
        self,
        message: str,
        messages: List[Dict[str, str]],
        max_iterations: int = 30,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        if status_callback:
            status_callback("正在分析您的旅行需求...")
        pre_analysis = self.pre_analyze_query(message)
        scenario_type = pre_analysis["scenario_type"]
        needs_r1 = pre_analysis["needs_deep_analysis"]

        if status_callback:
            if scenario_type == "multi_destination":
                status_callback("检测到多目的地行程，准备调用深度路线优化...")
            elif scenario_type == "complex":
                status_callback("检测到复杂约束，准备进行深度分析...")
            else:
                status_callback("已识别为常规旅行规划，准备调用工具...")

        tools = self.create_tools()
        prompt = self._build_prompt()
        agent = create_react_agent(self.get_llm(), tools, prompt)
        memory = self._build_memory(messages)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=max_iterations,
        )

        if needs_r1:
            if status_callback:
                status_callback("正在组织 R1 深度分析上下文...")
            extraction = pre_analysis["extraction"]
            agent_input = f"""用户查询: {message}

重要提示：系统检测到这是一个{'多目的地' if scenario_type == 'multi_destination' else '复杂'}场景。

请按以下顺序处理：
1. 首先调用 r1_analysis 进行深度路线规划和优化，输入应包含完整的用户需求
2. 然后根据 R1 的建议，调用其他工具查询具体信息（火车票、天气、酒店等）
3. 最后综合所有信息生成完整的旅行规划

已提取的信息：
- 目的地: {extraction.get('destination', '未知')}
- 出发地: {extraction.get('origin', '未知')}
- 旅行天数: {extraction.get('travel_days', 0)}
- 预算: {extraction.get('budget', 0)}元
- 出发日期: {extraction.get('travel_date', '未知')}
- 偏好: {extraction.get('preferences', [])}
"""
        else:
            agent_input = message

        if status_callback:
            status_callback("正在查询交通、天气、住宿和黄历信息...")
        response = executor.invoke({"input": agent_input}, config={})
        answer = response.get("output", "抱歉，我无法生成回答。")
        if status_callback:
            status_callback("旅行方案生成完成。")

        return {
            "answer": answer,
            "scenario_type": scenario_type,
            "needs_r1": bool(needs_r1),
            "extraction": pre_analysis.get("extraction", {}),
        }

    def _build_memory(self, messages: List[Dict[str, str]]) -> ConversationBufferMemory:
        memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history", output_key="output")
        for item in messages:
            role = item.get("role")
            content = item.get("content", "")
            if not content:
                continue
            if role == "user":
                memory.chat_memory.add_message(HumanMessage(content=content))
            elif role == "assistant":
                memory.chat_memory.add_message(AIMessage(content=content))
            elif role == "system":
                memory.chat_memory.add_message(SystemMessage(content=content))
        return memory

    def _build_prompt(self):
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_year = datetime.now().year
        instructions = f"""你是一个专业的旅游规划助手。当前日期是{current_date}。

完整旅行规划必须包含交通信息、天气预报、住宿推荐、黄历吉日；复杂行程需要调用 r1_analysis。
日期必须使用{current_year}年。每个工具可以针对不同参数调用多次。请用中文回答，提供详细完整的行程规划。"""

        template = """
{instructions}

TOOLS:
------
You have access to the following tools:
{tools}

To use a tool, you MUST strictly follow this EXACT format:

Thought: Do I need to use a tool? Yes
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a response to say to the Human, or if you do not need to use a tool, you MUST strictly follow this EXACT format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]

CRITICAL RULES:
1. For complete travel planning, you MUST call: train_query, gaode_weather, gaode_hotel_search, lucky_day
2. You CAN call the same tool multiple times with DIFFERENT parameters
3. NEVER call the same tool with the SAME parameters twice
4. If a tool returns an error, explain the error to the user and move on
5. For multi-city complex trips, call r1_analysis to optimize the route
6. Use Chinese to respond to users
7. Provide detailed and complete travel plans

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}"""
        return PromptTemplate.from_template(template).partial(instructions=instructions)


agent_service = AgentService()
