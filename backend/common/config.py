"""
Load and validate environment variables.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseSettings

# Load .env locally
if os.getenv("AWS_LAMBDA_FUNCTION_NAME") is None:
    load_dotenv()

class Settings(BaseSettings):
    AWS_REGION: str
    USERS_TABLE: str
    OTPS_TABLE: str
    ORDERS_TABLE: str
    RECEIPTS_TABLE: str
    AUDIT_LOGS_TABLE: str
    JWT_SECRET: str
    RECEIPT_BUCKET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
