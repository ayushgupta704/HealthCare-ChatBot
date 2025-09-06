import json
import psycopg2
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from tqdm import tqdm  
load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

cur.execute("""
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    intent TEXT,
    entity TEXT,
    answer TEXT,
    language TEXT,
    embedding vector(384)
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS schemes (
    id SERIAL PRIMARY KEY,
    scheme_name_en TEXT,
    scheme_name_hi TEXT,
    scheme_name_hinglish TEXT,
    purpose_en TEXT,
    purpose_hi TEXT,
    purpose_hinglish TEXT,
    keywords TEXT[],
    embedding vector(384)
);
""")

model = SentenceTransformer('all-MiniLM-L6-v2')
with open("master_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Inserting {len(data)} FAQs into DB...")
for item in tqdm(data, desc="FAQs"):
    if not item.get("query") or not item.get("answer"):
        continue

    text = item["query"] + " " + item["answer"]
    embedding = model.encode(text).tolist()

    cur.execute("""
        INSERT INTO faqs (query, intent, entity, answer, language, embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        item.get("query"),
        item.get("intent"),
        item.get("entity"),
        item.get("answer"),
        item.get("language"),
        embedding
    ))
with open("govt.scheme.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

print(f"Inserting {len(schemes)} Schemes into DB...")
for item in tqdm(schemes, desc="Schemes"):
    text = (item.get("scheme_name_en", "") or "") + " " + (item.get("purpose_en", "") or "")
    embedding = model.encode(text).tolist()

    cur.execute("""
        INSERT INTO schemes (
            scheme_name_en, scheme_name_hi, scheme_name_hinglish,
            purpose_en, purpose_hi, purpose_hinglish, keywords, embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        item.get("scheme_name_en"),
        item.get("scheme_name_hi"),
        item.get("scheme_name_hinglish"),
        item.get("purpose_en"),
        item.get("purpose_hi"),
        item.get("purpose_hinglish"),
        item.get("keywords", []),
        embedding
    ))
conn.commit()
cur.close()
conn.close()
print("all data inserted successfully into Neon DB!")

