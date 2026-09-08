---
name: emqx-hot-patch-package
description: Use when packaging compiled EMQX beam hot patches for customer delivery.
---

# EMQX Hot Patch Package

1. Verify target release, source/patch commits, fix PR, build profile, OTP/app
   versions, and beam paths; report missing provenance. Reuse verified release
   beams or compile the target profile, never test/check artifacts.
2. Run `scripts/build_emqx_hot_patch_zip.py` relative to this skill directory;
   use `--help` for arguments. Supply build metadata, a concrete fix summary,
   and only applicable `--fixed-errors`. Choose unused output paths.
3. Inspect the zip layout (`<name>/README.md`, `<name>/patches/*.beam`), compare
   packaged/input SHA256 values, and review the README for the target deployment.
4. Retain the official directory documentation link, `emqx eval 'c:lm().'`,
   `code:which/1` verification, and rollback/restart fallback. Replacement
   instructions must preserve prior customer patches for rollback.
5. Deliver the zip path, SHA256, target build, and unverified runtime steps.
   Packaging does not authorize deployment.
