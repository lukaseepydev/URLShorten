from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import random, string

from database import Base, engine, get_db
from models import URL

Base.metadata.create_all(bind=engine)

app = FastAPI()

class URLRequest(BaseModel):
    url: HttpUrl

def make_code() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))

@app.post("/shorten")
def shorten(request: URLRequest, db : Session = Depends(get_db)) -> dict:
    code = make_code()
    entry = URL(code=code, destination=str(request.url))
    db.add(entry)
    db.commit()
    return {"short_url": f"http://localhost:8000/{code}"}

@app.delete("/delete/{code}")
def delete(code: str, db : Session = Depends(get_db)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
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