#!/usr/bin/env bash
# Logout Devin and then relog so the token is good for Cadence. 
#
# Usage: scripts/relog-devin

devin auth logout
devin auth login --force-manual-token-flow