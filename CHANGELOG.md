# Changelog

Dates are UTC. Each entry names the release record in `releases/`.

## 2026-11-19: repository created; QV-DQI-1

- Vendored Syed Asad Ali's v12 generators (DQI and inverse square root; Apache-2.0), unchanged.
- `build/build_dqi.sh`: one command from source to `dqi.kmb`. Step 1 runs the v12 generator unchanged and reproduces
  its published output byte for byte (`7cbe8ecf6f6e…`, 889 qubits).
- **QV-DQI-1** (`releases/2026-11-19-qv-dqi-1.json`): our inverse pass replaces the 20-Toffoli GF(2^6) clean-inverse
  leaf by a 19-Toffoli leaf at the 100 of its 108 sites that are provably clean at entry. 100 fewer Toffolis per shot,
  889 qubits unchanged; 48-draw expected cost −0.026% against the unmodified generator output, with the same failing
  draws (local results).
- Next: the inverse-square-root build, chemistry from our own loader emitter, and further passes.
