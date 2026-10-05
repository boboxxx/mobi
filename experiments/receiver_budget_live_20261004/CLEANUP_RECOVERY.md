The capture and independent audit finished all36 episodes. Stop-Process succeeded
for ownerPID81732 (executable/start-time identity checked); the launcher exited.
The frozen stop script wrote the historical Windows temporary basename
mobi-ego-policy-cert-stopped.json, while the shell wrapper tried to copy
mobi-receiver-budget-server-stopped.json. Its original stop log and copy failure
are retained. recover_cleanup.py only validates the existing stop JSON against
start identity and the actual stop log, then copies that receipt into this new
result directory. No actor, source, metric, core code or old published result is
changed; no recapture or server restart. This is an artifact-copy correction,
not a safety/physics correction.
