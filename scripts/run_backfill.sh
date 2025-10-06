#!/bin/bash
# Wrapper script to run backfill with suppressed gRPC/ALTS warnings

# Filter out ALTS and deprecation warnings from stderr while keeping error messages
python scripts/backfill_embeddings.py "$@" 2> >(grep -v "ALTS creds ignored" | grep -v "deprecated as of" | grep -v "UserWarning" >&2)
