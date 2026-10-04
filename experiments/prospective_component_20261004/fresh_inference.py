"""Six initialized services with common known-body/motion source-age contract."""
import bootstrap
import importlib.util
from pathlib import Path
from fractions import Fraction as F
from scores import ROOT
from inference import state as old_state,infer as old_infer,compact,groups
spec=importlib.util.spec_from_file_location('fixed_component_method',ROOT/'experiments/component_expiry_20261004/method.py')
component=importlib.util.module_from_spec(spec);spec.loader.exec_module(component)
PRIMARY=('joint','ridge','local_mean','local_modes','component_mean','component_modes')
def state(hulls,layout,bp,models,family):
 return old_state(hulls,layout,bp,models,family.replace('component_','local_'))
def threshold(registry,bp,family):
 if family.startswith('component_'):
  return dict(supported=F(*registry[bp]['supported_'+family[len('component_'):]]),fallback_um=int(F(*registry[bp]['fallback_um'])))
 return F(*registry[bp][family])
def infer(hulls,extent,hypothesis,q,family,variant='max'):
 if family.startswith('component_'):return component.infer(hulls,extent,hypothesis,q,family)
 return old_infer(hulls,extent,hypothesis,q,family,variant)
