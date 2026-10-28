import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "usta_signing_policy", Path(__file__).resolve().parents[2] / "packaging/macos/signing_policy.py"
)
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


class MacOSSigningTests(unittest.TestCase):
    def test_release_cannot_silently_fall_back_to_ad_hoc(self):
        with self.assertRaisesRegex(ValueError, "Developer ID"):
            policy.resolve_identity(None, None, "")

    def test_ad_hoc_requires_explicit_development_opt_in(self):
        self.assertEqual(policy.resolve_identity(None, None, "", allow_ad_hoc=True), "-")
        with self.assertRaises(ValueError):
            policy.resolve_identity("-", None, "")

    def test_selects_valid_developer_id_by_name_and_checks_team(self):
        listing = "  1) " + "A" * 40 + ' "Developer ID Application: Test Publisher (ABCDE12345)"\n'
        result = policy.resolve_identity(
            "Developer ID Application: Test Publisher (ABCDE12345)", "ABCDE12345", listing
        )
        self.assertEqual(result, "A" * 40)
        with self.assertRaisesRegex(ValueError, "Team"):
            policy.resolve_identity("A" * 40, "WRONG12345", listing)

    def test_rejects_other_certificate_types_and_missing_private_keys(self):
        listing = "  1) " + "B" * 40 + ' "Apple Development: Test Publisher (ABCDE12345)"\n'
        with self.assertRaisesRegex(ValueError, "Developer ID"):
            policy.resolve_identity("B" * 40, "ABCDE12345", listing)
        with self.assertRaisesRegex(ValueError, "keychain"):
            policy.resolve_identity("C" * 40, "ABCDE12345", listing)

    def test_signed_bundle_must_keep_bundle_id_team_and_stable_requirement(self):
        details = (
            "Identifier=com.sedataym.usta\nTeamIdentifier=ABCDE12345\nflags=0x10000(runtime)\n"
        )
        requirement = 'designated => identifier "com.sedataym.usta" and anchor apple generic and certificate leaf[subject.OU] = "ABCDE12345"'
        policy.validate_signature(details + requirement, "ABCDE12345")
        for invalid in (
            details.replace("com.sedataym.usta", "other.app") + requirement,
            details.replace("ABCDE12345", "OTHER12345") + requirement,
            details + 'designated => cdhash H"abcd"',
            details.replace("flags=0x10000(runtime)", "flags=0x2(adhoc)") + requirement,
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                policy.validate_signature(invalid, "ABCDE12345")

    def test_self_signed_identity_is_pinned_and_not_silently_regenerated(self):
        listing = "  1) " + "D" * 40 + ' "USTA Local Code Signing"\n'
        self.assertEqual(policy.resolve_self_signed_identity(None, "D" * 40, listing), "D" * 40)
        with self.assertRaises(ValueError):
            policy.resolve_self_signed_identity("E" * 40, "D" * 40, listing)
        with self.assertRaises(ValueError):
            policy.resolve_self_signed_identity(None, "D" * 40, "")

    def test_self_signed_requirement_must_bind_to_the_pinned_certificate(self):
        details = "Identifier=com.sedataym.usta\nTeamIdentifier=not set\nflags=0x0(none)\n"
        requirement = 'designated => identifier "com.sedataym.usta" and anchor H"' + "D" * 40 + '"'
        policy.validate_self_signed_signature(details + requirement, "D" * 40)
        for invalid in (
            details + 'designated => identifier "com.sedataym.usta"',
            details + 'designated => cdhash H"' + "D" * 40 + '"',
            details + requirement.replace("D" * 40, "E" * 40),
            details.replace("flags=0x0(none)", "flags=0x10000(runtime)") + requirement,
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                policy.validate_self_signed_signature(invalid, "D" * 40)
