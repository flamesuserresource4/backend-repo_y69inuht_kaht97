import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

from database import db, create_document, get_documents, get_document_by_id, update_document, delete_document

app = FastAPI(title="Ayurvedic Cosmetics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductIn(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(ge=0)
    category: str
    ingredients: List[str] = []
    image_url: Optional[str] = None
    gallery: List[str] = []
    in_stock: bool = True
    stock_count: int = 10
    rating: float = 4.5
    reviews_count: int = 0
    popularity: int = 0
    tags: List[str] = []


class Product(ProductIn):
    id: str


@app.get("/")
def read_root():
    return {"message": "Ayurvedic Cosmetics API running"}


@app.get("/api/products", response_model=List[Product])
def list_products(
    q: Optional[str] = Query(None, description="Search term for title or tags"),
    category: Optional[str] = Query(None),
    ingredient: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort: Optional[str] = Query("popularity_desc", description="price_asc|price_desc|name_asc|name_desc|popularity_desc"),
    limit: int = Query(50, ge=1, le=100),
):
    if db is None:
        # Fallback to mock data if db not available
        sample = _mock_products()
        return sample

    filter_dict: dict = {}
    if q:
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    if category:
        filter_dict["category"] = category
    if ingredient:
        filter_dict["ingredients"] = {"$elemMatch": {"$regex": ingredient, "$options": "i"}}
    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        filter_dict["price"] = price_filter

    # Sorting mapping
    sort_map = {
        "price_asc": ("price", 1),
        "price_desc": ("price", -1),
        "name_asc": ("title", 1),
        "name_desc": ("title", -1),
        "popularity_desc": ("popularity", -1),
    }
    sort_key, sort_dir = sort_map.get(sort, ("popularity", -1))

    # Query Mongo directly for sort support
    try:
        cursor = db["product"].find(filter_dict).sort(sort_key, sort_dir).limit(limit)
        items = []
        for d in cursor:
            d["id"] = str(d.pop("_id"))
            items.append(Product(**d))
        return items
    except Exception:
        # fallback using helper
        docs = get_documents("product", filter_dict, limit)
        docs_sorted = sorted(docs, key=lambda x: x.get(sort_key, 0), reverse=(sort_dir == -1))
        return [Product(**d) for d in docs_sorted]


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    doc = get_document_by_id("product", product_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**doc)


@app.post("/api/products", response_model=str)
def create_product(product: ProductIn):
    new_id = create_document("product", product.model_dump())
    return new_id


@app.put("/api/products/{product_id}")
def update_product(product_id: str, product: ProductIn):
    ok = update_document("product", product_id, product.model_dump())
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found or not modified")
    return {"status": "ok"}


@app.delete("/api/products/{product_id}")
def delete_product(product_id: str):
    ok = delete_document("product", product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "ok"}


@app.post("/api/seed")
def seed_products():
    if db is None:
        return {"status": "db_unavailable"}
    existing = db["product"].count_documents({})
    if existing > 0:
        return {"status": "exists", "count": existing}
    for item in _mock_products():
        data = item.model_dump()
        data.pop("id", None)
        create_document("product", data)
    count = db["product"].count_documents({})
    return {"status": "seeded", "count": count}


# -------------------- Utilities --------------------
class _ProductMock(ProductIn):
    id: str = Field("mock")


def _mock_products() -> List[_ProductMock]:
    return [
        _ProductMock(
            id="1",
            title="Kumkumadi Radiance Serum",
            description="Ancient Ayurvedic blend with saffron and sandalwood for glowing skin.",
            price=29.99,
            category="Face Care",
            ingredients=["Saffron", "Sandalwood", "Manjistha"],
            image_url="https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?q=80&w=1200&auto=format&fit=crop",
            popularity=95,
            tags=["glow", "serum", "saffron"],
        ),
        _ProductMock(
            id="2",
            title="Neem & Tea Tree Cleanser",
            description="Purifying face wash to combat acne and excess oil.",
            price=14.5,
            category="Face Care",
            ingredients=["Neem", "Tea Tree", "Tulsi"],
            image_url="https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?q=80&w=1200&auto=format&fit=crop",
            popularity=80,
            tags=["cleanser", "acne"],
        ),
        _ProductMock(
            id="3",
            title="Bhringraj Hair Oil",
            description="Strengthens hair roots and reduces hair fall.",
            price=19.99,
            category="Hair Care",
            ingredients=["Bhringraj", "Amla", "Coconut"],
            image_url="https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?q=80&w=1200&auto=format&fit=crop",
            popularity=88,
            tags=["hair", "oil"],
        ),
        _ProductMock(
            id="4",
            title="Ubtan Body Scrub",
            description="Traditional turmeric and chickpea flour exfoliant.",
            price=12.0,
            category="Body Care",
            ingredients=["Turmeric", "Chickpea", "Rose"],
            image_url="https://images.unsplash.com/photo-1575052814086-f385e2e2ad1b?q=80&w=1200&auto=format&fit=crop",
            popularity=70,
            tags=["ubtan", "scrub"],
        ),
    ]


@app.get("/test")
def test_database():
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            resp["database"] = "✅ Available"
            resp["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "⚠️ Default"
            resp["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "⚠️ Default"
            resp["connection_status"] = "Connected"
            try:
                resp["collections"] = db.list_collection_names()[:10]
                resp["database"] = "✅ Connected & Working"
            except Exception as e:
                resp["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            resp["database"] = "❌ Not Available"
    except Exception as e:
        resp["database"] = f"❌ Error: {str(e)[:80]}"
    return resp


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
