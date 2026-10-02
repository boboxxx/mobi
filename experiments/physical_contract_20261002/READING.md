# Primary-source implementation reading

CARLA0.9.15 [sensor reference](https://carla.readthedocs.io/en/0.9.15/ref_sensors/):
read the LiDAR and semantic LiDAR sections. Semantic LiDAR returns instance and
semantic labels and lacks the ordinary LiDAR intensity/dropout/noise attributes.
Within a measurement the world is static for the simulated ray generation.
These facts motivate strict same-frame labels and the explicit ideal-sensor
limitation; they do not justify a solid obstacle core or a physical noise bound.

CARLA0.9.15 [Python API](https://carla.readthedocs.io/en/0.9.15/python_api/):
read World.cast_ray, frame/settings, and bounding-box definitions. A bounding box
is enclosing geometry, not an occupied solid. cast_ray returns ordered labelled
intersections; this capture uses the existing semantic LiDAR rather than adding
arbitrary ray casts. Actor state is retained only for independent falsification.
No paper novelty claim follows from these simulator APIs.
