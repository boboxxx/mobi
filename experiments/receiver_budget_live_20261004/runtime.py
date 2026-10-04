"""Fixed processing budget; no imported whole-episode risk certificate."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('receiver_budget_parent_runtime',Path(__file__).resolve().parents[1]/'ego_policy_certificate_20261004/runtime.py');PARENT=importlib.util.module_from_spec(spec);spec.loader.exec_module(PARENT)
for name in dir(PARENT):
 if not name.startswith('__'):globals()[name]=getattr(PARENT,name)
BUDGET=20000
# .75m/s * (.300+.020)s + .020m margin, plus full3D ego radius.
def action_radius(body):return math.ceil(math.sqrt(sum(e*e for e in body['extent']))*1000000)+260000
PARENT.action_radius=action_radius
PARENT.BASE.action_radius=action_radius
_spec=importlib.util.spec_from_file_location('receiver_budget_fixed_schedule',Path(__file__).resolve().parent/'schedule.py');_schedule=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_schedule)
ready_at=_schedule.ready_at;usable_by=_schedule.usable_by;command_clock=_schedule.command_clock
