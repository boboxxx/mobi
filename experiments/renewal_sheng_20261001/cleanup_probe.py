import json
from pathlib import Path
import carla
client=carla.Client('100.109.48.32',2000);client.set_timeout(10)
world=client.get_world();actors=world.get_actors()
report=dict(remaining_vehicles=len(actors.filter('vehicle.*')),remaining_sensors=len(actors.filter('sensor.*')),synchronous_mode=world.get_settings().synchronous_mode)
Path('results/cleanup_world.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
