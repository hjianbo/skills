---
name: emqx-hot-patch-package
description: Package compiled EMQX beam hot patches as customer-deliverable zip files with provenance, load/rollback instructions, and checksums.
---

# EMQX Hot Patch Package

## Prepare

- Verify the target release, source and patch commits, fix PR, build profile,
  OTP version, application version, and beam paths. Report missing provenance.
- Use beams from the matching release profile, not test/check builds. Reuse verified
  compiled artifacts; otherwise compile with the target checkout's build command.
- Resolve `scripts/build_emqx_hot_patch_zip.py` relative to this skill directory.
  Run it with `--help` for arguments. Supply the verified build metadata and a
  concrete fix summary; pass `--fixed-errors` only for errors this patch addresses.

## Package and verify

- Choose an unused package name and output directory. The helper refuses to replace
  existing packages. It produces `<name>.zip` containing `<name>/README.md` and
  `<name>/patches/*.beam`, and prints SHA256 checksums.
- Inspect the archive listing, compare packaged beams with the input checksums,
  and review the generated README for the exact target before delivery.
- Keep the official EMQX files/directories documentation link in the README and
  verify deployment paths against the target release. Load with `emqx eval 'c:lm().'`
  and verify `code:which/1`; document rollback and its restart fallback.
- Check for existing customer patches before applying replacement instructions;
  rollback must restore any previous patch. Packaging does not authorize deployment.
- Report the zip path, checksum, target build, and any unverified runtime steps.
