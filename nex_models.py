"""
NEX Autonomous Vision & Loss Prevention OS — Core Data Models
Production-ready Pydantic models for POS integration, Incident Dossiers,
Biometric Retention, and Network Lockout Synchronization.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import hashlib
import uuid

def hash_qr(qr_code: str) -> str:
    """Generates SHA-256 hash of customer QR/identifier for GDPR privacy compliance."""
    return hashlib.sha256(qr_code.encode('utf-8')).hexdigest()[:16]

def generate_incident_id() -> str:
    """Generates human-readable incident identifier matching pitch-deck specification (NX-XXXX)."""
    return f"NX-{uuid.uuid4().hex[:4].upper()}"

class ScannedItem(BaseModel):
    sku: str = Field(..., description="Stock Keeping Unit identifier")
    name: str = Field(..., description="Product human-readable title")
    price: float = Field(..., ge=0.0, description="Unit price in USD/local currency")
    qty: int = Field(1, ge=1, description="Quantity scanned at POS kiosk")

class POSEventRequest(BaseModel):
    transaction_id: str = Field(default_factory=lambda: f"TXN-{uuid.uuid4().hex[:6].upper()}")
    scanned_items: List[ScannedItem] = Field(default_factory=list, description="Items scanned at POS kiosk")
    detected_items: Optional[List[ScannedItem]] = Field(default=None, description="Physical detections override/simulation")
    cooler_id: str = Field("COOLER_04", description="Identifier of the vending cabinet")
    customer_qr: str = Field(..., description="Customer barcode/app credential")

class UnpaidSKU(BaseModel):
    name: str
    qty: int
    price: float
    total: float

class IncidentDossier(BaseModel):
    incident_id: str = Field(default_factory=generate_incident_id)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    cooler_id: str = "COOLER_04"
    customer_face_url: Optional[str] = None
    customer_qr_hash: str
    unpaid_skus: List[UnpaidSKU] = Field(default_factory=list)
    total_unpaid: float = 0.0
    status: str = "LOCKED"  # LOCKED | RESOLVED | DISPUTED
    resolution_method: Optional[str] = None
    evidence_snapshots: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class PayToUnlockRequest(BaseModel):
    customer_qr: Optional[str] = None
    customer_qr_hash: Optional[str] = None
    incident_id: Optional[str] = None
    payment_amount: float
    payment_method: str = "CARD_POS"

class CheckAccessResponse(BaseModel):
    access: str = "GRANTED"  # GRANTED | DENIED
    customer_qr_hash: str
    lock_engaged: bool = False
    unpaid_amount: float = 0.0
    incident_id: Optional[str] = None
    reason: Optional[str] = None

class GDPRPurgeRequest(BaseModel):
    customer_qr: Optional[str] = None
    customer_qr_hash: Optional[str] = None
    reason: str = "USER_REQUEST_GDPR_ARTICLE_17"
