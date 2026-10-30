#!/usr/bin/env bash
# Source with the absolute package.conf path. Profiles never rename the machine.
[[ -r "$1" ]] || { echo "Missing packaged configuration: $1" >&2; exit 1; }
source "$1"
[[ "$LESSON3_VERSION" =~ ^v[0-9]+\.[0-9]+$ ]] || { echo "Invalid release" >&2; exit 1; }
case "$ARES_PROFILE" in
  production) ARES_ALIAS=ares.local ;;
  test) ARES_ALIAS=ares-test.local ;;
  *) echo "Unknown packaged profile: $ARES_PROFILE" >&2; exit 1 ;;
esac
ARES_URL="http://$ARES_ALIAS"
LESSON3_URL="$ARES_URL:3001"
export LESSON3_VERSION ARES_PROFILE ARES_ALIAS ARES_URL LESSON3_URL
