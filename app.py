from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import random, string, secrets, bcrypt

from database import Base, engine, get_db
from models import URL

Base.metadata.create_all(bind=engine)

app = FastAPI()

class URLRequest(BaseModel):
    url: HttpUrl

def make_code() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))

def make_api_key():
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    return bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

def verify_api_key(api_key: str, hashed: str) -> bool:
    return bcrypt.checkpw(api_key.encode(), hashed.encode())

@app.post("/shorten")
def shorten(request: URLRequest, db : Session = Depends(get_db)) -> dict:
    code = make_code()
    api_key = make_api_key()
    entry = URL(code=code, destination=str(request.url), api_key=hash_api_key(api_key))
    db.add(entry)
    db.commit()
    return {"short_url": f"https://urlshorten-production-abc0.up.railway.app/{code}", "api_key": api_key}

@app.delete("/delete/{code}")
def delete(code: str, x_api_key: str = Header(), db : Session = Depends(get_db)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    if not verify_api_key(x_api_key, entry.api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    db.delete(entry)
    db.commit()
    return {"message": f"Redirect {code} succesfully deleted"}

@app.get("/preview/{code}")
def preview(code: str, db : Session = Depends(get_db)) -> dict:
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"code": entry.code, "destination": entry.destination, "created_at": entry.created_at}

@app.get("/{code}")
def redirect(code: str, db : Session = Depends(get_db)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    return RedirectResponse(entry.destination)