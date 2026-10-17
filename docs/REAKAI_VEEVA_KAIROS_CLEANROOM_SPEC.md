---
schema: reakai-clean-room-spec-v1
target_name: reakai_target
rea_evidence_id: ev_684f50e259e4a2df8432b767f575097c9f69471c16e67a2ca4c747419996b416
parent_evidence_id: ev_684f50e259e4a2df8432b767f575097c9f69471c16e67a2ca4c747419996b416
root_artifact_sha256: 4c2722aaded089843264842dd83e6dbe8f4792939a345ce20038de600646f9ea
laya_decider: laya-d42786b-laya-lanes-q2
copied_source_code: false
target_executed: false
---
# Clean-Room Behavioral Specification: `reakai_target`

## 1. Provenance & Clean-Room Assurance
- **Target Artifact:** `/Users/zainkhalpey/workspace/kairos-blind-datalake-demo/reakai_target`
- **REA Static Mode:** `complete` (`rea-agents@6.4.0`)
- **REA Evidence ID:** `ev_684f50e259e4a2df8432b767f575097c9f69471c16e67a2ca4c747419996b416`
- **Root Artifact SHA-256:** `4c2722aaded089843264842dd83e6dbe8f4792939a345ce20038de600646f9ea`
- **Target Immutability:** `target_hashes_unchanged=True`, `target_executed=False`
- **JevKai Laya Compression:** `426947` B -> `6299` B (`98.52%` reduction; `5/7` nodes retained, `2` vendor/low-signal nodes quarantined).
- **Clean-Room Rule:** This specification contains only AST structural graph metadata, module/export signatures, and interface boundaries. Zero lines of target source code are copied.

## 2. Entrypoints & Module Inventory (Inputs)
- **`veeva_vault_patient_crm_architecture.js`** (`javascript-module` / `source-module`): format=`esm`, imports=`0`, exports=`4`, Laya `P(load)=0.2414`, authority=`ast-static-analysis` (`exact`).

## 3. Exported Interfaces & Public Surface (Outputs)
- **Export `kairosLighthouseEnclaveDispatch`** from `veeva_vault_patient_crm_architecture.js` (`export`): Laya `P(load)=0.4671`, node_id=`jag_node_7bdd63ba3abd9e2cf135cefb57b9014b81f56a5cb6eff19dafc66cf7506d50cd`.
- **Export `promoteBronzeToSilverGold`** from `veeva_vault_patient_crm_architecture.js` (`export`): Laya `P(load)=0.2126`, node_id=`jag_node_12c49a9f3f6a64e4d2ce2eb8f79e692c3ae4eeabdb6600239ea38ed3213cf986`.
- **Export `INTEGRATION_SPOKES`** from `veeva_vault_patient_crm_architecture.js` (`export`): Laya `P(load)=0.0839`, node_id=`jag_node_6b8307a6b040297a459de5bfaea3771cb925d9ce13a8fadc5e522ce1f078d717`.

## 4. SDK, Runtime & IPC Boundaries
- **Boundary `veeva_vault_patient_crm_architecture.js:mdmMatchAndConsentGate:return-shapes`** (`export-return-shapes`, resolution=`external-boundary`): Laya `P(load)=0.3017`.

## 5. JevKai Gate Verdicts (`step_delegate` & `stop_gate`)
- **`step_delegate`:** route=`HUMAN_REQUIRED`, candidate=`None`, reasons=`['decider_chose_escape_hatch']`
- **`stop_gate`:** route=`SHADOW_ACCEPT`, advised=`goal_not_met`, noul=`0.0354`

## 6. Clean-Room Verification & Test Obligations (`codexKai`)
- [ ] **Contract Parity:** Re-implement the module entrypoints in Section 2 and exported bindings in Section 3 from scratch in an isolated directory without reading target source files.
- [ ] **Boundary Mocking:** Provide clean mocks/adapters for every external SDK/IPC boundary listed in Section 4.
- [ ] **Static Graph Equivalence:** Run `reakai_laya_bridge.py` on the new clean-room implementation and verify that its exported node kinds and entrypoint roles match Sections 2–4.
- [ ] **Zero Target Mutation:** Confirm `target_hashes_unchanged=True` and `target_executed=False` in the accompanying JSON receipt.

## 7. Known Static Limitations
- CommonJS and ESM binding relationships were recovered from inert syntax and resolved only within the inventoried artifact container.
- JavaScript and HTML were parsed as inert text; bundle bootstrap code was never executed.
- Static imports, entrypoints, workers, endpoints, and storage relationships do not prove runtime execution.
- Static paths and relationships may remain unresolved when expressions are dynamic or obfuscated.
- Webpack/Rspack factories were recovered from AST literals; REA did not invoke push handlers or bundle bootstrap code.
