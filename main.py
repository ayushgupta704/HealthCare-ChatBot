import os
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")
# model = SentenceTransformer('all-MiniLM-L6-v2')
def get_conn():
    return psycopg2.connect(DATABASE_URL)

class QueryInput(BaseModel):
    query: str

@app.get("/")
def home():
    return {"message": "Health Assistant API is running."}

@app.get("/faq")
def faq_search_get(query: str):
    embedding = model.encode(query).tolist()
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT answer, 1 - (embedding <=> %s::vector) AS similarity
            FROM faqs
            ORDER BY similarity DESC
            LIMIT 1;
        """, (embedding,))
        res = cur.fetchone()
    conn.close()

    if res:
        answer, similarity = res
        return {"answer": answer, "similarity": float(similarity)}
    return {
        "answer": "No result found. Please consult a doctor.",
        "doctor_link": "https://meet.jit.si/doctor-demo-room",
        "similarity": 0.0
    }

@app.post("/faq")
def faq_search_post(data: QueryInput):
    return faq_search_get(data.query)

@app.get("/schemes")
@app.get("/scheme")  # alias
def schemes_search_get(query: str):
    embedding = model.encode(query).tolist()
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT scheme_name_en, purpose_en, 1 - (embedding <=> %s::vector) AS similarity
            FROM schemes
            ORDER BY similarity DESC
            LIMIT 3;
        """, (embedding,))
        results = cur.fetchall()
    conn.close()

    if results:
        return {"results": [
            {"scheme_name": r[0], "purpose": r[1], "similarity": float(r[2])}
            for r in results
        ]}
    return {
        "results": [],
        "fallback": "No schemes found. Please consult a doctor.",
        "doctor_link": "https://meet.jit.si/doctor-demo-room"
    }
@app.post("/schemes")
@app.post("/scheme")  # alias
def schemes_search_post(data: QueryInput):
    return schemes_search_get(data.query)

@app.get("/symptoms")
def alias_symptoms(query: str):
    return faq_search_get(query)

@app.post("/symptoms")
def symptoms_search_post(data: QueryInput):
    # Reuse FAQ GET logic (includes fallback)
    return faq_search_get(data.query)



# Consult Doctor
@app.get("/consult")
def consult_doctor():
    return {
        "doctor_link": "https://meet.jit.si/doctor-demo-room",
        "note": "For accurate diagnosis, please consult a doctor."
    }
