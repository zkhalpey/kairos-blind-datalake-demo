"""Veeva Vault-style MDM, Consent Gate, and Bronze/Silver/Gold Medallion Lake.

Reverse-engineered clean-room implementation of the Patient Engagement & Support
Program System Architecture (7 integration spokes -> MDM match/resolve -> Consent
enforcement -> Bronze update-only landing -> Silver pseudonymization with isolated
custodian RE-ID crosswalk -> Gold analytics-ready blind layer).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import hmac
import json
from typing import Any


INTEGRATION_SPOKES: tuple[dict[str, Any], ...] = (
    {
        "spoke_id": "frm_nursing",
        "name": "FRM / Nursing",
        "mode": "HUB_INTEGRATED",
        "outbound": ["referral", "rx", "insurance", "consent", "mdm_id", "tasks"],
        "inbound": ["case_status", "bv_pa_nursing"],
    },
    {
        "spoke_id": "hub_partner",
        "name": "Hub Partner + Nursing EHR",
        "mode": "HUB_INTEGRATED",
        "outbound": ["referral", "rx_routing", "mdm_id"],
        "inbound": ["dispense", "ship_status", "fill_refill"],
    },
    {
        "spoke_id": "specialty_pharmacy",
        "name": "Specialty Pharmacy (Direct Decoupled)",
        "mode": "DIRECT",
        "outbound": ["case_patient_status"],
        "inbound": ["enrollment_demographics", "insurance", "rx", "consent"],
    },
    {
        "spoke_id": "hcp_portal",
        "name": "HCP Portal",
        "mode": "DIRECT_HUB_SHARE",
        "outbound": ["content", "reminders", "status"],
        "inbound": ["engagement", "patient_reported", "consent", "afford_enroll", "mdm_id"],
    },
    {
        "spoke_id": "patient_app",
        "name": "RediHealth / Patient Self-Enroll App",
        "mode": "MATCH_ON_REGISTRATION",
        "outbound": ["status"],
        "inbound": ["self_enrollment_demographics", "insurance", "consent"],
    },
    {
        "spoke_id": "bv_pa_partner",
        "name": "BV / PA Partner (Benefits & Prior Auth)",
        "mode": "HUB_INTEGRATED",
        "outbound": ["bv_pa_request", "insurance", "rx", "provider", "mdm_id"],
        "inbound": ["coverage_determination", "pa_status", "appeals", "sob"],
    },
    {
        "spoke_id": "veeva_crm_hcp",
        "name": "Veeva CRM (HCP Field Surface)",
        "mode": "HCP_HCO_MDM",
        "outbound": ["scoped_case_status_activity"],
        "inbound": ["field_interactions", "account_context"],
    },
)

ALLOWED_BATCH_FEEDS = frozenset({
    "realtime_cdc",
    "sp_dispense_status_daily",
    "claims_adjudication_daily",
    "copay_accumulator_weekly",
    "pap_eligibility_recon",
    "hub_eod_reconciliation",
    "formulary_roster_ref",
})


@dataclass(frozen=True)
class ConsentRecord:
    mdm_id: str
    status: str  # "ALLOW" | "DENY" | "REVOKED"
    allowed_purposes: tuple[str, ...]
    dividend_configured: bool
    institute_consented: bool
    updated_at: str


@dataclass(frozen=True)
class SpokeIngestEvent:
    event_id: str
    spoke_id: str
    feed_type: str
    mdm_id: str | None
    purpose: str
    quasi_identifiers: dict[str, Any]
    numeric_features: tuple[float, ...]
    embedding_vector: tuple[float, ...]
    synthetic: bool = True


@dataclass(frozen=True)
class BronzeRecord:
    event_id: str
    spoke_id: str
    feed_type: str
    mdm_id: str
    purpose: str
    quasi_identifiers_hash: str
    numeric_features: tuple[float, ...]
    embedding_vector: tuple[float, ...]
    record_sha256: str


@dataclass(frozen=True)
class SilverRecord:
    opaque_analytics_key: str
    spoke_id: str
    purpose: str
    age_band: str
    region_coarse: str
    numeric_features: tuple[float, ...]
    embedding_vector: tuple[float, ...]
    quasi_identifiers_treated: bool = True


@dataclass(frozen=True)
class GoldRecord:
    opaque_analytics_key: str
    cohort_domain: str
    numeric_features: tuple[float, ...]
    embedding_vector: tuple[float, ...]
    workload_stamp: str  # "homomorphic-numeric" | "confidential-compute"
    walkback_to_mdm_possible: bool = False


class CustodianCrosswalkVault:
    """Isolated hospital/custodian HSM crosswalk.

    In standard Veeva lake deployments, the RE-ID crosswalk often lives in the same
    cloud warehouse under IAM roles. In the Kai Blind DataLake, the crosswalk stays
    exclusively inside the custodian HSM enclave and is never reachable from Silver,
    Gold, or sponsor KaiRos Lighthouse sessions.
    """

    def __init__(self, custodian_hsm_secret: bytes, *, custodian_id: str) -> None:
        if len(custodian_hsm_secret) < 32:
            raise ValueError("custodian_hsm_secret must be at least 32 bytes")
        self._secret = custodian_hsm_secret
        self.custodian_id = custodian_id
        self._crosswalk: dict[str, str] = {}

    def issue_opaque_analytics_key(self, mdm_id: str) -> str:
        if not mdm_id or not mdm_id.strip():
            raise ValueError("mdm_id is required")
        msg = f"kai-blind-silver-key-v1\x00{self.custodian_id}\x00{mdm_id}".encode("utf-8")
        digest = hmac.new(self._secret, msg, hashlib.sha256).hexdigest()
        opaque_key = f"ak1_{digest[:32]}"
        self._crosswalk[opaque_key] = mdm_id
        return opaque_key

    def attempt_external_walkback(self, caller_role: str) -> dict[str, Any]:
        """Any attempt by an analyst, sponsor, or vendor to read the crosswalk fails closed."""
        return {
            "allowed": False,
            "caller_role": caller_role,
            "reason": "REID_CROSSWALK_ISOLATED_IN_CUSTODIAN_HSM_NO_WALKBACK",
        }


class MedallionDataLake:
    """Veeva Vault-compatible MDM + Consent + Bronze/Silver/Gold blind medallion lake."""

    def __init__(self, crosswalk_vault: CustodianCrosswalkVault, *, lake_id: str, domain: str) -> None:
        self.crosswalk_vault = crosswalk_vault
        self.lake_id = lake_id
        self.domain = domain
        self.mastered_mdm_ids: set[str] = set()
        self.consents: dict[str, ConsentRecord] = {}
        self.bronze: list[BronzeRecord] = []
        self.silver: list[SilverRecord] = []
        self.gold: list[GoldRecord] = []
        self.exception_queue: list[dict[str, Any]] = []

    def register_mastered_patient(self, consent: ConsentRecord) -> None:
        """MDM registration must occur in the CRM before any Bronze CDC/batch feed lands."""
        self.mastered_mdm_ids.add(consent.mdm_id)
        self.consents[consent.mdm_id] = consent

    def revoke_consent(self, mdm_id: str, timestamp: str) -> None:
        """Propagate consent revocation across MDM, Silver, and Gold."""
        if mdm_id in self.consents:
            old = self.consents[mdm_id]
            self.consents[mdm_id] = ConsentRecord(
                mdm_id=mdm_id,
                status="REVOKED",
                allowed_purposes=(),
                dividend_configured=old.dividend_configured,
                institute_consented=old.institute_consented,
                updated_at=timestamp,
            )
            opaque_key = self.crosswalk_vault.issue_opaque_analytics_key(mdm_id)
            self.silver = [r for r in self.silver if r.opaque_analytics_key != opaque_key]
            self.gold = [r for r in self.gold if r.opaque_analytics_key != opaque_key]

    def ingest_spoke_event(self, event: SpokeIngestEvent) -> dict[str, Any]:
        """Enforce Bronze landing rules: update-only on existing MDM ID + active consent."""
        if not event.synthetic:
            self.exception_queue.append({
                "event_id": event.event_id,
                "status": "REJECT_NOT_SYNTHETIC",
                "reason": "demonstrator accepts synthetic fixtures only",
            })
            return self.exception_queue[-1]

        if event.feed_type not in ALLOWED_BATCH_FEEDS:
            self.exception_queue.append({
                "event_id": event.event_id,
                "status": "QUARANTINE_INVALID_FEED",
                "reason": f"feed_type {event.feed_type} is not allowlisted",
            })
            return self.exception_queue[-1]

        # Veeva Bronze law: update-only matched on existing MDM ID; unmatched rows -> exception queue, never new patients
        if not event.mdm_id or event.mdm_id not in self.mastered_mdm_ids:
            entry = {
                "event_id": event.event_id,
                "mdm_id": event.mdm_id,
                "status": "QUARANTINE_EXCEPTION_QUEUE",
                "reason": "unmatched_mdm_id_update_only_never_creates_new_patient",
            }
            self.exception_queue.append(entry)
            return entry

        consent = self.consents.get(event.mdm_id)
        if (
            consent is None
            or consent.status != "ALLOW"
            or event.purpose not in consent.allowed_purposes
            or not consent.institute_consented
            or not consent.dividend_configured
        ):
            entry = {
                "event_id": event.event_id,
                "mdm_id": event.mdm_id,
                "status": "DENIED_CONSENT_OR_RIGHTS",
                "reason": "patient/institute consent or dividend rights incomplete for requested purpose",
            }
            self.exception_queue.append(entry)
            return entry

        qi_canonical = json.dumps(event.quasi_identifiers, sort_keys=True, separators=(",", ":"))
        qi_hash = hashlib.sha256(qi_canonical.encode("utf-8")).hexdigest()
        body = {
            "event_id": event.event_id,
            "spoke_id": event.spoke_id,
            "feed_type": event.feed_type,
            "mdm_id": event.mdm_id,
            "purpose": event.purpose,
            "qi_hash": qi_hash,
            "numeric_features": list(event.numeric_features),
        }
        rec_hash = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        bronze_rec = BronzeRecord(
            event_id=event.event_id,
            spoke_id=event.spoke_id,
            feed_type=event.feed_type,
            mdm_id=event.mdm_id,
            purpose=event.purpose,
            quasi_identifiers_hash=qi_hash,
            numeric_features=event.numeric_features,
            embedding_vector=event.embedding_vector,
            record_sha256=rec_hash,
        )
        self.bronze.append(bronze_rec)

        # Promote to Silver: swap MDM ID for opaque pseudonymous analytics key & generalize quasi-identifiers
        opaque_key = self.crosswalk_vault.issue_opaque_analytics_key(event.mdm_id)
        raw_age = int(event.quasi_identifiers.get("age", 65))
        age_band = "65+" if raw_age >= 65 else ("50-64" if raw_age >= 50 else "18-49")
        zip3 = str(event.quasi_identifiers.get("zip", "85258"))[:3] + "XX"

        silver_rec = SilverRecord(
            opaque_analytics_key=opaque_key,
            spoke_id=event.spoke_id,
            purpose=event.purpose,
            age_band=age_band,
            region_coarse=zip3,
            numeric_features=event.numeric_features,
            embedding_vector=event.embedding_vector,
            quasi_identifiers_treated=True,
        )
        self.silver.append(silver_rec)

        # Promote to Gold: analytics-ready blind layer, zero walkback to MDM
        gold_rec = GoldRecord(
            opaque_analytics_key=opaque_key,
            cohort_domain=self.domain,
            numeric_features=event.numeric_features,
            embedding_vector=event.embedding_vector,
            workload_stamp="homomorphic-numeric",
            walkback_to_mdm_possible=False,
        )
        self.gold.append(gold_rec)

        return {
            "event_id": event.event_id,
            "status": "PROMOTED_TO_GOLD",
            "opaque_analytics_key": opaque_key,
            "bronze_record_sha256": rec_hash,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "lake_id": self.lake_id,
            "domain": self.domain,
            "mastered_patients": len(self.mastered_mdm_ids),
            "bronze_count": len(self.bronze),
            "silver_count": len(self.silver),
            "gold_count": len(self.gold),
            "exception_queue_count": len(self.exception_queue),
            "reid_crosswalk_custodian_isolated": True,
        }
