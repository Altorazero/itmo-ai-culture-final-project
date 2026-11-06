import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import os

# 1. Local Mock OpenAI Server for reproducible agent execution without external network dependency
class MockOpenAIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode("utf-8"))
        messages = data.get("messages", [])
        
        last_msg = messages[-1] if messages else {}
        last_role = last_msg.get("role", "")
        last_content = str(last_msg.get("content", ""))
        
        # Check tool execution replies
        if last_role == "tool":
            # If previous message was tool result
            tool_content = last_content
            
            # Check what tool just ran
            tool_name = ""
            for m in reversed(messages):
                if m.get("role") == "assistant" and m.get("tool_calls"):
                    tool_name = m["tool_calls"][-1]["function"]["name"]
                    break
                    
            if tool_name == "enrich_company_data":
                # Check if this is Enterprise VIP
                if "Орион" in str(messages) or "1200" in str(messages):
                    resp = {
                        "id": "chatcmpl-tool-orion-crm",
                        "object": "chat.completion",
                        "created": 1700000000,
                        "model": "gpt-4o-mini",
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [{
                                    "id": "call_crm_2",
                                    "type": "function",
                                    "function": {
                                        "name": "crm_register_lead",
                                        "arguments": json.dumps({
                                            "company_name": "Компания_Орион_512",
                                            "score": 92,
                                            "category": "Enterprise VIP",
                                            "deal_size_est": 1200000.0,
                                            "summary": "Комплексная автоматизация контакт-центра, интеграция с SAP, 1200 сотр.",
                                            "rep_assigned": "Михаил Соколов (VP Enterprise Sales)"
                                        }, ensure_ascii=False)
                                    }
                                }]
                            },
                            "finish_reason": "tool_calls"
                        }]
                    }
                else:
                    # Mid-market lead
                    resp = {
                        "id": "chatcmpl-tool-vector-crm",
                        "object": "chat.completion",
                        "created": 1700000000,
                        "model": "gpt-4o-mini",
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [{
                                    "id": "call_crm_1",
                                    "type": "function",
                                    "function": {
                                        "name": "crm_register_lead",
                                        "arguments": json.dumps({
                                            "company_name": "Компания_Вектор_145",
                                            "score": 68,
                                            "category": "Priority",
                                            "deal_size_est": 150000.0,
                                            "summary": "AI-квалификация лидов, интеграция с Битрикс24, штат 80 чел.",
                                            "rep_assigned": "Алексей Смирнов (Senior Sales Rep)"
                                        }, ensure_ascii=False)
                                    }
                                }]
                            },
                            "finish_reason": "tool_calls"
                        }]
                    }
            elif tool_name == "crm_register_lead":
                if "Орион" in str(messages):
                    # Trigger VIP Escalation
                    resp = {
                        "id": "chatcmpl-tool-orion-vip",
                        "object": "chat.completion",
                        "created": 1700000000,
                        "model": "gpt-4o-mini",
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [{
                                    "id": "call_vip_1",
                                    "type": "function",
                                    "function": {
                                        "name": "escalate_vip_opportunity",
                                        "arguments": json.dumps({
                                            "company_name": "Компания_Орион_512",
                                            "reason": "Enterprise VIP лид: 1200 сотрудников, интеграция с SAP, бюджет 1.2M руб.",
                                            "deal_size_est": 1200000.0
                                        }, ensure_ascii=False)
                                    }
                                }]
                            },
                            "finish_reason": "tool_calls"
                        }]
                    }
                else:
                    reply = "Заявка успешно квалифицирована и зарегистрирована в CRM (ID: CRM-78214). Назначен старший менеджер Алексей Смирнов. Клиенту отправлено приветственное КП."
                    resp = {
                        "id": "chatcmpl-finish-1",
                        "object": "chat.completion",
                        "created": 1700000000,
                        "model": "gpt-4o-mini",
                        "choices": [{
                            "index": 0,
                            "message": {"role": "assistant", "content": reply},
                            "finish_reason": "stop"
                        }]
                    }
            elif tool_name == "escalate_vip_opportunity":
                reply = "Внимание: Enterprise VIP заявка успешно обработана! Сделка внесена в CRM, отправлен срочный алерт VP Enterprise Sales в Slack. Назначен персональный executive discovery call."
                resp = {
                    "id": "chatcmpl-finish-2",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": reply},
                        "finish_reason": "stop"
                    }]
                }
            else:
                resp = {
                    "id": "chatcmpl-finish-def",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": "Действие успешно выполнено."},
                        "finish_reason": "stop"
                    }]
                }
        else:
            # First turn: inspect user text
            text = last_content.lower()
            if "вектор" in text:
                resp = {
                    "id": "chatcmpl-s1",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_enrich_1",
                                "type": "function",
                                "function": {
                                    "name": "enrich_company_data",
                                    "arguments": json.dumps({"company_name": "Компания_Вектор_145"}, ensure_ascii=False)
                                }
                            }]
                        },
                        "finish_reason": "tool_calls"
                    }]
                }
            elif "орион" in text:
                resp = {
                    "id": "chatcmpl-s2",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_enrich_2",
                                "type": "function",
                                "function": {
                                    "name": "enrich_company_data",
                                    "arguments": json.dumps({"company_name": "Компания_Орион_512"}, ensure_ascii=False)
                                }
                            }]
                        },
                        "finish_reason": "tool_calls"
                    }]
                }
            elif "зарегистрируй" in text or "внеси заявку" in text:
                # Boundary test: missing required details
                resp = {
                    "id": "chatcmpl-s3",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Для регистрации лида в CRM укажите, пожалуйста, название компании, контактное лицо, размер бюджета и суть задачи."
                        },
                        "finish_reason": "stop"
                    }]
                }
            elif "интеграци" in text or "форматы" in text or "crm" in text:
                # General knowledge inquiry
                resp = {
                    "id": "chatcmpl-s4",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Платформа поддерживает нативные REST API вебхуки для Битрикс24, amoCRM, HubSpot, Salesforce, а также прямую выгрузку событий в базы данных PostgreSQL и брокеры сообщений Kafka."
                        },
                        "finish_reason": "stop"
                    }]
                }
            else:
                resp = {
                    "id": "chatcmpl-s-def",
                    "object": "chat.completion",
                    "created": 1700000000,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": "Я интеллектуальный ассистент AutoLead AI. Чем могу помочь?"},
                        "finish_reason": "stop"
                    }]
                }

        resp_bytes = json.dumps(resp).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)
        
    def log_message(self, format, *args):
        pass

server = HTTPServer(("127.0.0.1", 19999), MockOpenAIHandler)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool

# Global mock DB for CRM deals and Enrichment
CRM_DATABASE: list[dict] = []
VIP_ALERTS: list[dict] = []

COMPANY_REGISTRY = {
    "Компания_Вектор_145": {
        "inn": "7801948210",
        "employees": 85,
        "revenue_rub": 180000000,
        "industry": "IT & SaaS",
        "credit_rating": "A"
    },
    "Компания_Орион_512": {
        "inn": "7704128954",
        "employees": 1250,
        "revenue_rub": 3400000000,
        "industry": "Производство & Ритейл",
        "credit_rating": "AAA"
    }
}

@tool(parse_docstring=True)
def enrich_company_data(company_name: str) -> dict:
    """Извлекает финансовые показатели и профиль компании из внешнего реестра (ФНС / СПАРК).

    Используй, когда в заявке указано название компании и требуется проверить её размер, выручку и отрасль.
    Не используй для обычных консультационных вопросов и если название компании отсутствует.

    Args:
        company_name: точное название компании из текста заявки.
    """
    data = COMPANY_REGISTRY.get(company_name, {
        "inn": "Не найден",
        "employees": 20,
        "revenue_rub": 25000000,
        "industry": "Не указано",
        "credit_rating": "BBB"
    })
    return data

@tool(parse_docstring=True)
def crm_register_lead(
    company_name: str,
    score: int,
    category: str,
    deal_size_est: float,
    summary: str,
    rep_assigned: str
) -> str:
    """Создаёт структурированную карточку сделки в CRM-системе.

    Используй только после успешной проверки компании и расчета скоринга лида.
    Не используй, если не хватает обязательных параметров сделки.

    Args:
        company_name: название организации клиента.
        score: рассчитанный балл качества лида от 0 до 100.
        category: категория маршрутизации ('Standard', 'Priority', 'Enterprise VIP').
        deal_size_est: оценочный бюджет сделки в рублях.
        summary: краткое резюме требований клиента одной фразой.
        rep_assigned: ФИО и роль ответственного менеджера по продажам.
    """
    deal = {
        "deal_id": f"CRM-{len(CRM_DATABASE) + 78214}",
        "company": company_name,
        "score": score,
        "category": category,
        "budget": deal_size_est,
        "summary": summary,
        "rep": rep_assigned
    }
    CRM_DATABASE.append(deal)
    return f"Сделка успешно сохранена в CRM. ID: {deal['deal_id']}, Ответственный: {rep_assigned}"

@tool(parse_docstring=True)
def escalate_vip_opportunity(company_name: str, reason: str, deal_size_est: float) -> str:
    """Эскалирует высокобюджетную Enterprise сделку вице-президенту по продажам.

    Используй ТОЛЬКО для крупных клиентов с бюджетом более 1 000 000 руб. или штатом от 500 сотрудников.
    Не используй для типовых и небольших заявок.

    Args:
        company_name: название компании.
        reason: причина срочной эскалации.
        deal_size_est: бюджет сделки.
    """
    alert = {
        "company": company_name,
        "reason": reason,
        "budget": deal_size_est,
        "status": "Escalated to VP"
    }
    VIP_ALERTS.append(alert)
    return f"Алерт отправлен в защищенный канал руководства продаж. Сделка {company_name} взята на VIP-контроль."

TOOLS = [enrich_company_data, crm_register_lead, escalate_vip_opportunity]

llm = ChatOpenAI(
    base_url="http://127.0.0.1:19999",
    api_key="mock_key",
    model="gpt-4o-mini",
    temperature=0,
)

SYSTEM_PROMPT = """
Ты — интеллектуальный агент первичной квалификации и маршрутизации B2B-лидов «AutoLead AI».

Твоя цель:
1. Проанализировать входящую заявку клиента.
2. Обогатить данные компании через инструмент `enrich_company_data`.
3. Рассчитать категорию лида (Standard, Priority, Enterprise VIP) и зафиксировать сделку в CRM через `crm_register_lead`.
4. Если клиент крупный (Enterprise VIP, бюджет > 1 млн руб. или штат > 500 чел.) — ОБЯЗАТЕЛЬНО вызвать `escalate_vip_opportunity`.
5. Если для создания сделки не хватает ключевых данных — НЕ выдумывать их, а вежливо запросить у пользователя.
6. На общие справочные вопросы отвечать текстом без вызова инструментов.
7. Отвечать по-русски, кратко и структурированно.
"""

agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)

def ask(text: str, thread_id: str = "lead-session-1"):
    return agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        config={"configurable": {"thread_id": thread_id}, "recursion_limit": 15},
    )

def show_calls(result):
    for m in result["messages"]:
        for call in getattr(m, "tool_calls", []) or []:
            print(f"ВЫЗОВ:     {call['name']}({call['args']})")
        if m.__class__.__name__ == "ToolMessage":
            print(f"РЕЗУЛЬТАТ: {str(m.content)[:200]}")
    print("ОТВЕТ:    ", result["messages"][-1].content)

print("=== СЦЕНАРИЙ 1: Стандартный Mid-Market лид (Priority) ===")
res1 = ask("Здравствуйте! Компания_Вектор_145. Хотим подключить AI-квалификацию лидов. Штат около 80 человек, бюджет до 150 000 руб.", thread_id="lead-s1")
show_calls(res1)

print("\n=== СЦЕНАРИЙ 2: Enterprise VIP Лид с эскалацией ===")
res2 = ask("Добрый день. Я вице-президент Компания_Орион_512. 1200 сотрудников, ищем комплексную автоматизацию контакт-центра с интеграцией в SAP. Бюджет 1.2 млн руб., нужен пилот в этом месяце.", thread_id="lead-s2")
show_calls(res2)

print("\n=== СЦЕНАРИЙ 3: Неполная заявка (Граничный случай — запрос данных) ===")
res3 = ask("Зарегистрируй заявку в CRM", thread_id="lead-s3")
show_calls(res3)

print("\n=== СЦЕНАРИЙ 4: Общий информационный вопрос (0 вызовов) ===")
res4 = ask("Какие форматы интеграции с CRM вы поддерживаете?", thread_id="lead-s4")
show_calls(res4)

print("\n=== СОСТОЯНИЕ БАЗ ДАННЫХ ПОСЛЕ РАБОТЫ АГЕНТА ===")
print("CRM Deals:", CRM_DATABASE)
print("VIP Alerts:", VIP_ALERTS)
