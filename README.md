# VQCC Quantum Voodoo

Source-built circuits for the Kaggle competition
[Google Quantum AI – Verifiable Quantum Circuit Compilation](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation),
by James Barlow (Kaggle `manwithacat`), with AI assistance (Claude, Anthropic).

Every circuit released here is **generated from source by the code in this repository**. No public `.kmb` or `.kmx`
circuit file is read as an input at any step. Open-source generators we build on are vendored here unchanged, with
their licences and notices, and our own changes are passes and builders in `qv/` and `build/`. Each release records
its inputs, the SHA-256 of every circuit and the verification results in `releases/`.

Licence: Apache-2.0 (see `LICENSE` and `NOTICE`).

## Credit and lineage

- **Syed Asad Ali** is the original builder of the inverse-square-root and DQI generators this repository starts
  from (Kaggle dataset [`syed3000/vqcc-own-circuit-portfolio`](https://www.kaggle.com/datasets/syed3000/vqcc-own-circuit-portfolio),
  version 12, Apache-2.0). His licence asks that every derived work name him first as the original builder and carry
  his NOTICE; it is reproduced in `vendor/syed-asad-ali-v12/NOTICE`. His archives are vendored byte-for-byte in
  `vendor/syed-asad-ali-v12/` (SHA-256 in `vendor/syed-asad-ali-v12/SOURCE.md`).
- Our additions are listed by date in `CHANGELOG.md`. The 19-Toffoli GF(2^6) inverse leaf was constructed by our
  research agent (history caching with free phase repayment); the pass that places it, and the build, are ours.

## Build

DQI (about 4 minutes, about 1 GB memory; Python 3.13 with NumPy; the competition's `kickmix/` and `verifiers/`
folders):

```sh
ENGINE_DIR=/path/to/competition/kickmix VERIFIERS_DIR=/path/to/competition/verifiers PY=python3.13 \
  bash build/build_dqi.sh out/ releases/2026-11-19-qv-dqi-1.json
```

It runs Syed Asad Ali's v12 generator unchanged (it checks its own output hash, `7cbe8ecf6f6e…`), then our inverse
pass, then checks the final SHA-256 against the release record. On macOS also set `MAC_ENGINE` to a macOS build of the
kickmix engine (see the vendored README).

The invsqrt and chemistry builds will be added as they are moved onto this pipeline (see `CHANGELOG.md`).

## Verification

Each release lists the unmodified official verifier result (run locally at the default salt) and, for DQI, the
expected cost over 48 fixed draws together with a paired comparison against the unmodified generator output (same
failing draws and failed-shot counts). These are local results, not leaderboard scores.

## Status

See `CHANGELOG.md` and `releases/`.
