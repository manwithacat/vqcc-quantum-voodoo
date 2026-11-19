#!/usr/bin/env bash
# Copyright 2026 James Barlow. Licensed under Apache-2.0.
# Builds the Quantum Voodoo DQI circuit from source:
#   1. Syed Asad Ali's v12 DQI generator (vendor/syed-asad-ali-v12/dqi_source.zip, Apache-2.0), unchanged, through its
#      own build.sh -> dqi_v12.kmb (must be 7cbe8ecf6f6e..., checked by his build.sh);
#   2. our inverse pass (qv/qv_inverse19_pass.py): the 20-Toffoli GF(2^6) inverse leaf -> a 19-Toffoli leaf at every
#      site that is provably clean at entry;
#   3. qv/qhdl_edit.py applies the edit -> dqi.kmb; its SHA-256 is checked against releases/<release>.json.
# No public circuit file is read at any step.
#
# Usage: ENGINE_DIR=<competition kickmix/> VERIFIERS_DIR=<competition verifiers/> PY=python3.13 \
#        [MAC_ENGINE=<kickmix.cpython-313-darwin.so>] bash build/build_dqi.sh OUT_DIR [RELEASE_JSON]
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?OUT_DIR}"; REL="${2:-}"
PY="${PY:-python3}"
: "${ENGINE_DIR:?set ENGINE_DIR to the competition's kickmix/ folder}"
: "${VERIFIERS_DIR:?set VERIFIERS_DIR to the competition's verifiers/ folder}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

echo "== 1. Syed Asad Ali's v12 DQI generator (unchanged)"
(cd "$WORK" && unzip -q "$HERE/vendor/syed-asad-ali-v12/dqi_source.zip")
mkdir -p "$WORK/v12out"
WORK="$WORK/gen" PY="$PY" bash "$WORK/dqi_source/build.sh" "$ENGINE_DIR" "$VERIFIERS_DIR" "$WORK/v12out"

echo "== 2. inverse pass"
"$PY" -I "$HERE/qv/qv_inverse19_pass.py" "$WORK/v12out/dqi.kmb" "$HERE/qv/templates/gf64_inverse20_old.kmb" \
    "$HERE/qv/templates/gf64_inverse19_records.kmb" "$OUT/inverse19"

echo "== 3. apply"
"$PY" -I -c 'import sys; sys.path.insert(0, sys.argv[1]); import qhdl_edit as E
E.edit_file(sys.argv[2], open(sys.argv[3]).read(), sys.argv[4], sys.argv[4] + ".map.json")' \
    "$HERE/qv" "$WORK/v12out/dqi.kmb" "$OUT/inverse19/inverse19.qed" "$OUT/dqi.kmb"
H="$(shasum -a 256 "$OUT/dqi.kmb" | cut -c1-64)"
echo "BUILT dqi.kmb $H"
if [ -n "$REL" ]; then
  WANT="$("$PY" -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["circuits"]["dqi.kmb"])' "$REL")"
  [ "$H" = "$WANT" ] || { echo "SHA-256 differs from $REL ($WANT)" >&2; exit 1; }
  echo "matches $REL"
fi
