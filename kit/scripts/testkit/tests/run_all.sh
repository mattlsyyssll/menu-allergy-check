#!/bin/bash
# Runs every self-test of the hackathon test-kit library and the PDF and gallery makers. Prints ALL PASS or the failures.
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(dirname "$(dirname "$HERE")")"
TK="$SCRIPTS/testkit"
fails=()
run() {
  local out
  out=$(/usr/bin/python3 -I "$@" 2>&1); local rc=$?
  echo "$out" | tail -1
  if [ $rc -ne 0 ]; then fails+=("$*"); fi
}
for m in cases keys score replay freeze runs trace; do run "$TK/$m.py" --selftest; done
run "$SCRIPTS/make_pdf.py" --selftest
run "$SCRIPTS/gallery.py" --selftest
if [ ${#fails[@]} -eq 0 ]; then echo "ALL PASS"; else echo "FAILURES:"; printf '  %s\n' "${fails[@]}"; exit 1; fi
