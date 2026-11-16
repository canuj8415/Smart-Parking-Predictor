"""Experimental identity-only continuation; the production GateCounter is unchanged.

Weak boxes may preserve an unambiguous existing identity. They cannot start an
identity or preserve crossing memory. Missing observations still drop identity.
"""
import math
from .flow import GateCounter


class ContinuationGateCounter(GateCounter):
    def __init__(self, *, continuation_confidence=.5, **kwargs):
        super().__init__(**kwargs)
        if not math.isfinite(continuation_confidence) or not 0<continuation_confidence<self.config['confidence']:
            raise ValueError('Continuation confidence must be positive and below birth confidence')
        self.continuation_confidence=continuation_confidence
        self._weak_parser=GateCounter(**dict(self.config,confidence=continuation_confidence))
        self.config['continuation_confidence']=continuation_confidence
        self.weak_continuations=0
        self._accept_weak=False

    @staticmethod
    def _reset_crossing(track):
        track.update(stable_side=0,stable_center=None,pending_side=0,pending_count=0)

    def _detections(self, detections):
        high=super()._detections(detections)  # Validates all inputs before state changes.
        if not self._accept_weak or not self.tracks:
            return high
        weak=[d for d in self._weak_parser._detections(detections) if d['score']<self.config['confidence']]
        # A weak observation cannot compete with any high-confidence association.
        protected={tid for tid,t in self.tracks.items()
                   if any(math.dist(t['center'],d['center'])<=self.max_distance for d in high)}
        weak=[d for d in weak if not any(math.dist(self.tracks[tid]['center'],d['center'])<=self.max_distance for tid in protected)]
        distances={(tid,j):math.dist(t['center'],d['center']) for tid,t in self.tracks.items() for j,d in enumerate(weak)}
        eligible={key:value for key,value in distances.items() if value<=self.max_distance}
        accepted={}
        for tid in self.tracks:
            options=sorted((distance,j) for (t,j),distance in eligible.items() if t==tid)
            if not options:continue
            distance,j=options[0]
            rivals=sorted((v,t) for (t,k),v in eligible.items() if k==j)
            ambiguous=(len(options)>1 and options[1][0]<=max(1.,distance)*self.config['ambiguity_ratio']) or (len(rivals)>1 and rivals[1][0]<=max(1.,rivals[0][0])*self.config['ambiguity_ratio'])
            if not ambiguous and rivals[0][1]==tid:
                accepted[j]=tid
        # Do not manufacture confidence. Keep the actual detector score/box/label.
        # Weak rows only bridge identity; they erase crossing evidence before the
        # inherited counting rule runs, so no low-confidence event is emitted.
        for tid in accepted.values():self._reset_crossing(self.tracks[tid])
        return high+[weak[j] for j in sorted(accepted)]

    def update(self, detections, timestamp, *, image_size=None):
        gap=self.config['max_gap_frames'] if self.time_unit=='frames' else self.config['max_gap_seconds']
        self._accept_weak=self.last_time is not None and isinstance(timestamp,(int,float)) and math.isfinite(timestamp) and 0<timestamp-self.last_time<=gap
        previous_ids=set(self.tracks)
        result=super().update(detections,timestamp,image_size=image_size)
        continued=0
        for track in result['tracks']:
            weak=track['score']<self.config['confidence']
            track['continuation_only']=weak
            if weak:
                if track['track_id'] not in previous_ids:
                    raise RuntimeError('Weak continuation must never create an identity')
                self._reset_crossing(self.tracks[track['track_id']])
                continued+=1
        self.weak_continuations+=continued
        result['weak_continuations']=self.weak_continuations
        result['weak_observations_this_frame']=continued
        return result
