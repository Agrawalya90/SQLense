import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

from database import init_db, get_schema
from tools import tools, handle_tool_calls

load_dotenv(dotenv_path=".env", override=True)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)
MODEL = "openai/gpt-oss-120b"


init_db()
SCHEMA = get_schema()

SYSTEM_PROMPT = f"""
You are a helpful data analyst assistant for an Amazon product dataset.
You have access to a SQLite database with the following schema:

{SCHEMA}

Guidelines:
- Always use the execute_sql tool to answer data questions — never guess numbers.
- Write clean, efficient SQLite-compatible SELECT queries.
- After getting results, explain them in plain English.
- If a question is ambiguous, make a reasonable assumption and state it.
- Prices are in rupees — format them with the rupee symbol.
- The category column may contain pipe-separated subcategories e.g. "Electronics|Headphones".
  Use LIKE '%keyword%' to filter by category.
- If the user asks something unrelated to the data, politely redirect them.
"""

EXAMPLE_QUESTIONS = [
    "Which product category has the highest average rating?",
    "Show me the top 10 most discounted products.",
    "Which products have more than 10,000 ratings?",
    "What is the average discount percentage across all products?",
    "Show me all products with a rating above 4.5 and more than 5000 reviews.",
]



def chat(user_message, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    response = groq.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools
    )

    while response.choices[0].finish_reason == "tool_calls":
        msg = response.choices[0].message
        tool_responses = handle_tool_calls(msg)

        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id":   tc.id,
                    "type": tc.type,
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        })
        messages.extend(tool_responses)

        response = groq.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools
        )

    return response.choices[0].message.content



with gr.Blocks(title="Amazon Product Analyst") as demo:
    gr.Markdown("""
    # Amazon Product Data Analyst
    Ask questions about the product and review data in plain English.
    The assistant will write and run SQL queries automatically.
    """)

    gr.ChatInterface(
        fn=chat,
        type="messages",
        examples=EXAMPLE_QUESTIONS,
        chatbot=gr.Chatbot(height=500),
    )

    gr.Markdown("""
    **Database tables:** `products`, `reviews`
    Read-only — only SELECT queries are allowed.
    """)

demo.launch(theme=gr.themes.Soft())
