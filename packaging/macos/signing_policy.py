"""Require a pinned signing identity; self-signed and ad-hoc modes are explicit."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BUNDLE_ID = "com.sedataym.usta"


def resolve_identity(identity, team, listing, *, allow_ad_hoc=False):
    if not identity or identity == "-":
        if allow_ad_hoc:
            return "-"
        raise ValueError(
            "Developer ID Application certificate required. Set USTA_CODESIGN_IDENTITY and "
            "USTA_SIGNING_TEAM_ID. USTA_ALLOW_ADHOC=1 is for local development only."
        )
    if not team or not re.fullmatch(r"[A-Z0-9]{10}", team):
        raise ValueError("Set USTA_SIGNING_TEAM_ID to the fixed 10-character Apple Team ID.")
    entries = re.findall(r'\d+\)\s+([A-Fa-f0-9]{40})\s+"([^"\n]+)"', listing)
    matches = {
        (digest.upper(), name)
        for digest, name in entries
        if digest.lower() == identity.lower() or name == identity
    }
    if len(matches) != 1:
        raise ValueError("Select one valid signing identity with its private key in the keychain.")
    digest, name = matches.pop()
    if not name.startswith("Developer ID Application:"):
        raise ValueError("Distribution requires a Developer ID Application certificate.")
    if not name.endswith(f"({team})"):
        raise ValueError("Signing certificate Team ID differs from USTA_SIGNING_TEAM_ID.")
    return digest


def validate_signature(details, team):
    if f"Identifier={BUNDLE_ID}\n" not in details:
        raise ValueError("The application bundle identifier changed.")
    if f"TeamIdentifier={team}\n" not in details:
        raise ValueError("The application signing Team ID changed.")
    requirement = next((line for line in details.splitlines() if "designated =>" in line), "")
    if not requirement or "cdhash" in requirement.lower() or "anchor apple" not in requirement:
        raise ValueError(
            "The application must have a stable Apple certificate requirement, not a code hash."
        )
    if "(runtime)" not in details:
        raise ValueError("The signed distribution must enable hardened runtime.")


def load_self_signed_pin():
    folder = Path(__file__).resolve().parent
    pin = json.loads((folder / "self-signed-identity.json").read_text())
    certificate = (folder / "certs/usta-self-signed.cer").read_bytes()
    if (
        hashlib.sha1(certificate).hexdigest().upper() != pin["sha1"]
        or hashlib.sha256(certificate).hexdigest().upper() != pin["sha256"]
    ):
        raise ValueError(
            "Pinned self-signed certificate changed; do not generate a new identity for updates."
        )
    if pin["bundle_id"] != BUNDLE_ID:
        raise ValueError("Pinned bundle identifier changed.")
    return pin


def resolve_self_signed_identity(identity, fingerprint, listing):
    if identity and identity.upper() != fingerprint.upper():
        raise ValueError("Self-signed builds must use the pinned certificate fingerprint.")
    entries = re.findall(r'\d+\)\s+([A-Fa-f0-9]{40})\s+"([^"\n]+)"', listing)
    if not any(digest.upper() == fingerprint.upper() for digest, _ in entries):
        raise ValueError(
            "Pinned self-signed identity/private key not available in the keychain. Restore it; do not regenerate it."
        )
    return fingerprint.upper()


def validate_self_signed_signature(details, fingerprint):
    if f"Identifier={BUNDLE_ID}\n" not in details:
        raise ValueError("The application bundle identifier changed.")
    requirement = next(
        (line for line in details.splitlines() if "designated =>" in line), ""
    ).lower()
    anchored = "certificate leaf" in requirement or "anchor" in requirement
    if not anchored or "cdhash" in requirement or f'h"{fingerprint.lower()}"' not in requirement:
        raise ValueError(
            "Self-signed requirement must bind to the pinned certificate, not a code hash or identifier alone."
        )
    if "(runtime)" in details:
        raise ValueError("Self-signed Python bundles cannot use Developer ID library validation.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify-app")
    action.add_argument("--sign-app")
    args = parser.parse_args()
    try:
        identity = os.environ.get("USTA_CODESIGN_IDENTITY")
        team = os.environ.get("USTA_SIGNING_TEAM_ID")
        mode = os.environ.get("USTA_SIGNING_MODE", "developer-id")
        if mode not in ("developer-id", "self-signed"):
            raise ValueError("USTA_SIGNING_MODE must be developer-id or self-signed.")
        self_signed = mode == "self-signed"
        pin = load_self_signed_pin() if self_signed else None
        if args.sign_app:
            if not self_signed:
                raise ValueError("Post-build signing is only for the explicit self-signed mode.")
            listing = subprocess.check_output(
                ["security", "find-identity", "-v", "-p", "codesigning"], text=True
            )
            selected = resolve_self_signed_identity(identity, pin["sha1"], listing)
            subprocess.run(
                [
                    "codesign",
                    "--force",
                    "--deep",
                    "--options",
                    "0",
                    "--timestamp=none",
                    "--sign",
                    selected,
                    "--identifier",
                    BUNDLE_ID,
                    args.sign_app,
                ],
                check=True,
            )
        elif args.verify_app:
            details = subprocess.run(
                ["codesign", "-d", "--verbose=4", "-r-", args.verify_app],
                capture_output=True,
                text=True,
                check=True,
            )
            if self_signed:
                validate_self_signed_signature(details.stdout + details.stderr, pin["sha1"])
            else:
                validate_signature(details.stdout + details.stderr, team)
        else:
            listing = ""
            if self_signed or (identity and identity != "-"):
                listing = subprocess.run(
                    ["security", "find-identity", "-v", "-p", "codesigning"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
            if self_signed:
                selected = resolve_self_signed_identity(identity, pin["sha1"], listing)
            else:
                selected = resolve_identity(
                    identity, team, listing, allow_ad_hoc=os.environ.get("USTA_ALLOW_ADHOC") == "1"
                )
            print(selected)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"Signing preflight failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
