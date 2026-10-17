/**
 * Clean-room structural fixture extracted via macOS Vision OCR from:
 * - Image 1: Veeva Vault Patient CRM + AgentVerse Orchestration + Bronze/Silver/Gold Medallion Lake
 * - Image 2: Origin AI / KBE Sovereign Quantum-Ready Clinical Intelligence Bridge (KaiRos Lighthouse)
 */

export const INTEGRATION_SPOKES = [
  { id: "frm_nursing", name: "FRM / Nursing", direction: "IN_OUT", payload: ["referral", "rx", "insurance", "consent", "mdm_id", "tasks", "case_status", "bv_pa_nursing"] },
  { id: "hub_partner", name: "Hub Partner + Nursing EHR", direction: "IN_OUT", payload: ["referral", "rx_routing", "mdm_id", "dispense", "ship_status", "fill_refill"] },
  { id: "specialty_pharmacy", name: "Specialty Pharmacy (Direct)", direction: "IN_OUT", payload: ["case_patient_status", "enrollment_demographics", "insurance", "rx", "consent"] },
  { id: "hcp_portal", name: "HCP Portal", direction: "IN_OUT", payload: ["content", "reminders", "status", "engagement", "patient_reported", "consent", "afford_enroll", "mdm_id"] },
  { id: "patient_app", name: "RediHealth / Patient App (Self-Enroll)", direction: "IN_OUT", payload: ["status", "self_enrollment_demographics", "insurance", "consent"] },
  { id: "bv_pa_partner", name: "BV / PA Partner (Benefits & Prior Auth)", direction: "IN_OUT", payload: ["bv_pa_request", "insurance", "rx", "provider", "mdm_id", "coverage_determination", "pa_status", "appeals", "sob"] },
  { id: "veeva_crm_hcp", name: "Veeva CRM (HCP)", direction: "IN_OUT", payload: ["scoped_case_status_activity", "field_interactions", "account_context"] }
];

export function mdmMatchAndConsentGate(record, masteredMdmRegistry, consentLedger) {
  if (!record || !record.mdm_id || !masteredMdmRegistry.has(record.mdm_id)) {
    return { status: "QUARANTINE_EXCEPTION_QUEUE", reason: "unmatched_mdm_id_never_create_patient" };
  }
  const consent = consentLedger.get(record.mdm_id);
  if (!consent || consent.status !== "ALLOW") {
    return { status: "DENIED_CONSENT", reason: "consent_check_failed_or_revoked" };
  }
  return { status: "ALLOW_BRONZE_LANDING", mdm_id: record.mdm_id };
}

export function promoteBronzeToSilverGold(bronzeRecord, custodianCrosswalkVault) {
  const opaqueAnalyticsKey = custodianCrosswalkVault.swapMdmForPseudonym(bronzeRecord.mdm_id);
  return {
    silver: {
      analytics_key: opaqueAnalyticsKey,
      quasi_identifiers_treated: true,
      reid_crosswalk_custodian_only: true
    },
    gold: {
      analytics_key: opaqueAnalyticsKey,
      walkback_to_mdm_blocked: true,
      features: bronzeRecord.features
    }
  };
}

export function kairosLighthouseEnclaveDispatch(sponsorRequest, enclavePolicy, kbeAssuranceGate) {
  if (sponsorRequest.requested_row_export || sponsorRequest.requested_vendor_decrypt) {
    return { decision: "REJECT_VENDOR_PATH", released: false };
  }
  return kbeAssuranceGate.evaluateBlindCompute(sponsorRequest, enclavePolicy);
}
