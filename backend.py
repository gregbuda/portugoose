from fastapi import FastAPI, Request
import os, openai, uuid
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer

# --- OpenAI setup ---
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_KEY)

# --- FastAPI app ---
app = FastAPI()

# --- SQLite database setup ---
DATABASE_URL = "sqlite:///./sessions.db"
database = Database(DATABASE_URL)
metadata = MetaData()

# Table to store sessions and jokes
jokes_table = Table(
    "jokes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("session_id", String),
    Column("joke_text", String),
)

engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

# --- Startup / Shutdown ---
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# --- Joke endpoint ---
@app.get("/joke")
async def get_joke(request: Request):
    # Get session ID from header sent by iPhone app
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())
        print(f"New session created: {session_id}")

    # Get existing jokes for this session
    query = jokes_table.select().where(jokes_table.c.session_id == session_id)
    existing_jokes = await database.fetch_all(query)
    existing_texts = [j["joke_text"] for j in existing_jokes]
    print(f"Session {session_id} existing jokes: {existing_texts}")

    # GPT prompt avoiding repeated jokes
    prompt = "Escribe un chiste / juego de palabras corto con la palabra 'michi' (refiriendose a gatos). Tiene que ser diferente de los siguientes: " + ", ".join(existing_texts)
    print(f"Prompt sent to GPT: {prompt}")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a witty assistant who tells short jokes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9
    )
    joke_text = response.choices[0].message.content
    print(f"GPT returned joke: {joke_text}")

    # Store joke
    await database.execute(
        jokes_table.insert().values(session_id=session_id, joke_text=joke_text)
    )
    print(f"Stored joke for session {session_id}")

    return {"joke": joke_text, "session_id": session_id}
