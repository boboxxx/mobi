"""Finer internal tiles, unchanged trusted physical/source wire contract."""
import json
from dataclasses import replace
import numpy as np
import observer
body=observer.body;base=observer.base


class Receiver(observer.Receiver):
    def __init__(self,profiles,contract,factor=2):
        if type(factor) is not int or factor!=2:raise ValueError('Frozen factor2 only')
        super().__init__(profiles,contract);self.factor=factor
        self.grid_profiles={n:replace(p,step=p.step/factor) for n,p in profiles.items()}

    def register(self,legacy,blob,scope,motion):
        anchor=super().register(legacy,blob,scope,motion);coarse=self._states[anchor.identity]
        raw=json.loads(blob)['raw'];p,o,r=body.decode(body.canonical(raw),self.profiles,scope,self.contract)
        v=body.projections(o,r,p['reference_us'],self.profiles,scope,self.contract)
        possible={};effective={}
        for n,grid in self.grid_profiles.items():
            possible[n]=np.repeat(np.repeat(coarse.possible[n],self.factor,axis=0),self.factor,axis=1)&~observer.exclusion(v[n],grid,motion)
            effective[n]=base.reference_speed(grid,r,p['reference_us'])
        self._states[anchor.identity]=observer.State(coarse.reference_us,coarse.sequence,possible,effective)
        return anchor

    def rebuild(self,transport):
        b=json.loads(observer.stream.decode(transport))
        if set(b)!={'kind','dynamics','anchor','steps'} or b['kind']!='position-observations-v1' or b['dynamics']!='observation-speed-age-v1':raise ValueError('Wrong observation bundle')
        anchor=self._anchors[b['anchor']]
        if not isinstance(b['steps'],list) or not 1<=len(b['steps'])<=base.MAX_STEPS:raise ValueError('Step bound')
        state=self._states[anchor.identity]
        for raw in b['steps']:
            # Physical metadata remains the original registered contract;
            # internal grid size is a local observer representation choice.
            p,o,r=body.decode(body.canonical(raw),self.profiles,anchor.scope,self.contract)
            ref=p['reference_us']
            if ref<=state.reference_us or p['sequence']<=state.sequence:raise ValueError('Observation order/replay')
            v=body.projections(o,r,ref,self.profiles,anchor.scope,self.contract);dt=(ref-state.reference_us)/1e6
            possible={};effective={}
            for n,grid in self.grid_profiles.items():
                prediction=observer.propagate(state.possible[n],grid.step,body.travel(dt,state.effective_profiles[n]))
                possible[n]=prediction&~observer.exclusion(v[n],grid,anchor.motion)
                effective[n]=base.reference_speed(grid,r,ref)
            state=observer.State(ref,p['sequence'],possible,effective)
        classes={n:observer.frontier(state.possible[n],state.effective_profiles[n],anchor.motion) for n in self.profiles}
        h=min(x['horizon_us'] for x in classes.values())
        return dict(reference_us=state.reference_us,endpoint_us=state.reference_us+h,sequence=state.sequence,horizon_us=h,
                    classes=classes,steps=len(b['steps']),anchor=anchor.identity,grid_factor=self.factor),state
