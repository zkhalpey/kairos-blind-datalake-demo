# KaiRos Lighthouse & ATARI / Origin Blind DataLake (KBE v0.2)

**Synthetic-Only Reference Architecture Demonstrator**  
*Prepared by ATARI AI / Z-Cor LLC (Zain Khalpey, MD, PhD, FACS)*

---

## Executive Overview

This repository demonstrates how **KaiRos** (the sovereign clinical AI lighthouse and assurance control plane) and the **ATARI / Origin Blind DataLake** (powered by **KBE — Kai Blind Encryption**) fuse enterprise **Veeva Vault** data-governance discipline with a **hardware-attested, cryptographically cloaked compute-to-data enclave**.

External biopharma AI teams (such as **Merck** cardiovascular cohorts or **Regeneron** ophthalmology/retinal OCT models) can execute allowlisted AI inference over live blind **Gold** cohorts through the **KaiRos Lighthouse** without ever exporting patient rows, touching the Silver re-identification crosswalk, or holding decryption keys.

> **Disclosure & Governance Boundary:** This repository is a **synthetic-only reference demonstrator** (`0` real patient records, `0` PHI). It demonstrates the public-safe **Tier A** verification architecture and pre-computed calibration benchmarks ($n = 289,604$ STS cardiac benchmark and $n = 90$ paired OLIVES retinal OCT eyes). Proprietary **Tier B/C** internal fitting algorithms (`homoKai` / `CAPC` least-squares probe construction, internal parameter-fingerprint canonicalisation, and trade-secret drift tuning) remain held under counsel IP lock.

---

## 1. Five Core Architectural Layers (Veeva Vault Discipline + KBE Blind Enclave)

```text
  [7 Integration Spokes: FRM/Nursing · Hub/EHR · Specialty Pharmacy · HCP Portal · Patient App · BV/PA · Veeva CRM]
                                                     │
                                                     ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ LAYER 1: MDM & CONSENT PERIMETER (Veeva Vault CRM + AgentVerse Orchestration)                            │
  │  • Match/resolve on existing MDM ID; purpose-specific patient + institute consent & dividend check       │
  │  • Unmatched batch/CDC rows route to Exception Queue (update-only: never auto-creates new patients)      │
  └──────────────────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                                     ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ LAYER 2: CUSTODIAN-ISOLATED MEDALLION DATALAKE (Bronze -> Silver -> Gold)                                │
  │  • BRONZE: Encrypted CDC & daily/weekly batch feeds keyed by MDM ID                                      │
  │  • SILVER: Swaps MDM ID for opaque analytics key (ak1_...); treats quasi-identifiers (Age Band / ZIP-3)  │
  │  • CUSTODIAN HSM CROSSWALK: RE-ID crosswalk isolated in Hospital HSM; zero sponsor/cloud walk-back path  │
  │  • GOLD: Blind analytics-ready vectors & embeddings; real-time purge on MDM consent revocation           │
  └──────────────────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                                     ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ LAYER 3: SOVEREIGN COMPUTE-TO-DATA ENCLAVE (Hardware TEE + CKKS FHE + Stochastic Embedding Cloak)        │
  │  • Hospital HSM releases evaluation context only to PCR0-pinned, freshly attested TEE enclaves           │
  │  • Numeric vectors execute under Ring-LWE CKKS FHE; deep representations use model-specific Cloak        │
  │  • Bulk DICOM/video/free-text stay at rest under NIST FIPS 203 (ML-KEM-768) post-quantum envelopes       │
  └──────────────────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                                     ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ LAYER 4: KAIROS LIGHTHOUSE CLINICAL-OUTPUT ASSURANCE GATE                                                │
  │  • Catches silent FHE calibration collapse (where AUC holds at 0.6676 but slope explodes to 1.32e7       │
  │    and clinical net benefit at threshold 0.35 inverts negative)                                          │
  │  • Enforces cryptographic parameter fingerprint match + post-decryption calibration parity (slope 1.011) │
  └──────────────────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                                     ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ LAYER 5: ACCOUNTABLE RELEASE & WITNESSED CT MERKLE TRANSPARENCY LOG                                      │
  │  • Enforces k >= 25 cohort floor + per-tenant Differential Privacy cumulative epsilon budget             │
  │  • Appends body-free receipt to Private CT-style Merkle Log signed by Org HSM + RFC 3161 Timestamp       │
  │  • Co-signed by >= 2 Independent Witnesses (OracleKai & SparkKai) to defeat split-view equivocation      │
  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Why This Architecture Outperforms Standard Veeva Vault + Cloud Lakehouses

| Architectural Dimension | Standard Veeva Vault + Cloud Lakehouse | Kai Blind DataLake + KaiRos Lighthouse | Strategic Advantage for Pharma (Merck / Regeneron) |
|---|---|---|---|
| **1. Patient MDM & Consent Ingestion** | 7 spokes $\rightarrow$ MDM match/resolve $\rightarrow$ update-only Bronze landing $\rightarrow$ exception queue for unmatched MDM IDs. | Retains full Veeva 7-spoke MDM & update-only Bronze discipline, plus cryptographic consent-purpose & patient/institute dividend verification before Silver/Gold promotion. | Eliminates unconsented secondary model training and enforces real-time revocation across derived Gold cohorts. |
| **2. Silver RE-ID Crosswalk Custody** | Swaps MDM ID for pseudonymous analytics key in Silver, but the RE-ID crosswalk typically resides in the same cloud tenant under IAM roles. | Isolates the RE-ID crosswalk exclusively inside the hospital/custodian HSM enclave; zero network or role path exists from Silver, Gold, or KaiRos Lighthouse. | Structural impossibility of sponsor or cloud-admin walk-back to patient MDM identity. |
| **3. Data-in-Use Compute Perimeter** | Plaintext cloud warehouse/lakehouse analytics; external AI models require row export or direct plaintext table access. | Sovereign Compute-to-Data Enclave: Hardware TEE attestation (`PCR0` pinned) + Ring-LWE CKKS FHE for numeric circuits + fitted Stochastic Embedding Cloak for deep representations. | Merck and Regeneron AI models touch live blind Gold cohorts without raw row export or vendor key possession. |
| **4. Clinical AI Output Assurance** | Document/record management only; no cryptographic or clinical calibration gate on AI model outputs. | KaiRos Lighthouse enforces fail-closed post-decryption calibration & clinical net-benefit assurance (catching silent FHE slope collapse before release). | Prevents silent calibration collapse (e.g., AUC preserved at `0.6676` while calibration slope explodes to `1.32e7` and clinical net benefit inverts). |
| **5. Audit Trail & Non-Equivocation** | Single-vendor database audit log; cannot defeat split-view equivocation if privileged state is altered. | Private CT-style append-only Merkle transparency log signed by Org HSM, RFC 3161 trusted timestamp, and $\ge 2$ independent witness co-signatures. | Mathematically verifiable non-equivocation and tamper evidence for FDA 21 CFR Part 11 & SOC 2 Processing Integrity diligence. |

---

## 3. Cybersecurity & Regulatory Readiness Mapping (ISO 27001/27701, SOC 1 & 2 Type II, HIPAA, 21 CFR Part 11)

*Note: Framed honestly for enterprise pharma CISO/QA diligence as implemented architectural controls backed by automated tests in this repository; formal third-party audit opinions require an operating observation period over production infrastructure.*

| Framework & Clause | Implemented Technical Control in `kairos-blind-lake` | Executable Verification Path |
|---|---|---|
| **ISO/IEC 27001:2022 & ISO/IEC 27701**<br>`A.8.24`, `A.8.3`, `PIMS 7.2` | Custodian-held HSM secret keys, `ML-KEM-768` post-quantum at-rest envelope, `CKKS` FHE in-use evaluation, and MDM consent-purpose enforcement. | `MedallionDataLake.ingest_spoke_event` + `CustodianCrosswalkVault.attempt_external_walkback` |
| **SOC 2 Type II (Trust Services Criteria)**<br>`CC6.1`, `CC6.7`, `PI1.4`, `C1.1` | `PCR0`-pinned TEE enclave attestation, fail-closed calibration/net-benefit release gate (`PI1.4`), and $k \ge 25$ + Differential Privacy ($\epsilon$) budget enforcement. | `KaiRosLighthouse.evaluate_sponsor_request` (8-stage fail-closed gate) |
| **SOC 1 Type II (ICFR / Royalty Metering)**<br>`ITGC Transaction Integrity` | Witnessed CT-style Merkle log records immutable sequence numbers, tenant $\epsilon$ consumption, and patient/institute dividend flags per computation. | `MerkleTransparencyLog.append_receipt` + `verify_log_integrity` |
| **HIPAA Security & Privacy Rule**<br>`45 CFR 164.312`, `164.514(b)` | Silver quasi-identifier generalisation (`Age Band`, `ZIP-3`), isolated custodian crosswalk, $k \ge 25$ cohort floor, and real-time revocation purge. | `MedallionDataLake.revoke_consent` + `MIN_COHORT_K_ANONYMITY` gate |
| **FDA 21 CFR Part 11 & ASME V&V 40**<br>`11.10(a)`, `11.10(e)`, `11.50` | Deterministic circuit-digest binding, RFC 3161 trusted timestamps, Org HSM + dual-witness signatures, and pre-specified clinical acceptance bands. | `CircuitCatalogEntry.parameter_profile_digest` + `MerkleTransparencyLog` |

---

## 4. Live Sponsor Model Execution Matrix (Merck & Regeneron Scenarios)

Running `python3 -m kairos_blind_lake.cli` executes 7 deterministic scenarios across **Merck** (`merck-cardio-ai`) and **Regeneron** (`regeneron-ophtha-ai`) over 30 mastered synthetic patients (1 revoked $\rightarrow 29$ active Gold records, 1 unmatched MDM ID quarantined):

| Request ID | Sponsor Tenant & Model | KaiRos Lighthouse Verdict | Released Output / Assurance Metrics |
|---|---|---|---|
| `REQ-MERCK-001-PASS` | **merck-cardio-ai**<br>`merck-cabg-af-risk-v2` (CKKS FHE) | `RELEASE_ASSURED_FHE_AGGREGATE` | `n=29` \| `AUC=0.6676` \| `Slope=1.011` \| `Brier=0.1749` \| `NB@0.35=+0.0845` |
| `REQ-REGENERON-002-PASS` | **regeneron-ophtha-ai**<br>`regeneron-oct-fluid-persistence-v1` (Stochastic Cloak) | `RELEASE_CLOAKED_EMBEDDING_AGGREGATE` | `n=29` \| `AUC=0.7420` \| `Slope=1.004` \| `Brier=0.1610` \| `NB@0.35=+0.0910` |
| `REQ-MERCK-003-UNCALIBRATED-BLOCK` | **merck-cardio-ai**<br>`merck-cabg-af-risk-v2` (Uncalibrated FHE) | `WITHHOLD_UNCALIBRATED_SLOPE_COLLAPSE` | **WITHHELD** (Slope `1.32e7` outside `[0.90, 1.10]`; Net Benefit `-0.0412` harmful) |
| `REQ-SPONSOR-004-ROW-EXPORT-BLOCK` | **merck-cardio-ai**<br>`merck-raw-extract` | `REJECT_VENDOR_OR_ROW_EXPORT_PATH` | **REJECTED** (Raw row export & vendor decrypt are hard-blocked) |
| `REQ-REGENERON-005-FINGERPRINT-DRIFT` | **regeneron-ophtha-ai**<br>`regeneron-oct-fluid-persistence-v1` | `WITHHOLD_CRYPTO_FINGERPRINT_MISMATCH` | **WITHHELD** (Presented CKKS parameter digest diverges from calibrated profile) |
| `REQ-REGENERON-006-BULK-DICOM-BLOCK` | **regeneron-ophtha-ai**<br>`regeneron-raw-dicom-fhe` | `REJECT_FHE_ON_BULK_MODALITY` | **REJECTED** (Bulk DICOM/video stays at rest under `ML-KEM-768` envelope) |
| `REQ-REGENERON-007-DOSE-CLAIM-ABSTAIN` | **regeneron-ophtha-ai**<br>`regeneron-unvalidated-dose-comparator` | `ABSTAIN_UNSUPPORTED_CLINICAL_CLAIM` | **ABSTAINED** (No validated dose-comparative circuit in allowlisted catalog) |

---

## 5. Quickstart (Zero External Dependencies)

```bash
# 1. Run the full synthetic demonstration and generate JSON + HTML receipts
PYTHONPATH=src python3 -m kairos_blind_lake.cli

# 2. Run the automated verification suite (Medallion MDM/Consent, Crosswalk isolation,
#    Merkle split-view equivocation defense, and Merck/Regeneron KaiRos Lighthouse gates)
PYTHONPATH=src pytest -v
```

Generated artefacts land in:
- `receipts/kairos_blind_datalake_demo_receipt.json`
- `receipts/kairos_blind_datalake_dashboard.html`
- `docs/REAKAI_VEEVA_KAIROS_CLEANROOM_SPEC.md` (`reaKai` + JevKai Laya static clean-room specification, `rea_evidence_id=ev_684f50e259e4a2df8432b767f575097c9f69471c16e67a2ca4c747419996b416`)
