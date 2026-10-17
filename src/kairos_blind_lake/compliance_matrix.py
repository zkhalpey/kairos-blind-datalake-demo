"""Compliance Readiness Mapping (ISO 27001/27701, SOC 1/2 Type II, HIPAA, 21 CFR Part 11),
Cloaked Veeva-Like Platform Comparison, and Truth-Class Provenance Table (v0.3).

Framed honestly for enterprise pharma CISO/QA and VP Biometrics diligence:
1. Separates Observed Published Clinical Benchmarks (STS n=289,604; OLIVES OCT n=90; ARTEMIS-UC n=135)
   from Synthetic Live Enclave Cohorts (Kai Lake Gold n=29) in an explicit Truth-Class Table.
2. Maps architectural controls to ISO/SOC/HIPAA/Part 11 verification paths without claiming an
   unissued external audit opinion.
"""

from __future__ import annotations

from typing import Any


TRUTH_CLASS_PROVENANCE_TABLE: tuple[dict[str, str], ...] = (
    {
        "quantity_or_metric": "STS Adult Cardiac Surgery Benchmark (n = 289,604; AUC 0.6676; Uncalibrated CKKS Slope 1.32e7 -> Calibrated 1.011; Brier 0.2450 -> 0.1749)",
        "truth_class": "OBSERVED_EMPIRICAL_BENCHMARK",
        "source_provenance": "Paper 1 locked cardiac FHE + post-decryption calibration benchmark (protocol locked 2026-09-16).",
        "demo_role": "Establishes the empirical phenomenon that approximate FHE preserves rank while collapsing calibration slope and net benefit.",
    },
    {
        "quantity_or_metric": "OLIVES Retinal OCT Benchmark (90 paired eyes, 186 B-scans, central scan 25/49; Plaintext CST MAE 38.30 um; Uncalibrated CKKS slope 0.852 -> Calibrated 1.004, MAE 38.33 um)",
        "truth_class": "OBSERVED_EMPIRICAL_BENCHMARK",
        "source_provenance": "OLIVES public ophthalmic OCT archive (MD5 e08f4198aa919d6900bd30525c137933, patient split seed 7: train 53, cal 18, test 19).",
        "demo_role": "Provides the ground-truth accuracy and calibration reference for Use Case A (Regeneron Retinal OCT Fluid Persistence).",
    },
    {
        "quantity_or_metric": "ARTEMIS-UC Phase 2 Tulisokibart (MK-7240 / PRA023) Trial Reference (n = 135; Week-12 Clinical Remission 26% vs 1% Placebo in Cohort 1; 32% vs 11% in CDx+ Biomarker Stratum)",
        "truth_class": "PUBLISHED_LITERATURE_REFERENCE",
        "source_provenance": "Published NEJM Phase 2 ARTEMIS-UC (NCT04996797) and UEG Week long-term anti-TL1A extension studies.",
        "demo_role": "Defines the clinical precision-immunology stratification target for Use Case B (Merck Tulisokibart Anti-TL1A CDx).",
    },
    {
        "quantity_or_metric": "Kai Lake Live Medallion Cohort (30 Mastered Synthetic Patients -> 29 Active Gold Keys after 1 Consent Revocation; 1 Unmatched MDM Quarantined)",
        "truth_class": "SYNTHETIC_EXECUTED_COHORT",
        "source_provenance": "Deterministic zero-PHI synthetic generator in kairos_blind_lake.cli (seed-locked, 7 Veeva integration spokes).",
        "demo_role": "Exercises the live 11-stage KaiRos Lighthouse gate, k>=25 floor, differencing guard, and Dual-Witness CT Merkle Log in real time.",
    },
)


VEEVA_VS_KAI_COMPARISON: tuple[dict[str, str], ...] = (
    {
        "dimension": "1. 7-Spoke MDM & Bronze Landing (Cloaked Veeva-Like Intake)",
        "standard_veeva_vault": "7 spokes -> MDM match/resolve -> update-only Bronze landing -> exception queue for unmatched MDM IDs.",
        "kai_blind_datalake": "Kai Lake retains the full 7-spoke MDM & update-only Bronze discipline, plus cryptographic consent-purpose & patient/institute dividend verification before Silver/Gold promotion.",
        "pharma_advantage": "Eliminates unconsented secondary model training and enforces real-time revocation across derived Gold cohorts in Kai Lake.",
    },
    {
        "dimension": "2. Silver RE-ID Crosswalk Custody",
        "standard_veeva_vault": "Swaps MDM ID for pseudonymous analytics key in Silver, but the RE-ID crosswalk typically resides in the same cloud tenant under IAM roles.",
        "kai_blind_datalake": "Kai Lake isolates the RE-ID crosswalk exclusively inside the hospital/custodian HSM enclave; zero network or role path exists from Silver, Gold, or KaiRos.",
        "pharma_advantage": "Structural impossibility of sponsor or cloud-admin walk-back to patient MDM identity.",
    },
    {
        "dimension": "3. Quantum-Ready Compute-to-Data Enclave (The Cloak)",
        "standard_veeva_vault": "Plaintext cloud warehouse/lakehouse analytics; external AI models require row export or direct plaintext table access.",
        "kai_blind_datalake": "Kai Lake + KaiRos Quantum-Ready Enclave: NIST FIPS 203 (ML-KEM-768) & FIPS 204 (ML-DSA-65) PQC + Hardware TEE attestation (PCR0 + Anti-Replay Nonce + TTL <= 300s) + Ring-LWE CKKS FHE & Stochastic Cloak.",
        "pharma_advantage": "Merck (Tulisokibart/TL1A) and Regeneron (Retinal OCT) AI models touch live blind Gold cohorts in Kai Lake through KaiRos without raw row export or vendor key possession.",
    },
    {
        "dimension": "4. Clinical AI Output Assurance & Differencing Defense",
        "standard_veeva_vault": "Document/record management only; no cryptographic calibration gate or sub-cohort differencing guard on AI model outputs.",
        "kai_blind_datalake": "KaiRos sits directly on Kai Lake and enforces fail-closed post-decryption calibration/net-benefit assurance plus a symmetric cohort differencing guard (delta >= 3 patients).",
        "pharma_advantage": "Prevents silent calibration collapse (e.g. AUC preserved while slope explodes to 1.32e7) and blocks patient-reconstruction differencing attacks.",
    },
    {
        "dimension": "5. Audit Trail & Non-Equivocation",
        "standard_veeva_vault": "Single-vendor database audit log; cannot defeat split-view equivocation if privileged state is altered.",
        "kai_blind_datalake": "Private CT-style append-only Merkle transparency log signed by Org HSM (ML-DSA-65), RFC 3161 trusted timestamp, and >=2 independent witness co-signatures.",
        "pharma_advantage": "Mathematically verifiable non-equivocation and tamper evidence for FDA 21 CFR Part 11 & SOC 2 Processing Integrity diligence.",
    },
)


COMPLIANCE_CONTROLS: tuple[dict[str, Any], ...] = (
    {
        "framework": "ISO/IEC 27001:2022 & ISO/IEC 27701",
        "clauses": "A.8.24 (Use of Cryptography), A.8.3 (Access Restriction), PIMS 7.2 (Purpose Limitation & Consent)",
        "control_mechanism": "Custodian-held HSM secret keys, ML-KEM-768 post-quantum at-rest envelope, ML-DSA-65 model weight signatures, CKKS FHE in-use evaluation, and MDM consent-purpose enforcement.",
        "code_verifier": "MedallionDataLake.ingest_spoke_event + CustodianCrosswalkVault.attempt_external_walkback",
        "readiness_state": "CONTROL_IMPLEMENTED_IN_DEMO (External Certification Audit Required for Production)",
    },
    {
        "framework": "SOC 2 Type II (Trust Services Criteria)",
        "clauses": "CC6.1 (Logical Access), CC6.7 (Transmission/Movement), PI1.4 (Processing Integrity), C1.1 (Confidentiality)",
        "control_mechanism": "PCR0-pinned TEE attestation with Anti-Replay Nonce & 300s Key TTL, Egress-Zero sandbox attestation, fail-closed calibration gate (PI1.4), and k>=25 + Differencing Guard + DP ledger.",
        "code_verifier": "KaiRosLighthouse.evaluate_sponsor_request (11-stage fail-closed gate)",
        "readiness_state": "CONTROL_IMPLEMENTED_IN_DEMO (Type II Observation Period Required for Production)",
    },
    {
        "framework": "SOC 1 Type II (ICFR / Royalty & Usage Metering)",
        "clauses": "ITGC Change Management & Transaction Integrity for Sponsor Compute Metering",
        "control_mechanism": "Witnessed CT-style Merkle log records immutable sequence numbers, tenant epsilon consumption, and patient/institute dividend flags per computation.",
        "code_verifier": "MerkleTransparencyLog.append_receipt + verify_log_integrity",
        "readiness_state": "CONTROL_IMPLEMENTED_IN_DEMO (Scoped to Financial/Royalty Metering Integrity)",
    },
    {
        "framework": "HIPAA Security & Privacy Rule",
        "clauses": "45 CFR 164.312(a)(1), 164.312(b), 164.312(e)(1), 164.514(b) (Expert Determination / Safe Harbor Boundary)",
        "control_mechanism": "Silver quasi-identifier generalization, isolated custodian crosswalk, k>=25 cohort floor, symmetric differencing guard (delta >= 3), and zero raw PHI outside hospital boundary.",
        "code_verifier": "MedallionDataLake.revoke_consent + MIN_SYMMETRIC_DIFF_PATIENTS gate",
        "readiness_state": "CONTROL_IMPLEMENTED_IN_DEMO (BAA & Institutional Enclave Required Before PHI)",
    },
    {
        "framework": "FDA 21 CFR Part 11 & ASME V&V 40 Readiness",
        "clauses": "11.10(a) Validation, 11.10(e) Time-Stamped Audit Trails, 11.50 Signature Manifestation",
        "control_mechanism": "Deterministic circuit-digest binding, ML-DSA-65 model weight signature, RFC 3161 trusted timestamps, Org HSM + dual-witness signatures, and Truth-Class Provenance separation.",
        "code_verifier": "CircuitCatalogEntry parameter_profile_digest + MerkleTransparencyLog",
        "readiness_state": "CONTROL_IMPLEMENTED_IN_DEMO (Sponsor QMS Validation Required Per Intended Use)",
    },
)


def evaluate_compliance_readiness() -> dict[str, Any]:
    return {
        "schema": "kairos-compliance-readiness-v3",
        "posture_disclaimer": "Control-mapped synthetic reference architecture. Not a claim of completed third-party ISO/SOC audit opinion or live PHI custody.",
        "frameworks_mapped": len(COMPLIANCE_CONTROLS),
        "controls": list(COMPLIANCE_CONTROLS),
        "veeva_comparison": list(VEEVA_VS_KAI_COMPARISON),
        "truth_class_provenance": list(TRUTH_CLASS_PROVENANCE_TABLE),
    }
