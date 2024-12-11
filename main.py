from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import random

# Tietokannan asetukset
DB_PATH = "hashes.db"
app = FastAPI()

# Tietokantataulun luonti
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS hashes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        original_message TEXT,
        encrypted_message TEXT
    )
    """)
    conn.commit()
    conn.close()

initialize_db()

# Mallit
class NewUserRequest(BaseModel):
    name: str
    message: str

class FetchMessageRequest(BaseModel):
    name: str
    id: int

# Salausfunktio (ROT13)
def encrypt_message(message: str) -> str:
    kirjaimet = "abcdefghijklmnopqrstuvwxyz"
    encrypted = ""
    for merkki in message:
        if merkki.isalpha():
            indeksi = kirjaimet.find(merkki.lower())
            uusi_indeksi = (indeksi + 13) % len(kirjaimet)
            encrypted += kirjaimet[uusi_indeksi]
        else:
            encrypted += merkki
    return encrypted

# Reitit
@app.post("/add_user/")
def add_user(request: NewUserRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user_id = random.randint(1000000, 9999999)
    encrypted_message = encrypt_message(request.message)
    c.execute("INSERT INTO hashes (id, name, original_message, encrypted_message) VALUES (?, ?, ?, ?)",
              (user_id, request.name, request.message, encrypted_message))
    conn.commit()
    conn.close()
    return {"id": user_id, "encrypted_message": encrypted_message}

@app.post("/fetch_message/")
def fetch_message(request: FetchMessageRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT original_message, encrypted_message FROM hashes WHERE id = ? AND name = ?", 
              (request.id, request.name))
    result = c.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Message not found or invalid ID")
    return {"original_message": result[0], "encrypted_message": result[1]}
