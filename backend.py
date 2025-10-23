from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os, openai

app = FastAPI()

# Allow your iPhone to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_KEY = os.environ.get("OPENAI_KEY")
client = openai.OpenAI(api_key=OPENAI_KEY)

BUDGET_EURO = 1.0
COST_PER_JOKE = 0.00001
used = 0

@app.get("/joke")
def get_joke():
    global used
    if used + COST_PER_JOKE > BUDGET_EURO:
        return {"joke": "Budget exceeded 😅"}
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a witty assistant who only tells short, funny jokes."},
            {"role": "user", "content": "Tell me a short joke."}
        ]
    )
    
    joke_text = response.choices[0].message.content
    used += COST_PER_JOKE
    return {"joke": joke_text}
