"""
NEX Autonomous Vision & Loss Prevention OS — Persistent Storage & Network Lockout Sync
Handles SQLite storage for Incident Dossiers, City-Wide Customer Blacklisting,
Redis Pub/Sub Sync (with zero-dependency local fallback), and Biometric Retention.
"""
import sqlite3
import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from nex_models import (
    IncidentDossier, UnpaidSKU, CheckAccessResponse, hash_qr, generate_incident_id
)

DB_PATH = Path(__file__).parent / "nex_incidents.db"

class IncidentStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._init_redis()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # 1. Incident Dossiers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    cooler_id TEXT NOT NULL,
                    customer_qr_hash TEXT NOT NULL,
                    total_unpaid REAL NOT NULL,
                    status TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)
            # 2. City-wide Blacklist table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    customer_qr_hash TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    unpaid_amount REAL NOT NULL,
                    cooler_id TEXT NOT NULL,
                    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            # 3. Biometric consent & retention audit table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS biometrics_retention (
                    face_hash TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    customer_qr_hash TEXT NOT NULL,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    retention_until TIMESTAMP NOT NULL,
                    incident_linked INTEGER DEFAULT 0,
                    gdpr_deleted INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def _init_redis(self):
        self.redis_client = None
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_timeout=0.2)
            r.ping()
            self.redis_client = r
            print("✓ Redis Network Lockout Sync Active (localhost:6379)")
        except Exception:
            # Safe graceful fallback to internal SQLite & in-memory event bus
            self.redis_client = None

    # ─────────────────────────────────────────────────────────────────
    # INCIDENT DOSSIER CREATION & MANAGEMENT
    # ─────────────────────────────────────────────────────────────────
    def create_incident(self, dossier: IncidentDossier) -> IncidentDossier:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO incidents 
                (id, cooler_id, customer_qr_hash, total_unpaid, status, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dossier.incident_id,
                    dossier.cooler_id,
                    dossier.customer_qr_hash,
                    dossier.total_unpaid,
                    dossier.status,
                    dossier.model_dump_json(),
                    dossier.timestamp
                )
            )
            conn.commit()
            
        # Trigger city-wide lockout across coolers
        self.trigger_network_lockout(dossier.customer_qr_hash, dossier)
        return dossier

    def get_incident(self, incident_id: str) -> Optional[IncidentDossier]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT data FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if row:
                return IncidentDossier.model_validate_json(row["data"])
        return None

    def list_incidents(self, status: Optional[str] = None, limit: int = 50) -> List[IncidentDossier]:
        with self._get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT data FROM incidents WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM incidents ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [IncidentDossier.model_validate_json(r["data"]) for r in rows]

    # ─────────────────────────────────────────────────────────────────
    # NETWORK LOCKOUT SYNCHRONIZATION (SUB-200MS CITY-WIDE SYNC)
    # ─────────────────────────────────────────────────────────────────
    def trigger_network_lockout(self, customer_qr_hash: str, incident: IncidentDossier):
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO blacklist
                (customer_qr_hash, incident_id, unpaid_amount, cooler_id, locked_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_qr_hash,
                    incident.incident_id,
                    incident.total_unpaid,
                    incident.cooler_id,
                    incident.timestamp,
                    expires_at
                )
            )
            conn.commit()

        lockout_payload = {
            "type": "LOCKOUT_TRIGGERED",
            "customer_qr_hash": customer_qr_hash,
            "incident_id": incident.incident_id,
            "unpaid_amount": incident.total_unpaid,
            "cooler_id": incident.cooler_id,
            "timestamp": time.time(),
            "holding_force": "300KG_ACTIVE"
        }

        # Broadcast via Redis if available
        if self.redis_client:
            try:
                self.redis_client.publish("nex:lockout_events", json.dumps(lockout_payload))
                self.redis_client.setex(f"blacklist:{customer_qr_hash}", 86400 * 30, json.dumps(lockout_payload))
            except Exception as e:
                print(f"Redis publish notice: {e}")

        print(f"🔒 [NETWORK LOCKOUT] Customer {customer_qr_hash[:8]} locked out across city. "
              f"Dossier {incident.incident_id} (${incident.total_unpaid:.2f} unpaid)")

    def check_customer_access(self, customer_qr_or_hash: str) -> CheckAccessResponse:
        # Resolve hash if raw QR supplied
        qr_hash = customer_qr_or_hash if len(customer_qr_or_hash) == 16 else hash_qr(customer_qr_or_hash)

        # 1. Fast Redis check (< 5ms)
        if self.redis_client:
            try:
                cached = self.redis_client.get(f"blacklist:{qr_hash}")
                if cached:
                    data = json.loads(cached)
                    return CheckAccessResponse(
                        access="DENIED",
                        customer_qr_hash=qr_hash,
                        lock_engaged=True,
                        unpaid_amount=float(data.get("unpaid_amount", 0.0)),
                        incident_id=data.get("incident_id"),
                        reason=f"300KG Lockout Active. Unpaid balance ${data.get('unpaid_amount', 0.0):.2f} from {data.get('cooler_id', 'Cooler')}."
                    )
            except Exception:
                pass

        # 2. SQLite local blacklist check
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM blacklist WHERE customer_qr_hash = ?", (qr_hash,)
            ).fetchone()
            if row:
                return CheckAccessResponse(
                    access="DENIED",
                    customer_qr_hash=qr_hash,
                    lock_engaged=True,
                    unpaid_amount=float(row["unpaid_amount"]),
                    incident_id=row["incident_id"],
                    reason=f"300KG Lockout Active. Unpaid balance ${float(row['unpaid_amount']):.2f} from {row['cooler_id']}."
                )

        # Access clear
        return CheckAccessResponse(
            access="GRANTED",
            customer_qr_hash=qr_hash,
            lock_engaged=False,
            unpaid_amount=0.0
        )

    # ─────────────────────────────────────────────────────────────────
    # PAY-TO-UNLOCK RESOLUTION
    # ─────────────────────────────────────────────────────────────────
    def resolve_incident_and_unlock(
        self,
        identifier: str,  # incident_id OR customer_qr_hash
        payment_amount: float,
        method: str = "CARD_POS"
    ) -> Dict[str, Any]:
        """
        Settles debt: updates Incident Dossier to RESOLVED,
        purges customer from city-wide blacklist, releases lock.
        """
        with self._get_connection() as conn:
            # Locate incident
            row = conn.execute(
                "SELECT * FROM incidents WHERE id = ? OR customer_qr_hash = ? ORDER BY created_at DESC LIMIT 1",
                (identifier, identifier)
            ).fetchone()

            if not row:
                return {"success": False, "message": f"No active incident found for '{identifier}'"}

            dossier = IncidentDossier.model_validate_json(row["data"])
            now_iso = datetime.now().isoformat()
            dossier.status = "RESOLVED"
            dossier.resolution_method = method
            dossier.notes = f"Settled via {method} (${payment_amount:.2f}) at {now_iso}"

            # Update DB
            conn.execute(
                "UPDATE incidents SET status = 'RESOLVED', data = ?, resolved_at = ? WHERE id = ?",
                (dossier.model_dump_json(), now_iso, dossier.incident_id)
            )
            # Remove from blacklist
            conn.execute("DELETE FROM blacklist WHERE customer_qr_hash = ?", (dossier.customer_qr_hash,))
            conn.commit()

        # Evict from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(f"blacklist:{dossier.customer_qr_hash}")
                unlock_event = {
                    "type": "UNLOCK_RESOLVED",
                    "customer_qr_hash": dossier.customer_qr_hash,
                    "incident_id": dossier.incident_id,
                    "timestamp": time.time()
                }
                self.redis_client.publish("nex:lockout_events", json.dumps(unlock_event))
            except Exception:
                pass

        print(f"🔓 [PAY-TO-UNLOCK] Debt settled for {dossier.incident_id}. Lockout released across network!")
        return {
            "success": True,
            "incident_id": dossier.incident_id,
            "customer_qr_hash": dossier.customer_qr_hash,
            "status": "RESOLVED",
            "door_lock_released": True,
            "message": f"Payment of ${payment_amount:.2f} confirmed. Door lock released."
        }

    # ─────────────────────────────────────────────────────────────────
    # BIOMETRICS CONSENT & 72-HOUR GDPR RETENTION
    # ─────────────────────────────────────────────────────────────────
    def register_biometric_face(self, file_path: str, customer_qr_hash: str, incident_linked: bool = False):
        import hashlib
        face_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        # Retention: 72 hours if no incident, 30 days if linked to incident
        hours = 24 * 30 if incident_linked else 72
        retention_until = (datetime.now() + timedelta(hours=hours)).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO biometrics_retention
                (face_hash, file_path, customer_qr_hash, retention_until, incident_linked, gdpr_deleted)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (face_hash, file_path, customer_qr_hash, retention_until, 1 if incident_linked else 0)
            )
            conn.commit()

    def purge_expired_biometrics(self) -> int:
        """Purges facial captures older than 72 hours that are not linked to theft incidents"""
        now_iso = datetime.now().isoformat()
        purged = 0
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM biometrics_retention 
                WHERE retention_until < ? AND incident_linked = 0 AND gdpr_deleted = 0
                """,
                (now_iso,)
            ).fetchall()

            for r in rows:
                p = Path(r["file_path"])
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass
                conn.execute(
                    "UPDATE biometrics_retention SET gdpr_deleted = 1 WHERE face_hash = ?",
                    (r["face_hash"],)
                )
                purged += 1
            conn.commit()
        return purged

    def gdpr_delete_by_qr_hash(self, customer_qr_hash: str) -> int:
        """Deletes customer face biometrics upon GDPR Article 17 request"""
        deleted_count = 0
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM biometrics_retention WHERE customer_qr_hash = ? AND gdpr_deleted = 0",
                (customer_qr_hash,)
            ).fetchall()

            for r in rows:
                p = Path(r["file_path"])
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass
                conn.execute(
                    "UPDATE biometrics_retention SET gdpr_deleted = 1 WHERE face_hash = ?",
                    (r["face_hash"],)
                )
                deleted_count += 1
            conn.commit()
        return deleted_count

# Global Singleton Instance
incident_store = IncidentStore()
