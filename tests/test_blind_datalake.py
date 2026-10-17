"""Pytest verification suite for the Kai Blind Platform (KaiRos on Kai Lake, v0.3)."""

from __future__ import annotations

from pathlib import Path
import pytest

from kairos_blind_lake.cli import run_full_demo
from kairos_blind_lake.compliance_matrix import evaluate_compliance_readiness
from kairos_blind_lake.medallion_vault import (
    ConsentRecord,
    CustodianCrosswalkVault,
    MedallionDataLake,
    SpokeIngestEvent,
)
from kairos_blind_lake.transparency_log import IndependentWitness, MerkleTransparencyLog


def test_veeva_medallion_mdm_consent_and_crosswalk_isolation() -> None:
    vault = CustodianCrosswalkVault(b"custodian-secret-key-32-bytes-ok!", custodian_id="test-custodian")
    lake = MedallionDataLake(vault, lake_id="test-lake", domain="cardiac")

    # Unmatched MDM ID must go to exception queue, never create a patient in Bronze
    unmatched = lake.ingest_spoke_event(
        SpokeIngestEvent(
            event_id="evt-1",
            spoke_id="frm_nursing",
            feed_type="realtime_cdc",
            mdm_id="MDM-UNREGISTERED",
            purpose="sponsor_model_validation",
            quasi_identifiers={"age": 70, "zip": "85258"},
            numeric_features=(0.1, 0.2),
            embedding_vector=(0.1, 0.2),
        )
    )
    assert unmatched["status"] == "QUARANTINE_EXCEPTION_QUEUE"
    assert len(lake.bronze) == 0
    assert len(lake.gold) == 0

    # Register mastered patient with consent
    lake.register_mastered_patient(
        ConsentRecord(
            mdm_id="MDM-0001",
            status="ALLOW",
            allowed_purposes=("sponsor_model_validation",),
            dividend_configured=True,
            institute_consented=True,
            updated_at="2026-10-17T08:00:00Z",
        )
    )
    promoted = lake.ingest_spoke_event(
        SpokeIngestEvent(
            event_id="evt-2",
            spoke_id="veeva_crm_hcp",
            feed_type="realtime_cdc",
            mdm_id="MDM-0001",
            purpose="sponsor_model_validation",
            quasi_identifiers={"age": 70, "zip": "85258"},
            numeric_features=(0.5, 0.3),
            embedding_vector=(0.2, 0.4),
        )
    )
    assert promoted["status"] == "PROMOTED_TO_GOLD"
    assert len(lake.bronze) == 1
    assert len(lake.silver) == 1
    assert len(lake.gold) == 1
    assert lake.silver[0].region_coarse == "852XX"
    assert lake.gold[0].walkback_to_mdm_possible is False

    # External walkback attempt must fail closed
    walkback = vault.attempt_external_walkback("sponsor_merck")
    assert walkback["allowed"] is False

    # Consent revocation removes patient from Silver and Gold immediately
    lake.revoke_consent("MDM-0001", "2026-10-17T08:05:00Z")
    assert len(lake.silver) == 0
    assert len(lake.gold) == 0


def test_merkle_transparency_log_and_split_view_equivocation_defense() -> None:
    w1 = IndependentWitness("w1", b"witness-1-secret-key-32-bytes-ok!")
    w2 = IndependentWitness("w2", b"witness-2-secret-key-32-bytes-ok!")
    log = MerkleTransparencyLog("org-hsm-1", b"org-secret-key-32-bytes-ok-12345!", [w1, w2])

    # Forbidden PHI fields are rejected before hashing
    with pytest.raises(ValueError, match="forbidden sensitive fields"):
        log.append_receipt({"mrn": "12345"}, timestamp_utc="2026-10-17T08:00:00Z")

    log.append_receipt({"request_id": "req-1", "decision": "RELEASE"}, timestamp_utc="2026-10-17T08:00:01Z")
    log.append_receipt({"request_id": "req-2", "decision": "WITHHOLD"}, timestamp_utc="2026-10-17T08:00:02Z")

    ok, errors = log.verify_log_integrity()
    assert ok is True
    assert errors == []

    # Split-view equivocation attempt at the same (tree_size, epoch) with a different root must raise RuntimeError
    with pytest.raises(RuntimeError, match="SPLIT_VIEW_EQUIVOCATION_DETECTED"):
        w1.cosign(tree_size=1, epoch=1, root_hash="f" * 64, prev_root_hash="0" * 64)


def test_end_to_end_demo_merck_regeneron_and_cyberkai_redteam_scenarios(tmp_path: Path) -> None:
    bundle = run_full_demo(output_dir=tmp_path)

    assert bundle["medallion_summary"]["mastered_patients"] == 30
    assert bundle["medallion_summary"]["gold_count"] == 29  # 30 ingested minus 1 revoked
    assert bundle["medallion_summary"]["exception_queue_count"] == 1
    assert bundle["transparency_log_integrity"]["verified"] is True
    assert bundle["transparency_log_integrity"]["tree_size"] == 10

    decisions = {
        r["receipt"]["request_id"]: (r["receipt"]["decision"], r["receipt"]["released"])
        for r in bundle["sponsor_runs"]
    }
    assert decisions["REQ-MERCK-TULISOKIBART-001-PASS"] == ("RELEASE_ASSURED_FHE_AGGREGATE", True)
    assert decisions["REQ-REGENERON-OCT-002-PASS"] == ("RELEASE_CLOAKED_EMBEDDING_AGGREGATE", True)
    assert decisions["REQ-MERCK-TULISOKIBART-003-UNCALIBRATED-BLOCK"] == ("WITHHOLD_UNCALIBRATED_SLOPE_COLLAPSE", False)
    assert decisions["REQ-SPONSOR-004-ROW-EXPORT-BLOCK"] == ("REJECT_VENDOR_OR_ROW_EXPORT_PATH", False)
    assert decisions["REQ-REGENERON-005-FINGERPRINT-DRIFT"] == ("WITHHOLD_CRYPTO_FINGERPRINT_MISMATCH", False)
    assert decisions["REQ-REGENERON-006-BULK-DICOM-BLOCK"] == ("REJECT_FHE_ON_BULK_MODALITY", False)
    assert decisions["REQ-REGENERON-007-DOSE-CLAIM-ABSTAIN"] == ("ABSTAIN_UNSUPPORTED_CLINICAL_CLAIM", False)
    assert decisions["REQ-ATTACK-008-REPLAY-NONCE-BLOCK"] == ("REJECT_REPLAYED_VERIFIER_NONCE", False)
    assert decisions["REQ-ATTACK-009-DIFFERENCING-RECONSTRUCTION-BLOCK"] == ("REJECT_DIFFERENCING_RECONSTRUCTION_ATTACK", False)
    assert decisions["REQ-ATTACK-010-FORGED-MLDSA65-MODEL-SIG-BLOCK"] == ("REJECT_INVALID_MODEL_MLDSA65_SIGNATURE", False)

    comp = evaluate_compliance_readiness()
    assert comp["frameworks_mapped"] == 5
    assert len(comp["truth_class_provenance"]) == 4
    assert (tmp_path / "kairos_blind_datalake_demo_receipt.json").is_file()
    assert (tmp_path / "kairos_blind_datalake_dashboard.html").is_file()
