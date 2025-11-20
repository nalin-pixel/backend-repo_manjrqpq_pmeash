import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import ProductSaaS, License

app = FastAPI(title="Licensing SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Licensing SaaS backend is running"}


@app.get("/test")
def test_database():
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


# Simple ID helper
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    plan: Optional[str] = "standard"
    price: Optional[float] = 0
    status: Optional[str] = "active"


class LicenseCreate(BaseModel):
    product_id: str
    assigned_to: Optional[str] = None
    max_activations: int = 1
    expires_at: Optional[str] = None  # ISO string


@app.post("/api/products")
def create_product(product: ProductCreate):
    try:
        pid = create_document("productsaas", ProductSaaS(**product.model_dump()))
        return {"id": pid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/products")
def list_products():
    try:
        docs = get_documents("productsaas")
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
        return docs
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/licenses")
def create_license(data: LicenseCreate):
    try:
        # Ensure product exists
        prod = db["productsaas"].find_one({"_id": ObjectId(data.product_id)})
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")

        # Generate a simple license key
        import secrets
        token = secrets.token_urlsafe(16).upper().replace("-", "").replace("_", "")
        # Format like XXXX-XXXX-XXXX-XXXX
        key = "-".join([token[i:i+4] for i in range(0, 16, 4)])

        payload = License(
            product_id=data.product_id,
            key=key,
            assigned_to=data.assigned_to,
            max_activations=data.max_activations,
            activations=[],
            status="unused",
            expires_at=None,
        )
        lid = create_document("license", payload)
        return {"id": lid, "key": key}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/licenses")
def list_licenses(product_id: Optional[str] = None):
    try:
        filt = {"product_id": product_id} if product_id else {}
        docs = get_documents("license", filt)
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
        return docs
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ActivationRequest(BaseModel):
    key: str
    machine_id: str


@app.post("/api/licenses/activate")
def activate_license(payload: ActivationRequest):
    try:
        lic = db["license"].find_one({"key": payload.key})
        if not lic:
            raise HTTPException(status_code=404, detail="License not found")
        if lic.get("status") in ["suspended", "expired"]:
            raise HTTPException(status_code=403, detail="License not active")
        activations = lic.get("activations", [])
        max_acts = lic.get("max_activations", 1)
        if payload.machine_id in activations:
            return {"status": "ok", "message": "Already activated on this machine"}
        if len(activations) >= max_acts:
            raise HTTPException(status_code=403, detail="Activation limit reached")
        activations.append(payload.machine_id)
        status = "active"
        db["license"].update_one({"_id": lic["_id"]}, {"$set": {"activations": activations, "status": status}})
        return {"status": "ok", "message": "Activated", "activations": activations}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
