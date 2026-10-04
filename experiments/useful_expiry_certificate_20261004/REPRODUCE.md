# Reproduce useful-expiry finite experiments

Restore inherited model/logical inputs with their published helpers; compile the
frozen native body proposer as in preceding units. All core sources and inputs
are listed by SHA in freeze.json. Run the six test cases with unittest discovery.

On a fresh clone, raw clouds/packets are carried losslessly in observations/*.tar.xz.
Run restore.py --restore /tmp/mobi-useful-replay --out /tmp/mobi-useful-storage.json
with fresh output paths. It checks every member, rejects unsafe/nonregular paths
and restores both capture trees plus canonical small metadata/episodes. Then run
audit.py --split certification --capture /tmp/mobi-useful-replay/certification_capture
--out /tmp/mobi-useful-cert-audit.json and analogously --split test with test_capture.
Run audit_certificate.py --out /tmp/mobi-useful-exact-certificate.json to independently
verify both exact statistical tests and every recorded progress label. Compare
bytes with the published sheng results. summarize.py summarizes all held-out cases.

No fresh CARLA capture is required for replay. Re-running physics is a different
experiment and must not overwrite frozen artifacts. No old certificate transfers
to this changed controller. Read PROTOCOL.md and RISK_ARGUMENT.md for law/assumptions.
