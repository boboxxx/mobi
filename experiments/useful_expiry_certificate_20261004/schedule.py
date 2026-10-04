"""Bound completion before command without adding a gratuitous controller tick."""
DT=50000;BUDGET=20000

def ready_at(now,fee,cumulative,timing):
 assert fee>=0 and cumulative>=fee and timing in ('deferred','immediate')
 return now+(cumulative if timing=='immediate' else ((max(1,fee)+DT-1)//DT)*DT)
def usable_by(now,cumulative,timing):
 assert cumulative>=0 and timing in ('deferred','immediate')
 return now+(min(cumulative,BUDGET) if timing=='immediate' else 0)
def command_clock(now,receiver_fee,query_fee):
 assert receiver_fee>=0 and query_fee>=0
 return now+receiver_fee+query_fee,receiver_fee+query_fee<=BUDGET
