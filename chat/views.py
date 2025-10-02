from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SchemeQueryForm
from typing import Any, Dict, Iterable, List
import re
import os
from huggingface_hub import InferenceClient
import ollama
import markdown2
from pinecone import Pinecone
PINECONE_KEY = ''
os.environ["HUGGINGFACEHUB_API_TOKEN"] = ""
pc = Pinecone(api_key=PINECONE_KEY, environment="ap-south-1-aws")
index = pc.Index("")

# Key for storing conversation in session
SESSION_KEY = "chat_history"

def create_prompt(results) -> str:
        context = ""
        for match in results['matches']:
            context += match['metadata']['text'] + "\n---\n"
        return context.strip()

def generate_reply(user_message: str, history: List[Dict[str, str]]) -> str:
    """
    Generate reply using both Pinecone context and past conversation history.
    """
    msg = user_message.lower()
    if " hi " in msg:
        return "Hello! How can I help you today?"

    # Fetch relevant docs from Pinecone
    context = generate_context(msg)
    Ncontext = normalize_hits(context)
    doc_context = build_context(Ncontext)

    # Include last 5 turns of history
    conversation_context = ""
    for turn in history[-5:]:
        role = "User" if turn["role"] == "user" else "Bot"
        conversation_context += f"{role}: {turn['text']}\n"

    # Build the final prompt
    prompt = build_prompt(doc_context, msg, conversation_context)

    # Call model
    reply = generateOllamaReply(prompt)
    return reply

def home(request):
    """
    Landing page (home.html) – just shows the form once.
    """
    form = SchemeQueryForm()
    print("In home")
    if request.method == "POST":
        form = SchemeQueryForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"].strip()
            # Initialize session chat history if not present
            if SESSION_KEY not in request.session:
                request.session[SESSION_KEY] = []
            history = request.session[SESSION_KEY]
            history.append({"role": "user", "text": query})
            msg=generate_reply(query, history)
            msg_reply_html = markdown2.markdown(msg)
            history.append({"role": "bot", "text": msg_reply_html})
            request.session[SESSION_KEY] = history
            request.session.modified = True
            # After first message → go to chatStart.html
            return redirect(reverse("chat_view"))
    return render(request, "chat/home.html", {"form": form})

def chat_view(request):
    """
    Main chat interface (chatStart.html) shows history and input at bottom.
    """
    if SESSION_KEY not in request.session:
        request.session[SESSION_KEY] = []
    history = request.session[SESSION_KEY]

    form = SchemeQueryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        query = form.cleaned_data["query"].strip()
        if query:
            history.append({"role": "user", "text": query})
            bot_reply = generate_reply(query, history)
            bot_reply_html = markdown2.markdown(bot_reply)
            history.append({"role": "bot", "text": bot_reply_html})
            request.session[SESSION_KEY] = history
            request.session.modified = True
        return redirect(reverse("chat_view"))

    return render(request, "chat/chatStart.html", {
        "form": form,
        "history": history,
    })

def clear_chat(request):
    """
    Optional: clear the conversation and go back to chat_view.
    """
    request.session[SESSION_KEY] = []
    history = request.session[SESSION_KEY]
    request.session.modified = True
    return redirect(reverse("home"))


#-----------------------  Functions to to fetch context and normalize data   -----------------------
def normalize_hits(results):
    hits = (results.get("result") or {}).get("hits") or []
    norm = []
    for h in hits:
        fields = h.get("fields", {}) or {}
        raw_text = fields.get("chunk_text", "") or ""

        clean_text = re.sub(r"<.*?>", "", raw_text)
        norm.append({
            "id": h.get("_id"),
            "score": float(h.get("_score", 0.0) or 0.0),
            "text": fields.get("chunk_text", ""),
            "meta": {k: v for k, v in fields.items() if k != "chunk_text"},
        })
    return norm

def build_context(hits: List[Dict[str, Any]], top_k: int = 5) -> str:
    context_lines: List[str] = []
    for h in sorted(hits, key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]:
        cid = h.get("id") or "unknown-id"
        snippet = (h.get("text") or "").replace("\n", " ")
        context_lines.append(f"[{cid}] {snippet}")
    return "\n".join(context_lines)

def build_prompt(context: str, query: str, conversation: str = "") -> str:
    """
    Build final prompt with both Pinecone context and chat history.
    """
    prompt = f"""
You are a helpful AI assistant that explains Indian Government Schemes to citizens in a clear and structured way.

### Instructions:
- Use BOTH the provided scheme context and the past conversation to answer the question.
- Do **not** copy text word-for-word. Instead, **paraphrase and simplify** in your own words, but **do not oversimplify** to the point of losing important details.
- **Do not change or alter the meaning** of the retrieved context. Stay faithful to the factual information in the RAG content.
- Preserve all **numerical values (amounts in ₹, %, years, dates, counts, etc.) exactly as they appear in the context** without changing or rounding them.
- Organize the answer in **sections** with bullet points, steps, or short paragraphs.
- Highlight **scheme names** in bold.
- If info is missing, state: "Not available in the provided context."
- Do **not hallucinate** values, schemes, or details that are not present in the context.

---

### Past Conversation:
{conversation}

### Retrieved Scheme Context:
{context}

### Current Question:
{query}

### Answer:
"""
    return prompt


import json

def generate_context(query: str) -> dict:
    context = index.search(
        namespace="schemes-v1",
        query={
            "top_k": 20,
            "inputs": {
                "text": query
            }
        }
    )

    hits = context.get("result", {}).get("hits", [])
    filtered_hits = [hit for hit in hits if hit.get("_score", 0) >= 0.3]

    if not filtered_hits:
        print("⚠️ No hits above threshold (0.3) for query:", query)
        return {"result": {"hits": []}}

    # serializable_hits = [hit.to_dict() if hasattr(hit, "to_dict") else dict(hit) for hit in filtered_hits]
    # filename = f"filtered_hits_{query.replace(' ', '_')}.json"
    # with open(filename, "w", encoding="utf-8") as f:
    #     json.dump(serializable_hits, f, indent=2)

    return {"result": {"hits": filtered_hits}}

#-----------------------  Functions for Inteface Client   -----------------------

def generateLLMreply(prompt:str)-> str:
    client = InferenceClient(
        model="meta-llama/Llama-3.1-8B",
        token=os.environ["HUGGINGFACEHUB_API_TOKEN"]
    )

    result = client.text_generation(
        prompt,
        max_new_tokens=200,
        temperature=0.2,
        do_sample=True,
    )
    return result

def generateOllamaReply(prompt:str)-> str:
    client = ollama.Client()
    model = "llama3.1:8b"
    response = client.generate(model=model, prompt=prompt)
    return response.response