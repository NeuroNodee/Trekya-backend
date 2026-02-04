from typing import Optional
from langgraph.graph import StateGraph, END
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .llm import llm
from .rag import retriever
from .tools import (
    wikipedia_tool,
    tavily_search,
    weather_tool,
    nepali_news_tool,
)
from .models import FavoriteDestination


# =========================
# STATE
# =========================
class AgentState(MessagesState):
    intent: str
    user_name: Optional[str] = None


# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_TREKKA = SystemMessage(
    content=(
        "You are Trekka, a friendly and professional AI travel assistant specialized in Nepal. "
        "You maintain a natural conversational flow and remember previous messages. "
        "Do not reintroduce yourself unless the user explicitly asks who you are. "
        "Respond warmly, clearly, and professionally. "
        "If the user refers to earlier parts of the conversation, respond consistently. "
        "Do NOT use Markdown formatting such as **bold**, *italic*, or any special symbols. "
        "When listing items or instructions, always use numbered points like: "
        "1) First point\n2) Second point\n3) Third point, and so on. "
        "Always respond in plain, readable text suitable for chat display."
    )
)



# =========================
# INTENT NODE
# =========================
def intent_node(state: AgentState):
    text = state["messages"][-1].content.lower()

    if "save" in text:
        state["intent"] = "save"
    elif "weather" in text:
        state["intent"] = "weather"
    elif "news" in text:
        state["intent"] = "nepali_news"
    elif "wikipedia" in text:
        state["intent"] = "wiki"
    elif "search" in text:
        state["intent"] = "tavily"
    elif any(k in text for k in ["local information"]):
        state["intent"] = "rag"
    else:
        state["intent"] = "chat"

        # Debugging
    print(f"[DEBUG] User text: {text} -> Intent: {state['intent']}")

    return state


# =========================
# CHAT NODE
# =========================
def chat_node(state: AgentState):
    print("[DEBUG] Entering CHAT node")
    response = llm.invoke(state["messages"])
    state["messages"].append(response)
    return state


# =========================
# RAG NODE
# =========================
def rag_node(state: AgentState):
    print("[DEBUG] Entering rag node")
    query = state["messages"][-1].content
    docs = retriever.invoke(query)

    context = "\n\n".join(d.page_content for d in docs)

    response = llm.invoke(
        state["messages"] + [
            SystemMessage(content="Use the context below to answer naturally."),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion:\n{query}")
        ]
    )

    state["messages"].append(response)
    return state


# =========================
# WIKI NODE
# =========================
def wiki_node(state: AgentState):
    print("[DEBUG] Entering wiki node")
    query = state["messages"][-1].content
    result = wikipedia_tool(query)
    state["messages"].append(AIMessage(content=result))
    return state


# =========================
# SEARCH NODE
# =========================
def tavily_node(state: AgentState):
    print("[DEBUG] Entering tavily node")
    query = state["messages"][-1].content
    result = tavily_search(query)
    state["messages"].append(AIMessage(content=result))
    return state


# =========================
# WEATHER NODE
# =========================
def weather_node(state):
    print("[DEBUG] Entering weather node")
    user_text = state["messages"][-1].content
    weather_result = weather_tool(user_text, days=3)

    # Handle errors
    if isinstance(weather_result, dict) and "error" in weather_result:
        state["messages"].append(AIMessage(content=f"Sorry, {weather_result['error']}"))
        return state

    # If forecast is long, summarize using LLM with plain text instructions
    if len(weather_result.splitlines()) > 3:
        summary_prompt = f"Rephrase this weather forecast naturally and clearly in plain text, suitable for chat. Do NOT add any quotes:\n{weather_result}"

        summary = llm.invoke([HumanMessage(content=summary_prompt)])
        state["messages"].append(summary)
    else:
        state["messages"].append(AIMessage(content=weather_result))

    return state

# =========================
# NEWS NODE
# =========================
def nepali_news_node(state: AgentState):
    print("[DEBUG] Entering nepali news node")
    articles = nepali_news_tool(state["messages"][-1].content)

    if not articles:
        state["messages"].append(
            AIMessage(content="I couldn’t find recent Nepali news right now.")
        )
        return state

    response = llm.invoke(
        state["messages"] + [
            HumanMessage(content=f"Summarize these news articles clearly:\n{articles}")
        ]
    )

    state["messages"].append(response)
    return state


# =========================
# SAVE NODE
# =========================
def save_node(state: AgentState):
    print("[DEBUG] Entering save node")
    text = state["messages"][-1].content
    destination = text.replace("save", "").strip()

    FavoriteDestination.objects.create(
        name=state.get("user_name") or "User",
        destination=destination
    )

    state["messages"].append(
        AIMessage(content="Got it! I’ve saved that destination for you.")
    )
    return state





# =========================
# GRAPH
# =========================
graph = StateGraph(AgentState)

graph.add_node("intent", intent_node)
graph.add_node("chat", chat_node)
graph.add_node("rag", rag_node)
graph.add_node("wiki", wiki_node)
graph.add_node("tavily", tavily_node)
graph.add_node("weather", weather_node)
graph.add_node("nepali_news", nepali_news_node)
graph.add_node("save", save_node)

graph.set_entry_point("intent")

graph.add_conditional_edges(
    "intent",
    lambda s: s["intent"],
    {
        "chat": "chat",
        "rag": "rag",
        "wiki": "wiki",
        "tavily": "tavily",
        "weather": "weather",
        "nepali_news": "nepali_news",
        "save": "save",
    }
)

for node in [
    "chat",
    "rag",
    "wiki",
    "tavily",
    "weather",
    "nepali_news",
    "save",
]:
    graph.add_edge(node, END)

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)
