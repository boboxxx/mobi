# Explicit execution provenance

The currently online Tailscale peer advertised as sheng is Windows host
DESKTOP-UGDDO8T at100.109.48.32. CARLA0.9.15 is the installed WindowsNoEditor
server. Algorithm/capture/audit Python runs in Ubuntu20.04 WSL as user sheng,
using /home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python.
Independent package/geometry/statistical verification runs on the local Mac.

The local SSH alias also named sheng has a separately configured public address;
that connection timed out during this preflight. An additional previously known
route did not connect either. We do not infer that those routes identify the
online Windows peer. This experiment does not claim execution on an independently
reachable Linux cluster merely because a WSL user or Tailscale peer is named sheng.
Prior Windows/WSL captures retain their frozen process/executable/cleanup records;
this note clarifies their environment rather than altering historical artifacts.

Simulation source/RX message timing remains measured-delay co-simulation. Actual
RPC between the WSL client and Windows simulator, SSH/SCP publication traffic,
and the modeled20Mbps evidence link are distinct; none is a V2V radio trial.
