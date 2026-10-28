# Self-signed upgrade test — 2026-10-27

Tested on macOS 26.5.2, Apple Silicon. Both real USTA bundles target macOS 26+.

| Check | 0.1.11 (A) | 0.1.12 (B) |
| --- | --- | --- |
| Bundle identifier | com.sedataym.usta | com.sedataym.usta |
| Signature integrity / designated requirement | Passed | Passed |
| Screen Recording preflight | Allowed | Allowed |
| Accessibility preflight | Allowed | Allowed |
| Input Monitoring preflight | Allowed | Allowed |
| Actual screen capture (user verified) | Working | Working |
| Shift+Control+M hide/show (user verified) | Working after relaunch | Working |
| New privacy consent during A → B upgrade | — | None |
| RapidOCR / Apple Vision offline recognition | Passed | Passed |

Both versions use the pinned `USTA Local Code Signing` certificate with SHA-1
`4CCEC0AD3C63C8BEA5622471611F6F3E0FD5A24E`. Their designated requirements are identical:

```text
identifier "com.sedataym.usta" and certificate leaf = H"4ccec0ad3c63c8bea5622471611f6f3e0fd5a24e"
```

Their executable code hashes differ:

- A: `ec4b77671d1ca9837ab73f6bb28f186291d6c65f`
- B: `b7172b2e6307ee9a50506173af45f33fa00f21c5`

The old ad-hoc 0.1.10 application was backed up. On the initial migration to A,
only USTA's old ScreenCapture, ListenEvent and Accessibility records were reset,
and the user granted access manually. A was relaunched and both functions were
confirmed working. The application was then quit normally and replaced at
`/Applications/USTA.app` by B. No permissions were reset or changed between A and B.
Both versions were launched through Launch Services, avoiding Terminal permission
inheritance. Read-only permission diagnostics returned all three grants as allowed
before and after the upgrade. The user confirmed actual capture and shortcuts in B
without any new permission prompt.

Both DMGs were mounted read-only, their application signatures and public
certificate verified, and SHA-256 checksums checked. The private key remains in the
build user's Keychain and is absent from the repository and DMGs. The automated
suite passed 135 tests (32 skipped); Ruff and mypy also passed.

Artifacts: `dist/macos/USTA-0.1.11-macOS-arm64-selfsigned.dmg`,
`dist/macos/USTA-0.1.12-macOS-arm64-selfsigned.dmg`, and
`dist/macos/selfsigned-upgrade-test.json`. The installed app is 0.1.12.

This demonstrates permission retention for this upgrade on this Mac. These are
self-signed, non-notarized builds. Other Macs still require first-install approval;
macOS policy changes can require renewed consent. Preserve the pinned certificate,
its private key, bundle identifier and installation path for subsequent updates.
See [the build instructions](macos-dmg.md#free-persistent-self-signed-builds).
