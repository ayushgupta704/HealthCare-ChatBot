
import os
import psycopg2
from psycopg2 import pool
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

#Connection Pool
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def get_conn():
    try:
        conn = db_pool.getconn()
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Database connection failed: {e}")

def release_conn(conn):
    if conn:
        db_pool.putconn(conn)

class QueryInput(BaseModel):
    query: str

@app.get("/")
def home():
    return {"message": "Health Assistant API is running."}

@app.get("/faq")
def faq_search_get(query: str):
    model = get_model()
    embedding = model.encode(query).tolist()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT answer, 1 - (embedding <=> %s::vector) AS similarity
                FROM faqs
                ORDER BY similarity DESC
                LIMIT 1;
            """, (embedding,))
            res = cur.fetchone()
    finally:
        release_conn(conn)

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
    model = get_model()
    embedding = model.encode(query).tolist()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT scheme_name_en, purpose_en, 1 - (embedding <=> %s::vector) AS similarity
                FROM schemes
                ORDER BY similarity DESC
                LIMIT 3;
            """, (embedding,))
            results = cur.fetchall()
    finally:
        release_conn(conn)

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
    return faq_search_get(data.query)

@app.get("/consult")
def consult_doctor():
    return {
        "doctor_link": "https://meet.jit.si/doctor-demo-room",
        "note": "For accurate diagnosis, please consult a doctor."
    }
