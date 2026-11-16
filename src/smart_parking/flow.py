"""Conservative sequence-local gate crossings, not a calibrated traffic counter.

Box-centre association can fragment identities under occlusion. Ambiguous matches
and long/missing observation gaps reset crossing evidence instead of guessing.
"""
import math
from copy import deepcopy

VEHICLES = {'car', 'bus', 'truck', 'motorcycle'}

def _iou(a, b):
    area = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - area
    return area / union if union else 0.

class GateCounter:
    """Pixel gate; its directed left side is positive. Explicit entry direction."""
    def __init__(self, *, image_size, line, entry_direction='negative_to_positive',
                 confidence=.7, max_distance_fraction=.06, max_gap_seconds=.75,
                 deadband_pixels=6., stable_observations=2, ambiguity_ratio=1.5,
                 time_unit='seconds',max_gap_frames=None):
        if len(image_size)!=2 or any(not isinstance(n,int) or isinstance(n,bool) or n<1 for n in image_size):
            raise ValueError('Gate image size must be positive integer width and height')
        if len(line)!=2 or any(len(p)!=2 for p in line):raise ValueError('A gate needs two endpoints')
        w,h=image_size
        if any(not math.isfinite(v) for p in line for v in p):raise ValueError('Gate coordinates must be finite')
        if any(not (0<=p[0]<w and 0<=p[1]<h) for p in line):raise ValueError('Gate endpoints must lie inside the image')
        self.a,self.b=map(tuple,line);self.dx=self.b[0]-self.a[0];self.dy=self.b[1]-self.a[1]
        self.length=math.hypot(self.dx,self.dy)
        if self.length<1:raise ValueError('Gate endpoints must differ')
        if entry_direction not in {'negative_to_positive','positive_to_negative'}:raise ValueError('Declare gate entry direction')
        if not 0<confidence<1:raise ValueError('Gate confidence must be between zero and one')
        if not math.isfinite(max_distance_fraction) or not 0<max_distance_fraction<=.5:raise ValueError('Invalid association distance')
        if not math.isfinite(max_gap_seconds) or max_gap_seconds<=0:raise ValueError('Invalid observation gap')
        if time_unit not in {'seconds','frames'}:raise ValueError('Unknown tracking time unit')
        if time_unit=='frames':
            if not isinstance(max_gap_frames,int) or isinstance(max_gap_frames,bool) or max_gap_frames<1:raise ValueError('Frame tracking requires a positive integer gap')
        elif max_gap_frames is not None:raise ValueError('Frame gap requires frame-index tracking')
        self.time_unit=time_unit
        if not math.isfinite(deadband_pixels) or deadband_pixels<0:raise ValueError('Invalid gate deadband')
        if not isinstance(stable_observations,int) or stable_observations<2:raise ValueError('At least two stable observations required')
        if not math.isfinite(ambiguity_ratio) or ambiguity_ratio<=1:raise ValueError('Ambiguity ratio must exceed one')
        self.config=deepcopy(dict(image_size=list(image_size),line=line,entry_direction=entry_direction,
            confidence=confidence,max_distance_fraction=max_distance_fraction,max_gap_seconds=max_gap_seconds,
            deadband_pixels=deadband_pixels,stable_observations=stable_observations,ambiguity_ratio=ambiguity_ratio))
        if time_unit=='frames':
            self.config.pop('max_gap_seconds');self.config.update(time_unit='frames',max_gap_frames=max_gap_frames)
        self.max_distance=math.hypot(w,h)*max_distance_fraction
        self.tracks={};self.next_id=1;self.last_time=None;self.entries=0;self.exits=0
        self.gap_resets=0;self.ambiguous_matches=0;self.discarded_duplicates=0

    def _signed(self, p):return (self.dx*(p[1]-self.a[1])-self.dy*(p[0]-self.a[0]))/self.length

    def _crosses_segment(self, a, b):
        da,db=self._signed(a),self._signed(b)
        if da*db>=0:return False
        t=da/(da-db);p=(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
        u=((p[0]-self.a[0])*self.dx+(p[1]-self.a[1])*self.dy)/(self.length**2)
        return 0<=u<=1

    def _detections(self, detections):
        valid=[];w,h=self.config['image_size']
        for index,d in enumerate(detections):
            if d.get('label') not in VEHICLES:continue
            box=d.get('box',[]);score=d.get('score')
            if len(box)!=4 or score is None or not math.isfinite(score) or not all(math.isfinite(v) for v in box):
                raise ValueError('Vehicle detections need finite box coordinates and scores')
            if not 0<=score<=1 or not (0<=box[0]<box[2]<=w and 0<=box[1]<box[3]<=h):
                raise ValueError('Vehicle box outside configured image or invalid score')
            if score>=self.config['confidence']:
                valid.append(dict(detection_index=index,score=score,box=list(box),label=d['label'],
                    center=((box[0]+box[2])/2,(box[1]+box[3])/2)))
        # Class-agnostic suppression prevents one physical box with two vehicle labels
        # from generating two identities; no detector weights/outputs are modified.
        kept=[]
        for d in sorted(valid,key=lambda v:(-v['score'],v['detection_index'])):
            if any(_iou(d['box'],k['box'])>=.6 for k in kept):self.discarded_duplicates+=1
            else:kept.append(d)
        return kept

    def update(self, detections, timestamp, *, image_size=None):
        if self.time_unit=='frames' and (not isinstance(timestamp,int) or isinstance(timestamp,bool)):raise ValueError('Frame-index tracking requires an integer frame index')
        if not math.isfinite(timestamp) or timestamp<0 or (self.last_time is not None and timestamp<=self.last_time):
            raise ValueError('Flow timestamps must strictly increase and be finite/nonnegative')
        if image_size is not None and list(image_size)!=self.config['image_size']:raise ValueError('Gate view dimensions changed')
        current=self._detections(detections)  # Validate before mutating sequence state.
        max_gap=self.config['max_gap_frames'] if self.time_unit=='frames' else self.config['max_gap_seconds']
        if self.last_time is not None and timestamp-self.last_time>max_gap:
            self.gap_resets+=1;self.tracks={}
        self.last_time=timestamp
        distances={(tid,j):math.dist(track['center'],d['center'])
                   for tid,track in self.tracks.items() for j,d in enumerate(current)}
        eligible={key:value for key,value in distances.items() if value<=self.max_distance}
        proposals=[]
        for tid in self.tracks:
            options=sorted((distance,j) for (t,j),distance in eligible.items() if t==tid)
            if not options:continue
            distance,j=options[0]
            rivals=sorted((v,t) for (t,k),v in eligible.items() if k==j)
            ambiguous=(len(options)>1 and options[1][0]<=max(1.,distance)*self.config['ambiguity_ratio']) or (len(rivals)>1 and rivals[1][0]<=max(1.,rivals[0][0])*self.config['ambiguity_ratio'])
            if ambiguous:self.ambiguous_matches+=1;continue
            if rivals[0][1]==tid:proposals.append((tid,j))
        assignments={j:tid for tid,j in proposals};new_tracks={};events=[];visible=[]
        for j,d in enumerate(current):
            tid=assignments.get(j)
            if tid is None:
                tid=self.next_id;self.next_id+=1
                track=dict(stable_side=0,stable_center=None,pending_side=0,pending_count=0)
            else:track=self.tracks[tid]
            signed=self._signed(d['center']);side=1 if signed>self.config['deadband_pixels'] else -1 if signed < -self.config['deadband_pixels'] else 0
            if side==0:track['pending_side']=0;track['pending_count']=0
            else:
                track['pending_count']=track['pending_count']+1 if track['pending_side']==side else 1
                track['pending_side']=side
                if track['pending_count']>=self.config['stable_observations']:
                    previous=track['stable_side']
                    if previous and previous!=side and self._crosses_segment(track['stable_center'],d['center']):
                        direction='negative_to_positive' if previous<side else 'positive_to_negative'
                        kind='entry' if direction==self.config['entry_direction'] else 'exit'
                        self.entries+=kind=='entry';self.exits+=kind=='exit'
                        event=dict(track_id=tid,event_type=kind,direction=direction,
                            center=list(d['center']),evidence='Predicted box-centre crossing; not ground-truth accuracy')
                        event['frame_index' if self.time_unit=='frames' else 'video_time_seconds']=timestamp
                        events.append(event)
                    track['stable_side']=side;track['stable_center']=d['center']
            track['center']=d['center'];new_tracks[tid]=track
            visible.append(dict(track_id=tid,**d,side=side))
        # Missing/ambiguous association drops its crossing memory. New sightings
        # establish a baseline and cannot count an inferred crossing through a gap.
        self.tracks=new_tracks
        return dict(tracks=visible,events=events,counts=dict(entries=self.entries,exits=self.exits),
                    gap_resets=self.gap_resets,ambiguous_matches=self.ambiguous_matches,
                    discarded_duplicates=self.discarded_duplicates)
