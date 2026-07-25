from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import random, string
from fastapi.routing import APIRouter
from dotenv import load_dotenv

from database import Base, engine, get_db
from models import URL

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()
api = APIRouter(prefix="/api")

class URLRequest(BaseModel):
    url: HttpUrl

def make_code() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))

@api.post("/shorten")
def shorten(request: URLRequest, db: Session = Depends(get_db)) -> dict:
    code = make_code()
    entry = URL(code=code, destination=str(request.url), clicks=0)
    db.add(entry)
    db.commit()
    return {"short_url": f"https://eepyshort.de/{code}"}

@api.get("/info/{code}")
def info(code: str, db: Session = Depends(get_db)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"code": entry.code,
            "destination": entry.destination,
            "clicks": entry.clicks,
            "created_at": entry.created_at
    }

app.include_router(api)

@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    entry.clicks += 1
    db.commit()
    return RedirectResponse(entry.destination)
