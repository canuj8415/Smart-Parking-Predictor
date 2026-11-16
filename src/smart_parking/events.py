"""Sequence-local occupancy transitions, explicitly distinct from entry/exit flow."""
class OccupancyEvents:
    def __init__(self,stable_frames=2):
        if stable_frames<1:raise ValueError('Stable frame count must be positive')
        self.required=stable_frames;self.reset()
    def reset(self):self.current={};self.pending={}
    def update(self,observations,timestamp):
        events=[]
        for observation in observations:
            slot=observation['slot_id'];state=observation['state']
            if state=='uncertain':self.pending.pop(slot,None);continue
            previous,count=self.pending.get(slot,(None,0))
            count=count+1 if previous==state else 1;self.pending[slot]=(state,count)
            if count<self.required:continue
            old=self.current.get(slot)
            if old is not None and old!=state:
                events.append(dict(slot_id=slot,previous_state=old,state=state,video_time_seconds=timestamp,
                    event_type='occupancy_change; not entrance/exit crossing'))
            self.current[slot]=state
        return events
