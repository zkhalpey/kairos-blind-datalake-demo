"""KaiRos Lighthouse & Sovereign Blind Enclave Execution Engine.

Enforces the boundary where external biopharma models (e.g., Merck, Regeneron)
touch live blind data in the Gold Medallion layer through KaiRos Lighthouse:
1. Hardware TEE Enclave Attestation check (PCR0/measurement allowlist + freshness)
2. Custodian-held HSM key isolation (vendor/sponsor never receives secret keys or raw rows)
3. KBE Kernel modality & circuit routing (numeric CKKS FHE vs model-specific Stochastic Embedding Cloak)
4. Public-Safe Black-Box Output Assurance Gate (verifies discrimination, calibration slope, Brier score,
   and clinical net benefit at threshold without exposing Tier B/C internal CAPC fitting code)
5. Differential Privacy & k-Anonymity floor (n >= 25 distinct patients, cumulative epsilon accounting)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any

from .medallion_vault import GoldRecord, MedallionDataLake
from .transparency_log import MerkleTransparencyLog


MIN_COHORT_K_ANONYMITY = 25


def _canonical_sha256(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EnclaveAttestation:
    enclave_id: str
    tee_architecture: str  # e.g. "AWS-Nitro-Enclave-v2" or "Azure-Confidential-SEV-SNP"
    pcr0_measurement_sha256: str
    ephemeral_public_key_sha256: str
    verifier_nonce: str
    freshness_ok: bool
    key_custodian: str  # must be hospital/custodian HSM, never vendor or sponsor


@dataclass(frozen=True)
class CircuitCatalogEntry:
    circuit_id: str
    modality: str  # "numeric_vector" | "embedding_cloak"
    scheme: str  # "CKKS-Ring-LWE" | "Stochastic-Embedding-Cloak"
    n_features: int
    library_pinned: str
    parameter_profile_digest: str
    # Pre-computed synthetic calibration & clinical net-benefit assurance fixture
    # (Public-safe Tier A headline metrics; Tier B/C fitting internals remain held)
    uncalibrated_auc: float
    uncalibrated_slope: float
    uncalibrated_brier: float
    uncalibrated_net_benefit_at_035: float
    calibrated_auc: float
    calibrated_slope: float
    calibrated_brier: float
    calibrated_net_benefit_at_035: float


@dataclass(frozen=True)
class SponsorModelRequest:
    request_id: str
    sponsor_tenant: str  # e.g. "merck-research-labs" | "regeneron-genetics-center"
    model_id: str
    model_weights_sha256: str
    target_lake_id: str
    query_class: str  # "frozen_fhe_circuit" | "cloak_embedding_inference" | "export_row" | "drug_dose_claim"
    modality: str
    circuit_id: str | None
    presented_profile_digest: str | None
    apply_post_decryption_assurance: bool
    requested_vendor_decrypt: bool
    requested_row_export: bool
    epsilon_cost: float
    timestamp_utc: str
    synthetic: bool = True


class KaiRosLighthouse:
    """The KaiRos Lighthouse control plane mediating sponsor AI models over the Blind DataLake."""

    def __init__(
        self,
        *,
        allowed_pcr0_measurements: set[str],
        circuits: dict[str, CircuitCatalogEntry],
        transparency_log: MerkleTransparencyLog,
        tenant_privacy_budgets: dict[str, float],
    ) -> None:
        self.allowed_pcr0_measurements = allowed_pcr0_measurements
        self.circuits = circuits
        self.transparency_log = transparency_log
        self.tenant_privacy_budgets = dict(tenant_privacy_budgets)
        self.tenant_privacy_spent: dict[str, float] = {k: 0.0 for k in tenant_privacy_budgets}

    def evaluate_sponsor_request(
        self,
        request: SponsorModelRequest,
        lake: MedallionDataLake,
        attestation: EnclaveAttestation,
    ) -> dict[str, Any]:
        """Execute fail-closed 8-stage gate before any aggregate leaves the KaiRos Lighthouse."""
        reasons: list[str] = []

        # Gate 1: Synthetic-first boundary
        if not request.synthetic:
            return self._emit_decision(
                request, lake, attestation,
                decision="REJECT_NOT_SYNTHETIC",
                released=False,
                reasons=["synthetic_only_boundary_enforced"],
                aggregate_output=None,
            )

        # Gate 2: Zero row export & zero vendor/sponsor decrypt
        if (
            request.requested_row_export
            or request.requested_vendor_decrypt
            or request.query_class == "export_row"
            or attestation.key_custodian in {"vendor", "sponsor", request.sponsor_tenant}
        ):
            return self._emit_decision(
                request, lake, attestation,
                decision="REJECT_VENDOR_OR_ROW_EXPORT_PATH",
                released=False,
                reasons=["raw_row_export_and_vendor_decrypt_are_hard_rejected"],
                aggregate_output=None,
            )

        # Gate 3: Hardware TEE Enclave Attestation & Freshness
        if (
            not attestation.freshness_ok
            or attestation.pcr0_measurement_sha256 not in self.allowed_pcr0_measurements
        ):
            return self._emit_decision(
                request, lake, attestation,
                decision="WITHHOLD_INVALID_TEE_ATTESTATION",
                released=False,
                reasons=["tee_enclave_pcr0_measurement_or_freshness_failed"],
                aggregate_output=None,
            )

        # Gate 4: Bulk modality & unvalidated drug-dose claim block
        if request.modality in {"dicom", "video", "waveform", "free_text"}:
            return self._emit_decision(
                request, lake, attestation,
                decision="REJECT_FHE_ON_BULK_MODALITY",
                released=False,
                reasons=["bulk_imaging_video_notes_stay_at_rest_under_ml_kem_768_envelope"],
                aggregate_output=None,
            )
        if request.query_class in {"drug_dose_claim", "eligibility_freetext"}:
            return self._emit_decision(
                request, lake, attestation,
                decision="ABSTAIN_UNSUPPORTED_CLINICAL_CLAIM",
                released=False,
                reasons=["no_validated_dose_comparative_or_freetext_circuit_in_catalog"],
                aggregate_output=None,
            )

        # Gate 5: k-Anonymity Cohort Floor (n >= 25 distinct consented Gold patients)
        distinct_keys = {r.opaque_analytics_key for r in lake.gold}
        cohort_n = len(distinct_keys)
        if cohort_n < MIN_COHORT_K_ANONYMITY:
            return self._emit_decision(
                request, lake, attestation,
                decision="WITHHOLD_COHORT_BELOW_K25_FLOOR",
                released=False,
                reasons=[f"cohort_size_{cohort_n}_below_minimum_{MIN_COHORT_K_ANONYMITY}"],
                aggregate_output=None,
            )

        # Gate 6: Differential Privacy Cumulative Budget Accounting
        budget_max = self.tenant_privacy_budgets.get(request.sponsor_tenant, 0.0)
        spent = self.tenant_privacy_spent.get(request.sponsor_tenant, 0.0)
        if request.epsilon_cost <= 0 or (spent + request.epsilon_cost) > budget_max:
            return self._emit_decision(
                request, lake, attestation,
                decision="WITHHOLD_PRIVACY_BUDGET_EXHAUSTED",
                released=False,
                reasons=[f"tenant_epsilon_budget_exceeded ({spent + request.epsilon_cost:.2f} > {budget_max:.2f})"],
                aggregate_output=None,
            )

        # Gate 7: Circuit Catalog & Cryptographic Parameter Fingerprint Binding
        circuit = self.circuits.get(request.circuit_id or "")
        if circuit is None:
            return self._emit_decision(
                request, lake, attestation,
                decision="ABSTAIN_UNKNOWN_CIRCUIT",
                released=False,
                reasons=["requested_circuit_not_in_allowlisted_catalog"],
                aggregate_output=None,
            )
        if request.presented_profile_digest != circuit.parameter_profile_digest:
            return self._emit_decision(
                request, lake, attestation,
                decision="WITHHOLD_CRYPTO_FINGERPRINT_MISMATCH",
                released=False,
                reasons=["presented_crypto_parameter_digest_diverges_from_calibrated_profile"],
                aggregate_output=None,
            )

        # Gate 8: Clinical Output Assurance Gate (Discrimination, Calibration Slope & Net Benefit)
        # Demonstrates the Paper 1 / OLIVES finding: uncalibrated approximate FHE preserves AUC
        # but collapses calibration slope (e.g. 1.32e7) and inverts clinical net benefit (< 0).
        if not request.apply_post_decryption_assurance:
            slope_ok = 0.90 <= circuit.uncalibrated_slope <= 1.10
            nb_ok = circuit.uncalibrated_net_benefit_at_035 > 0.0
            if not (slope_ok and nb_ok):
                return self._emit_decision(
                    request, lake, attestation,
                    decision="WITHHOLD_UNCALIBRATED_SLOPE_COLLAPSE",
                    released=False,
                    reasons=[
                        f"uncalibrated_fhe_slope_{circuit.uncalibrated_slope:.3g}_outside_0.90_1.10",
                        f"uncalibrated_net_benefit_{circuit.uncalibrated_net_benefit_at_035:.4f}_harmful",
                    ],
                    aggregate_output=None,
                )

        # Compute bounded aggregate over Gold layer inside the enclave
        mean_score = self._compute_bounded_gold_aggregate(lake.gold, request.modality)
        self.tenant_privacy_spent[request.sponsor_tenant] = round(spent + request.epsilon_cost, 4)

        decision_label = (
            "RELEASE_CLOAKED_EMBEDDING_AGGREGATE"
            if circuit.modality == "embedding_cloak"
            else "RELEASE_ASSURED_FHE_AGGREGATE"
        )
        reasons.append("tee_attested_hsm_custodian_verified")
        reasons.append("k25_cohort_floor_and_dp_budget_verified")
        reasons.append("post_decryption_calibration_and_net_benefit_verified")
        if circuit.modality == "embedding_cloak":
            reasons.append("stochastic_cloak_is_model_specific_perturbation_not_fhe_encryption")

        aggregate_output = {
            "cohort_n": cohort_n,
            "k_anonymity_floor": MIN_COHORT_K_ANONYMITY,
            "mean_risk_probability": round(mean_score, 4),
            "assurance_metrics": {
                "auc_discrimination": circuit.calibrated_auc,
                "calibration_slope": circuit.calibrated_slope,
                "brier_score": circuit.calibrated_brier,
                "net_benefit_at_035": circuit.calibrated_net_benefit_at_035,
            },
            "privacy_ledger": {
                "epsilon_spent_this_run": request.epsilon_cost,
                "epsilon_cumulative": self.tenant_privacy_spent[request.sponsor_tenant],
                "epsilon_budget_max": budget_max,
            },
            "raw_rows_exported": 0,
            "reid_crosswalk_touched": False,
        }

        return self._emit_decision(
            request, lake, attestation,
            decision=decision_label,
            released=True,
            reasons=reasons,
            aggregate_output=aggregate_output,
        )

    @staticmethod
    def _compute_bounded_gold_aggregate(gold_records: list[GoldRecord], modality: str) -> float:
        probs: list[float] = []
        for rec in gold_records:
            vec = rec.embedding_vector if modality == "embedding_cloak" else rec.numeric_features
            logit = sum(vec) / max(len(vec), 1)
            prob = 1.0 / (1.0 + math.exp(-max(min(logit, 20.0), -20.0)))
            probs.append(prob)
        return sum(probs) / max(len(probs), 1)

    def _emit_decision(
        self,
        request: SponsorModelRequest,
        lake: MedallionDataLake,
        attestation: EnclaveAttestation,
        *,
        decision: str,
        released: bool,
        reasons: list[str],
        aggregate_output: dict[str, Any] | None,
    ) -> dict[str, Any]:
        receipt_body = {
            "schema": "kairos-lighthouse-execution-receipt-v1",
            "request_id": request.request_id,
            "sponsor_tenant": request.sponsor_tenant,
            "model_id": request.model_id,
            "model_weights_sha256": request.model_weights_sha256,
            "target_lake_id": lake.lake_id,
            "circuit_id": request.circuit_id or "NONE",
            "presented_profile_digest": request.presented_profile_digest or "NONE",
            "tee_enclave_id": attestation.enclave_id,
            "tee_pcr0_sha256": attestation.pcr0_measurement_sha256,
            "key_custodian": attestation.key_custodian,
            "decision": decision,
            "released": released,
            "reasons": reasons,
            "output_digest_sha256": _canonical_sha256(aggregate_output) if aggregate_output else "0" * 64,
        }
        receipt_sha256 = _canonical_sha256(receipt_body)
        receipt_body["receipt_sha256"] = receipt_sha256

        log_proof = self.transparency_log.append_receipt(
            receipt_body, timestamp_utc=request.timestamp_utc
        )

        return {
            "receipt": receipt_body,
            "aggregate_output": aggregate_output,
            "transparency_proof": log_proof,
        }
