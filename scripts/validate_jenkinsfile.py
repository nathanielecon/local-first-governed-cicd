#!/usr/bin/env python3
"""Validate the local Jenkinsfile delivery contract without starting Jenkins."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def strip_strings(text: str) -> str:
    result: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        chunk = text[index : index + 3]
        if chunk in {"'''", '"""'}:
            quote = chunk
            result.extend(" " * 3)
            index += 3
            while index < length and text[index : index + 3] != quote:
                result.append("\n" if text[index] == "\n" else " ")
                index += 1
            if index < length:
                result.extend(" " * 3)
                index += 3
            continue
        char = text[index]
        if char in {"'", '"'}:
            quote = char
            result.append(" ")
            index += 1
            while index < length:
                current = text[index]
                if current == "\\" and index + 1 < length:
                    result.extend("  ")
                    index += 2
                    continue
                result.append("\n" if current == "\n" else " ")
                index += 1
                if current == quote:
                    break
            continue
        result.append(char)
        index += 1
    return "".join(result)


def validate_braces(text: str) -> list[str]:
    stripped = strip_strings(text)
    depth = 0
    errors: list[str] = []
    for number, char in enumerate(stripped, start=1):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                errors.append(f"unexpected closing brace near character {number}")
                depth = 0
    if depth != 0:
        errors.append("unbalanced braces in Jenkinsfile")
    return errors


def require(pattern: str, text: str, errors: list[str], message: str) -> None:
    if not re.search(pattern, text, re.MULTILINE | re.DOTALL):
        errors.append(message)


def validate_text(text: str) -> list[str]:
    errors = validate_braces(text)
    require(r"^\s*pipeline\s*\{", text, errors, "missing top-level declarative pipeline block")
    require(r"\boptions\s*\{", text, errors, "missing options block")
    require(r"\btimestamps\s*\(\s*\)", text, errors, "missing timestamps() option")
    require(
        r"\bdisableConcurrentBuilds\s*\(\s*\)",
        text,
        errors,
        "missing disableConcurrentBuilds() option",
    )
    require(r"\bparameters\s*\{", text, errors, "missing parameters block")
    require(
        r"booleanParam\s*\(\s*name:\s*'PROMOTE_PRODUCTION'",
        text,
        errors,
        "missing PROMOTE_PRODUCTION boolean parameter",
    )
    require(r"\benvironment\s*\{", text, errors, "missing environment block")
    require(r"\bIMAGE_NAME\s*=\s*'delivery-api'", text, errors, "missing IMAGE_NAME contract")
    require(r"\bCI_PROVIDER\s*=\s*'jenkins'", text, errors, "missing CI_PROVIDER contract")
    require(r"\bstages\s*\{", text, errors, "missing stages block")
    for stage in (
        "Metadata",
        "Validate",
        "Build Once",
        "Staging",
        "Production Approval",
        "Production",
    ):
        require(
            rf"stage\s*\(\s*'{re.escape(stage)}'\s*\)",
            text,
            errors,
            f"missing required stage: {stage}",
        )
    require(r"docker build --pull", text, errors, "Build Once stage must build with --pull")
    require(r"docker push", text, errors, "Build Once stage must push the built image")
    require(r"image-digest\.txt", text, errors, "Build Once stage must retain image-digest.txt")
    require(
        r"input\s+message:\s*\"Promote verified digest\s+\$\{env\.IMAGE_DIGEST\}\s+to production\?\"",
        text,
        errors,
        "Production Approval stage must request human approval for the verified digest",
    )
    require(
        r"submitterParameter:\s*'APPROVED_BY'",
        text,
        errors,
        "Production Approval stage must record APPROVED_BY",
    )
    require(r"archiveArtifacts\b", text, errors, "post always must archive evidence artifacts")
    require(r"cleanWs\s*\(", text, errors, "post always must clean the workspace")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="Jenkinsfile")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    errors = validate_text(text)
    payload = {"path": str(path), "valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if errors:
            print(f"Jenkinsfile contract invalid: {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"Jenkinsfile contract valid: {path}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
