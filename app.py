from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import random, string
from fastapi.routing import APIRouter
import os
from dotenv import load_dotenv

from database import Base, engine, get_db
from models import URL

load_dotenv()

Base.metadata.create_all(bind=engine)

RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET")
ADMIN_KEY = os.getenv("ADMIN_KEY")

app = FastAPI()
api = APIRouter(prefix="/api")

class URLRequest(BaseModel):
    url: HttpUrl

def verify_rapidapi(
    x_rapidapi_proxy_secret: str = Header(alias="x-rapidapi-proxy-secret", default=None),
    x_rapidapi_user: str = Header(alias="x-rapidapi-user", default=None),
    x_admin_key: str = Header(alias="x-admin-key", default=None)
):
    if x_admin_key and x_admin_key == ADMIN_KEY:
        return "admin"  # bypass RapidAPI check
    if not x_rapidapi_proxy_secret or x_rapidapi_proxy_secret != RAPIDAPI_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return x_rapidapi_user

def make_code() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=6))

@api.post("/shorten")
def shorten(request: URLRequest, db : Session = Depends(get_db), rapidapi_user: str = Depends(verify_rapidapi)) -> dict:
    code = make_code()
    user = rapidapi_user
    entry = URL(code=code, destination=str(request.url), rapidapi_user=user, clicks=0)
    db.add(entry)
    db.commit()
    return {"short_url": f"https://www.eepyshort.de/{code}"}

@api.delete("/delete/{code}")
def delete(code: str, db : Session = Depends(get_db), rapidapi_user: str = Depends(verify_rapidapi)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    if rapidapi_user != entry.rapidapi_user:
        raise HTTPException(status_code=403, detail="Unauthorized")
    db.delete(entry)
    db.commit()
    return {"message": f"Redirect {code} succesfully deleted"}

@api.get("/info/{code}")
def info(code: str, db: Session = Depends(get_db), rapidapi_user: str = Depends(verify_rapidapi)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    if rapidapi_user != entry.rapidapi_user:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {"code": entry.code,
            "destination": entry.destination,
            "clicks": entry.clicks,
            "created_by": entry.rapidapi_user,
            "created_at": entry.created_at
    }
    

@app.get("/preview/{code}")
def preview(code: str, db : Session = Depends(get_db)) -> dict:
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"code": entry.code, "destination": entry.destination, "created_by": entry.rapidapi_user, "created_at": entry.created_at}

app.include_router(api)

@app.get("/{code}")
def redirect(code: str, db : Session = Depends(get_db)):
    entry = db.query(URL).filter(URL.code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Link not found")
    entry.clicks += 1
    db.commit()
    return RedirectResponse(entry.destination)

