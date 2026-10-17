"""KaiRos Lighthouse & Kai Lake (Kai Blind Platform / KBE).

Synthetic-only reference demonstrator combining:
1. Veeva Vault-grade Patient CRM & AgentVerse MDM/Consent + Bronze/Silver/Gold Medallion governance
2. Sovereign Compute-to-Data Enclave (Custodian HSM + Hardware TEE attestation + CKKS FHE / Stochastic Cloak)
3. KaiRos Lighthouse Assurance Gate (public-safe black-box calibration & clinical net-benefit verification)
4. Private CT-style Witnessed Merkle Transparency Log + Differential Privacy & k>=25 Cohort Floor
"""

from .medallion_vault import (
    INTEGRATION_SPOKES,
    ConsentRecord,
    CustodianCrosswalkVault,
    MedallionDataLake,
    SpokeIngestEvent,
)
from .enclave_lighthouse import (
    CircuitCatalogEntry,
    EnclaveAttestation,
    KaiRosLighthouse,
    SponsorModelRequest,
)
from .transparency_log import (
    MerkleTransparencyLog,
    WitnessSignature,
)
from .compliance_matrix import (
    COMPLIANCE_CONTROLS,
    VEEVA_VS_KAI_COMPARISON,
    evaluate_compliance_readiness,
)

__all__ = [
    "INTEGRATION_SPOKES",
    "ConsentRecord",
    "CustodianCrosswalkVault",
    "MedallionDataLake",
    "SpokeIngestEvent",
    "CircuitCatalogEntry",
    "EnclaveAttestation",
    "KaiRosLighthouse",
    "SponsorModelRequest",
    "MerkleTransparencyLog",
    "WitnessSignature",
    "COMPLIANCE_CONTROLS",
    "VEEVA_VS_KAI_COMPARISON",
    "evaluate_compliance_readiness",
]
