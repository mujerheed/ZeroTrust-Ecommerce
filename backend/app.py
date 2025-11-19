import os
from fastapi import FastAPI
from mangum import Mangum
from dotenv import load_dotenv

# Load .env file only in local development
if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is None:
    load_dotenv()

app = FastAPI()

# Import routers from modules (auth, vendor, ceo, receipt, order, integrations)
from auth_service.auth_routes import router as auth_router
from vendor_service.vendor_routes import router as vendor_router
from ceo_service.ceo_routes import router as ceo_router
from receipt_service.receipt_routes import router as receipt_router
from order_service.order_routes import router as order_router
from integrations.webhook_routes import router as webhook_router

# Include routers with prefixes
app.include_router(auth_router, prefix="/auth")
app.include_router(vendor_router, prefix="/vendor")
app.include_router(ceo_router, prefix="/ceo")
app.include_router(receipt_router, prefix="/receipts")
app.include_router(order_router, prefix="/orders")
app.include_router(webhook_router, prefix="/integrations")

# Lambda handler
handler = Mangum(app)
lambda_handler = handler  # Alias for AWS Lambda compatibility
