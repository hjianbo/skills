---
name: emqx-hot-patch-package
description: Build EMQX hot patch zip packages from compiled .beam files, including a customer-facing README with the fixed issue, source version/PR metadata, official EMQX data directory guidance, c:lm() load steps, rollback steps, and checksums. Use when Codex needs to package one or more EMQX beam hot patches for customer delivery.
---

# EMQX Hot Patch Package

Create customer-deliverable EMQX hot patch zip files from already compiled
`.beam` files.

## Workflow

1. Confirm the target branch/release and current commit.
   - Prefer exact commits over vague release names.
   - Record the base commit, fix PR URL, patch commit, build profile, OTP version,
     app version if known, and the compiled beam path.

2. Compile the target profile before packaging.
   - For EMQX release-510 enterprise builds, `make emqx-enterprise-compile` is
     the expected compile target.
   - Use the release profile beam, not `test` or `check` profile beams.  For
     example:
     `_build/emqx-enterprise/lib/emqx_postgresql/ebin/emqx_postgresql.beam`.

3. Generate the package with `scripts/build_emqx_hot_patch_zip.py`.
   - Package format must be `.zip`, not `.beams`.
   - Package layout must be:
     ```text
     <package-name>/
     <package-name>/README.md
     <package-name>/patches/<module>.beam
     ```
   - The README must cite the official EMQX files/directories documentation:
     `https://docs.emqx.com/en/emqx/latest/deploy/install.html#files-and-directories`
   - Load and rollback steps should use `emqx eval 'c:lm().'`; do not use
     `load_abs` unless the user explicitly asks for that style.

4. Verify the package.
   - Run `unzip -l <package>.zip`.
   - Check `sha256sum <package>.zip` and the beam files.
   - Ensure the README no longer mentions obsolete package formats or commands.

## Script Usage

Example:

```bash
python3 ~/.agents/skills/emqx-hot-patch-package/scripts/build_emqx_hot_patch_zip.py \
  --package-name emqx-postgresql-r510-pr17627 \
  --output-dir . \
  --beam _build/emqx-enterprise/lib/emqx_postgresql/ebin/emqx_postgresql.beam \
  --fix-title "EMQX PostgreSQL Connector Hot Patch" \
  --fix-summary "Fixes PostgreSQL connector raw batch execution when prepared statements are disabled." \
  --fixed-errors "08P01 protocol_violation" \
  --fixed-errors "26000 invalid_sql_statement_name" \
  --source-branch ce/release-510 \
  --base-commit "$(git rev-parse ce/release-510)" \
  --fix-pr-url https://github.com/emqx/emqx/pull/17627 \
  --patch-commit "$(git rev-parse HEAD)" \
  --git-describe "$(git describe --tags --always --dirty)" \
  --build-profile emqx-enterprise \
  --otp-version "$(erl -noshell -eval 'io:format(\"~s\", [erlang:system_info(otp_release)]), halt().')" \
  --app-version "emqx_postgresql 0.2.11"
```

The script writes:

- `<package-name>/README.md`
- `<package-name>/patches/*.beam`
- `<package-name>.zip`

It also prints checksums and the zip listing.
