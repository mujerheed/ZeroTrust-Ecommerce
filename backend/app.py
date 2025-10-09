from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

# Import routers from modules (auth, vendor, ceo)
from auth_service.auth_routes import router as auth_router
from vendor_service.vendor_routes import router as vendor_router
from ceo_service.ceo_routes import router as ceo_router

# Include routers with prefixes
app.include_router(auth_router, prefix="/auth")
app.include_router(vendor_router, prefix="/vendor")
app.include_router(ceo_router, prefix="/ceo")

handler = Mangum(app) # For AWS Lambda compatibility
