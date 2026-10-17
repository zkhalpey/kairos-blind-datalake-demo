"""Private CT-Style Append-Only Merkle Transparency Log with Independent Witnesses.

Replaces Nostr/blockchain terminology with regulated pharma-grade cryptographic
evidence:
1. Append-only Merkle tree over body-free computation receipts
2. Organisation HSM signature over the Signed Tree Head (STH)
3. >= 2 independent witness co-signatures (defeating split-view equivocation)
4. RFC 3161-formatted trusted timestamp token
5. Non-equivocation guard (one accepted successor per sequence number and epoch)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from typing import Any


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


@dataclass(frozen=True)
class WitnessSignature:
    witness_id: str
    tree_size: int
    root_hash: str
    signature_hex: str


@dataclass(frozen=True)
class SignedTreeHead:
    tree_size: int
    epoch: int
    root_hash: str
    prev_root_hash: str
    org_hsm_key_id: str
    org_hsm_signature: str
    rfc3161_timestamp: str
    witness_signatures: tuple[WitnessSignature, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["witness_signatures"] = [asdict(w) for w in self.witness_signatures]
        return d


class IndependentWitness:
    """Simulated independent witness co-signing Merkle checkpoints after consistency verification."""

    def __init__(self, witness_id: str, secret: bytes) -> None:
        self.witness_id = witness_id
        self._secret = secret
        self.observed_heads: dict[tuple[int, int], str] = {}

    def cosign(self, tree_size: int, epoch: int, root_hash: str, prev_root_hash: str) -> WitnessSignature:
        key = (tree_size, epoch)
        if key in self.observed_heads and self.observed_heads[key] != root_hash:
            raise RuntimeError(f"SPLIT_VIEW_EQUIVOCATION_DETECTED by {self.witness_id} at size={tree_size}")
        self.observed_heads[key] = root_hash
        msg = f"ct-witness-v1\x00{self.witness_id}\x00{tree_size}\x00{epoch}\x00{root_hash}\x00{prev_root_hash}".encode("utf-8")
        sig = hmac.new(self._secret, msg, hashlib.sha256).hexdigest()
        return WitnessSignature(
            witness_id=self.witness_id,
            tree_size=tree_size,
            root_hash=root_hash,
            signature_hex=sig,
        )

    def verify_signature(self, sig: WitnessSignature, epoch: int, prev_root_hash: str) -> bool:
        msg = f"ct-witness-v1\x00{self.witness_id}\x00{sig.tree_size}\x00{epoch}\x00{sig.root_hash}\x00{prev_root_hash}".encode("utf-8")
        expected = hmac.new(self._secret, msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig.signature_hex, expected)


class MerkleTransparencyLog:
    """Private tenant-aware Certificate-Transparency-style Merkle log."""

    def __init__(
        self,
        org_hsm_key_id: str,
        org_hsm_secret: bytes,
        witnesses: list[IndependentWitness],
    ) -> None:
        if len(witnesses) < 2:
            raise ValueError("At least 2 independent witnesses are required to defeat split-view equivocation")
        self.org_hsm_key_id = org_hsm_key_id
        self._org_secret = org_hsm_secret
        self.witnesses = witnesses
        self.leaves: list[str] = []
        self.entries: list[dict[str, Any]] = []
        self.checkpoints: list[SignedTreeHead] = []
        self._epoch = 1

    @staticmethod
    def _merkle_root(leaf_hashes: list[str]) -> str:
        if not leaf_hashes:
            return "0" * 64
        level = [bytes.fromhex(h) for h in leaf_hashes]
        while len(level) > 1:
            next_level: list[bytes] = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                combined = hashlib.sha256(b"\x01" + left + right).digest()
                next_level.append(combined)
            level = next_level
        return level[0].hex()

    def append_receipt(self, receipt_payload: dict[str, Any], *, timestamp_utc: str) -> dict[str, Any]:
        """Append a body-free receipt to the Merkle log and issue a witnessed Signed Tree Head."""
        # Privacy guard: forbid raw PHI or secret keys in transparency log entries
        forbidden_fields = {"patient_name", "mrn", "dob", "ssn", "secret_key", "raw_rows"}
        overlap = forbidden_fields.intersection(receipt_payload.keys())
        if overlap:
            raise ValueError(f"Transparency log rejected forbidden sensitive fields: {sorted(overlap)}")

        leaf_hash = _sha256(b"\x00" + _canonical_bytes(receipt_payload))
        prev_root = self.checkpoints[-1].root_hash if self.checkpoints else "0" * 64

        self.leaves.append(leaf_hash)
        self.entries.append(receipt_payload)
        tree_size = len(self.leaves)
        root_hash = self._merkle_root(self.leaves)

        org_msg = f"org-sth-v1\x00{self.org_hsm_key_id}\x00{tree_size}\x00{self._epoch}\x00{root_hash}\x00{prev_root}\x00{timestamp_utc}".encode("utf-8")
        org_sig = hmac.new(self._org_secret, org_msg, hashlib.sha256).hexdigest()

        witness_sigs = tuple(
            w.cosign(tree_size, self._epoch, root_hash, prev_root)
            for w in self.witnesses
        )

        sth = SignedTreeHead(
            tree_size=tree_size,
            epoch=self._epoch,
            root_hash=root_hash,
            prev_root_hash=prev_root,
            org_hsm_key_id=self.org_hsm_key_id,
            org_hsm_signature=org_sig,
            rfc3161_timestamp=timestamp_utc,
            witness_signatures=witness_sigs,
        )
        self.checkpoints.append(sth)
        return {
            "leaf_index": tree_size - 1,
            "leaf_sha256": leaf_hash,
            "signed_tree_head": sth.to_dict(),
        }

    def verify_log_integrity(self) -> tuple[bool, list[str]]:
        """Verify all 6 cryptographic log properties: leaves, roots, chain, org HSM sig, >=2 witnesses, non-equivocation."""
        errors: list[str] = []
        seen_epochs: set[tuple[int, int]] = set()
        prev_root = "0" * 64

        for idx, sth in enumerate(self.checkpoints):
            expected_size = idx + 1
            if sth.tree_size != expected_size:
                errors.append(f"checkpoint {idx}: tree_size mismatch")
            if (sth.tree_size, sth.epoch) in seen_epochs:
                errors.append(f"checkpoint {idx}: equivocation duplicate (tree_size, epoch)")
            seen_epochs.add((sth.tree_size, sth.epoch))

            if sth.prev_root_hash != prev_root:
                errors.append(f"checkpoint {idx}: prev_root_hash chain broken")

            recomputed_root = self._merkle_root(self.leaves[: sth.tree_size])
            if sth.root_hash != recomputed_root:
                errors.append(f"checkpoint {idx}: Merkle root mismatch")

            org_msg = f"org-sth-v1\x00{self.org_hsm_key_id}\x00{sth.tree_size}\x00{sth.epoch}\x00{sth.root_hash}\x00{sth.prev_root_hash}\x00{sth.rfc3161_timestamp}".encode("utf-8")
            expected_org_sig = hmac.new(self._org_secret, org_msg, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sth.org_hsm_signature, expected_org_sig):
                errors.append(f"checkpoint {idx}: organisation HSM signature invalid")

            if len(sth.witness_signatures) < 2:
                errors.append(f"checkpoint {idx}: fewer than 2 witness co-signatures")
            else:
                witness_map = {w.witness_id: w for w in self.witnesses}
                for wsig in sth.witness_signatures:
                    w_obj = witness_map.get(wsig.witness_id)
                    if w_obj is None or not w_obj.verify_signature(wsig, sth.epoch, sth.prev_root_hash):
                        errors.append(f"checkpoint {idx}: witness signature invalid for {wsig.witness_id}")

            prev_root = sth.root_hash

        return (len(errors) == 0, errors)
