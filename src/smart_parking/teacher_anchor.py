"""Training-only teacher retention penalty;no validation/final labels as targets."""
import math
import torch
from torch.nn import functional as F


def teacher_anchor_loss(student_logits,teacher_logits,temperature=2.):
    if not math.isfinite(temperature) or temperature<=0:raise ValueError('Positive finite temperature required')
    if student_logits.ndim!=2 or student_logits.shape[0]==0 or student_logits.shape[1]!=2 or student_logits.shape!=teacher_logits.shape:raise ValueError('Matching nonempty binary logits required')
    if not torch.isfinite(student_logits).all() or not torch.isfinite(teacher_logits).all():raise ValueError('Finite logits required')
    teacher=F.softmax(teacher_logits.detach()/temperature,dim=1)
    return F.kl_div(F.log_softmax(student_logits/temperature,dim=1),teacher,reduction='batchmean')*temperature**2
