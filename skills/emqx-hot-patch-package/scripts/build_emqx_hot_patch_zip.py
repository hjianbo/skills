#!/usr/bin/env python3
"""Build an EMQX hot patch zip from compiled beam files."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path


DOCS_URL = "https://docs.emqx.com/en/emqx/latest/deploy/install.html#files-and-directories"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()


def beam_md5(path: Path) -> str | None:
    expr = (
        f'{{ok,{{_,MD5}}}}=beam_lib:md5("{path}"), '
        'io:format("~s", [binary:encode_hex(MD5)]), halt().'
    )
    try:
        return run(["erl", "-noshell", "-eval", expr])
    except Exception:
        return None


def module_name(path: Path) -> str:
    if path.suffix != ".beam":
        raise SystemExit(f"beam path must end in .beam: {path}")
    return path.stem


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def render_readme(args: argparse.Namespace, copied_beams: list[Path], output_root: Path) -> str:
    fixed_errors = args.fixed_errors or [
        "protocol_violation",
        "invalid_sql_statement_name",
    ]
    modules = [module_name(p) for p in copied_beams]
    beam_lines: list[str] = []
    for beam in copied_beams:
        md5 = beam_md5(beam)
        beam_lines.append(f"{rel(beam, output_root)}")
        beam_lines.append(f"sha256: {sha256(beam)}")
        if md5:
            beam_lines.append(f"beam md5: {md5}")
        beam_lines.append("")
    beam_block = "\n".join(beam_lines).strip()
    error_lines = "\n".join(f"- `{err}`" for err in fixed_errors)
    rm_lines = "\n".join(
        f'   rm -f "$EMQX_DATA_DIR/patches/{module}.beam"' for module in modules
    )
    which_lines = "\n".join(
        f'   "$EMQX_HOME/bin/emqx" eval \'code:which({module}).\''
        for module in modules
    )
    expected_lines = "\n".join(
        f'   "<EMQX_DATA_DIR>/patches/{module}.beam"' for module in modules
    )
    normal_lines = "\n".join(
        f'   "<EMQX_HOME>/lib/*/ebin/{module}.beam"' for module in modules
    )

    return textwrap.dedent(
        f"""\
        # {args.fix_title}

        This zip package contains a hot patch for EMQX.

        ## What This Fixes

        {args.fix_summary}

        Errors that may be addressed by this patch include:

        {error_lines}

        ## Build Information

        - Source branch: `{args.source_branch}`
        - Base commit: `{args.base_commit}`
        - Fix PR: {args.fix_pr_url}
        - Patch commit: `{args.patch_commit}`
        - Git describe: `{args.git_describe}`
        - Build profile: `{args.build_profile}`
        - Erlang/OTP used for build: `{args.otp_version}`
        - Patched application: `{args.app_version}`

        Patched beam files:

        ```text
        {beam_block}
        ```

        Use this package only on the matching EMQX build line, or rebuild the
        beam files from the same source for the exact target release/OTP
        combination.

        ## Install And Load

        Apply the patch on every EMQX node.  A rolling procedure is recommended.

        1. Extract the package on the target host:

           ```bash
           unzip {args.package_name}.zip
           cd {args.package_name}
           ```

        2. Find the EMQX data directory.

           Refer to the official EMQX "Files and Directories" documentation:
           {DOCS_URL}

           The default directories are:

           | Installation method | `EMQX_HOME` | `EMQX_DATA_DIR` |
           | --- | --- | --- |
           | tar.gz | `<EMQX_INSTALL_DIR>` | `<EMQX_INSTALL_DIR>/data` |
           | RPM/DEB | `/usr/lib/emqx` | `/var/lib/emqx` |
           | Docker | `/opt/emqx` | `/opt/emqx/data` |

           The `data` directory can be configured.  Use the actual configured
           data directory for the target node.  The same official documentation
           describes `data/patches` as the directory that stores `.beam` files
           for hot patches.

        3. Copy the patched beam files to the EMQX data patches directory.

           Set `EMQX_HOME` and `EMQX_DATA_DIR` according to the table above and
           your actual deployment:

           ```bash
           EMQX_HOME=/usr/lib/emqx
           EMQX_DATA_DIR=/var/lib/emqx

           install -d "$EMQX_DATA_DIR/patches"
           cp patches/*.beam "$EMQX_DATA_DIR/patches/"
           ```

        4. Hot-load the patched modules:

           ```bash
           "$EMQX_HOME/bin/emqx" eval 'c:lm().'
           ```

           The command should reload modified modules from the EMQX code path.
           The exact returned list may include more than one module.  Verify the
           patched modules with the next step.

        5. Verify that the patched modules are loaded from the data patches
           directory:

           ```bash
{which_lines}
           ```

           Expected result:

           ```erlang
{expected_lines}
           ```

        6. If the node is restarted, verify `code:which/1` again.  If the
           patched modules are not loaded, run the hot-load command again.

        ## Rollback

        1. Remove the patched beam files:

           ```bash
           EMQX_HOME=/usr/lib/emqx
           EMQX_DATA_DIR=/var/lib/emqx

{rm_lines}
           ```

        2. Reload modified modules:

           ```bash
           "$EMQX_HOME/bin/emqx" eval 'c:lm().'
           ```

        3. Verify that the modules are no longer loaded from `data/patches`:

           ```bash
{which_lines}
           ```

           The path should point back to the normal EMQX release lib directory,
           for example:

           ```erlang
{normal_lines}
           ```

        If hot rollback does not load the original modules as expected, remove
        the beam files from `data/patches` and restart the node.
        """
    )


def build_zip(package_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(package_dir.rglob("*")):
            if path.name.startswith("."):
                continue
            zf.write(path, path.relative_to(package_dir.parent))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--beam", action="append", required=True, help="compiled .beam file")
    parser.add_argument("--fix-title", required=True)
    parser.add_argument("--fix-summary", required=True)
    parser.add_argument("--fixed-errors", action="append", default=[])
    parser.add_argument("--source-branch", default="unknown")
    parser.add_argument("--base-commit", default="unknown")
    parser.add_argument("--fix-pr-url", default="unknown")
    parser.add_argument("--patch-commit", default="unknown")
    parser.add_argument("--git-describe", default="unknown")
    parser.add_argument("--build-profile", default="unknown")
    parser.add_argument("--otp-version", default="unknown")
    parser.add_argument("--app-version", default="unknown")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    package_dir = output_dir / args.package_name
    patches_dir = package_dir / "patches"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    patches_dir.mkdir(parents=True)

    copied_beams: list[Path] = []
    for beam_arg in args.beam:
        src = Path(beam_arg).resolve()
        if not src.is_file():
            raise SystemExit(f"beam file not found: {src}")
        dst = patches_dir / src.name
        shutil.copy2(src, dst)
        copied_beams.append(dst)

    readme = render_readme(args, copied_beams, package_dir)
    (package_dir / "README.md").write_text(readme, encoding="utf-8")

    zip_path = output_dir / f"{args.package_name}.zip"
    build_zip(package_dir, zip_path)

    print(f"package: {zip_path}")
    print(f"package_sha256: {sha256(zip_path)}")
    print("files:")
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            print(f"  {name}")
    print("beam_sha256:")
    for beam in copied_beams:
        print(f"  {beam.name}: {sha256(beam)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
