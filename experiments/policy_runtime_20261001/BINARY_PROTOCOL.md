# Lossless wire follow-up, fixed before execution

The four JSON-runtime ablations retain 87 geometry packets but no timely stop
gate. Test whether serialization/validation overhead remains material using the
same integer rays, uncertainty contracts, body policy and deadlines.

Run 1,044 cases per method: JSON combined optimization, binary with full lookup
and full coverage checks, and binary with local lookup plus incremental cell
checks. Rotate method order. Require decoded origin coordinates, complete ray
records, scope/contracts/policy/speed/yaw/reference/horizon/sequence to equal the
frozen original successful packet, and require failures to match. Wire bytes
necessarily differ; never call this byte-equivalent to the JSON packet.

PVX1 wire contains a bounded prefix, canonical metadata, signed 32-bit millimeter
coordinates, unsigned 32-bit origin indices and signed 32-bit microsecond ray
ages, plus SHA-256 for corruption detection. The receiver reconstructs absolute
integer observation times and rejects future/overage rays, illegal indices,
coordinate/metadata range errors, malformed sizes, wrong contracts and expiry.
It then reconstructs all current-ray uncertainty and coverage as before.

Preserve emitted binary packets once per case, report all packet hashes and
byte sizes, and replay source-backed validation. Measure generation, receiver
validation and timing-predicate bookkeeping; include historical acquisition,
20 ms modeled link and a separate +1 ms sensitivity. No claim of measured
wireless delay, calibrated physical assumptions or evidence-guided driving.
