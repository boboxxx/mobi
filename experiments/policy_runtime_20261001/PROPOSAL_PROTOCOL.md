# Strong receiver-only verification baseline

The binary follow-up reduces serialization cost, but checking complete geometry
both before sending and after receiving duplicates work. A strong simple baseline
must test a sender that emits an UNVERIFIED candidate ray bundle and leaves the
complete geometric decision to the receiver. Source-selected data and metadata
are still current; the receiver may never act before verification. A proposal
is not itself a valid certificate.

Run the same 1,044 cases under two modes: full lookup plus full receiver coverage,
and bounded local lookup plus incremental receiver coverage. No complete source
coverage check in either mode. Rotate mode order. Save every emitted candidate,
including receiver rejections; record all bytes, the increased rejected-message
cost and timings. Receiver decisions must equal the original frozen geometry
decisions; each accepted bundle must have identical decoded integer rays and
metadata to the old packet. Both modes must emit identical candidate bytes.

Retain the 20 ms hypothetical link comparison for continuity, but explicitly
report that it does not price queueing or contention caused by rejected bundles.
Keep historical acquisition time and include receiver checking, timing predicate
bookkeeping and +1 ms sensitivity. Physical contracts are still unvalidated and
actual 50 ms go-policy tests have shown poor progress; timely conditional
verification is not evidence of successful driving.
