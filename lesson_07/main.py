from pathlib import Path
from time import perf_counter

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    status,
    Response,
    UploadFile,
    File,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.db import get_db
from validations.schemas import CatSchema, CatResponse, OwnerSchema, OwnerResponse
from database.models import Cat, Owner
from middlewares.logs import LogRequestMiddleware


app = FastAPI()

app.add_middleware(LogRequestMiddleware)

# @app.middleware("http")
# async def log_request(request: Request, call_next):
#     start = perf_counter()
#     print(f"Request: {request.method} {request.url}")
#     response: Response = await call_next(request)
#     print(f"Response: {response.status_code}")
#     response.headers["X-Response-Time"] = f"{perf_counter() - start:.2f}s"
#     return response


BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "public")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "public" / "templates"))


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        context={"request": request, "title": "FastAPI - Головна сторінка"},
    )


@app.get("/api/owners", response_model=list[OwnerResponse], tags=["owners"])
def read_owners(db: Session = Depends(get_db)):
    owners = db.query(Owner).all()
    return owners


@app.get("/api/owners/{owner_id}", response_model=OwnerResponse, tags=["owners"])
def read_owner(owner_id: int, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter_by(id=owner_id).first()
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found"
        )
    return owner


@app.post(
    "/api/owners",
    response_model=OwnerResponse,
    tags=["owners"],
    status_code=status.HTTP_201_CREATED,
)
def create_owner(body: OwnerSchema, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter_by(email=body.email).first()
    if owner:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )

    db_owner = Owner(fullname=body.fullname, email=body.email)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner


@app.put("/api/owners/{owner_id}", response_model=OwnerResponse, tags=["owners"])
def update_owner(owner_id: int, body: OwnerSchema, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter_by(id=owner_id).first()
    if owner:
        owner.fullname = body.fullname
        owner.email = body.email
        db.commit()
        db.refresh(owner)
        return owner
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found"
        )


@app.delete("/api/owners/{owner_id}", response_model=OwnerResponse, tags=["owners"])
def delete_owner(owner_id: int, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter_by(id=owner_id).first()
    if owner:
        db.delete(owner)
        db.commit()
        return owner
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found"
        )


@app.get("/api/cats", response_model=list[CatSchema], tags=["cats"])
def read_cats(db: Session = Depends(get_db)):
    cats = db.query(Cat).all()
    return cats


@app.get("/api/cats/{cat_id}", response_model=CatResponse, tags=["cats"])
def read_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter_by(id=cat_id).first()
    if cat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found"
        )
    return cat


@app.post(
    "/api/cats",
    response_model=CatResponse,
    tags=["cats"],
    status_code=status.HTTP_201_CREATED,
)
def create_cat(body: CatSchema, db: Session = Depends(get_db)):
    cat = Cat(**body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@app.put("/api/cats/{cat_id}", response_model=CatResponse, tags=["cats"])
def update_cat(cat_id: int, body: CatSchema, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter_by(id=cat_id).first()
    if cat:
        cat.nick = body.nick
        cat.age = body.age
        cat.vaccinated = body.vaccinated
        db.commit()
        db.refresh(cat)
        return cat
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found"
        )


@app.delete("/api/cats/{cat_id}", response_model=CatResponse, tags=["cats"])
def delete_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter_by(id=cat_id).first()
    if cat:
        db.delete(cat)
        db.commit()
        return cat
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found"
        )


@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    Path("uploads").mkdir(exist_ok=True)
    file_path = f"uploads/{file.filename}"
    MAX_FILE_SIZE = 1024 * 1024  # 1 MB
    file_size = 0
    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                f.close()
                Path(file_path).unlink()
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds the limit: {MAX_FILE_SIZE}",
                )
            f.write(chunk)


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )
