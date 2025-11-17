import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Dish as DishSchema, Reservation as ReservationSchema

app = FastAPI(title="Trattoria & Pizzeria API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# --------- Menu Endpoints ---------
class MenuQuery(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    limit: Optional[int] = 200


def _seed_menu_if_empty():
    try:
        existing = get_documents("dish", {}, 1)
        if not existing:
            sample_dishes = [
                {"name": "Margherita", "description": "San Marzano tomatoes, fior di latte, fresh basil", "price": 12.0, "category": "pizza", "tags": ["classic", "vegetarian"], "image": "https://images.unsplash.com/photo-1548365328-9f547fb09530?q=80&w=1200&auto=format&fit=crop"},
                {"name": "Diavola", "description": "Spicy salami, mozzarella, tomato, chili oil", "price": 14.5, "category": "pizza", "tags": ["spicy"], "image": "https://images.unsplash.com/photo-1600628421055-c8b0f4f6c69a?q=80&w=1200&auto=format&fit=crop"},
                {"name": "Bruschetta", "description": "Grilled bread, tomato, garlic, basil, EVOO", "price": 8.5, "category": "starter", "tags": ["vegan"], "image": "https://images.unsplash.com/photo-1523986371872-9d3ba2e2f642?q=80&w=1200&auto=format&fit=crop"},
                {"name": "Tagliatelle al Ragù", "description": "Slow-cooked beef ragù, Parmigiano Reggiano", "price": 16.0, "category": "pasta", "tags": ["house special"], "image": "https://images.unsplash.com/photo-1525755662778-989d0524087e?q=80&w=1200&auto=format&fit=crop"},
                {"name": "Branzino al Forno", "description": "Roasted sea bass, lemon, herbs", "price": 24.0, "category": "main", "tags": ["seafood"], "image": "https://images.unsplash.com/photo-1604909052743-89e532a5e2d3?q=80&w=1200&auto=format&fit=crop"},
                {"name": "Tiramisu", "description": "Espresso-soaked ladyfingers, mascarpone, cocoa", "price": 7.5, "category": "dessert", "tags": ["classic"], "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1200&auto=format&fit=crop"},
                {"name": "Negroni", "description": "Campari, gin, sweet vermouth", "price": 10.0, "category": "drinks", "tags": ["cocktail"], "image": "https://images.unsplash.com/photo-1541976076758-347942db1970?q=80&w=1200&auto=format&fit=crop"},
            ]
            for d in sample_dishes:
                create_document("dish", d)
    except Exception:
        pass


@app.get("/menu", response_model=List[DishSchema])
def get_menu(q: Optional[str] = None, category: Optional[str] = None, limit: int = 200):
    _seed_menu_if_empty()
    filt = {}
    if category:
        filt["category"] = {"$regex": f"^{category}$", "$options": "i"}
    if q:
        regex = {"$regex": q, "$options": "i"}
        filt["$or"] = [
            {"name": regex},
            {"description": regex},
            {"tags": regex},
            {"category": regex},
        ]
    docs = get_documents("dish", filt, limit)
    # Convert Mongo _id to string-safe fields removal
    for d in docs:
        d.pop("_id", None)
    return docs


# --------- Reservation Endpoints ---------
class ReservationResponse(BaseModel):
    success: bool
    message: str
    code: str


@app.post("/reservations", response_model=ReservationResponse)
def create_reservation(reservation: ReservationSchema):
    try:
        data = reservation.model_dump()
        # Basic sanity: future date
        if reservation.reservation_time < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Reservation time must be in the future")
        create_document("reservation", data)
        return {"success": True, "message": "Reservation received! We will confirm shortly.", "code": "OK"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional: echo contact submissions (handled on frontend for now)
class ContactMessage(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    message: str


@app.post("/contact")
def contact_submit(payload: ContactMessage):
    try:
        create_document("contact", payload.model_dump())
        return {"success": True}
    except Exception:
        return {"success": False}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
