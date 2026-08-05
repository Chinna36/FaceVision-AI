#!/usr/bin/env python
"""Test script to verify email credentials are loaded."""

import os
from pathlib import Path

print("\n=== Email Credentials Test ===\n")

# Try loading .env
try:
    from dotenv import load_dotenv, find_dotenv
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)
        print(f"[OK] Loaded .env from: {dotenv_path}\n")
except:
    print("[MANUAL] python-dotenv not available, using manual load\n")
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.split("#")[0].strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

# Check credentials
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
guardian_email = os.getenv("GUARDIAN_EMAIL")

print("Credentials Status:")
print(f"  SENDER_EMAIL:     {'[SET]' if sender_email else '[MISSING]'} {f'({sender_email})' if sender_email else ''}")
print(f"  SENDER_PASSWORD:  {'[SET]' if sender_password else '[MISSING]'}")
print(f"  GUARDIAN_EMAIL:   {'[SET]' if guardian_email else '[MISSING]'} {f'({guardian_email})' if guardian_email else ''}")

if sender_email and sender_password and guardian_email:
    print("\n[SUCCESS] All email credentials are loaded!")
else:
    print("\n[ERROR] Missing credentials. Please check your .env file:")
    print("\nRequired .env entries:")
    print("  SENDER_EMAIL=your.email@gmail.com")
    print("  SENDER_PASSWORD=your.app.password")
    print("  GUARDIAN_EMAIL=guardian@example.com")

print("\n=== Test Complete ===\n")
