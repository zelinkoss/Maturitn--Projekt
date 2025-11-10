from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI()

# Povolit frontend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Připojení k databázi
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="tvoje_heslo",
    database="autobazar"
)

@app.get("/auta")
def get_autos():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM auta")
    auta = cursor.fetchall()
    cursor.close()
    return auta

@app.post("/auta")
def add_auto(auto: dict):
    if not all(k in auto for k in ("znacka", "model", "cena")):
        raise HTTPException(status_code=400, detail="Chybí údaje")
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO auta (znacka, model, cena) VALUES (%s, %s, %s)",
        (auto["znacka"], auto["model"], auto["cena"])
    )
    db.commit()
    cursor.close()
    return {"message": "Auto přidáno!"}
