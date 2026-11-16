"""Read-only explanation of completed DEVELOPMENT outputs; no model calls."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(card_path):
    card_path=Path(card_path); card=read(card_path); rid=card['run_id']
    run=ROOT/'experiments/results'/rid
    output=ROOT/'reports'/('region_fpn_'+rid)
    output.mkdir(exist_ok=False)
    manifest_path=ROOT/read(run/'protocol.json')['dataset_manifest']
    manifest=read(manifest_path); pattern_groups={}; train_masks=[]; training=[]
    for record in manifest['records']:
        with np.load(ROOT/record['cache'],allow_pickle=False) as saved:mask=saved['mask'].copy()
        key=hashlib.sha256(mask.tobytes()).hexdigest()
        group=record['camera_id']+'|'+record['role']
        pattern_groups.setdefault(group,{})
        pattern_groups[group].setdefault(key,dict(images=0,dates=set()))
        pattern_groups[group][key]['images']+=1
        pattern_groups[group][key]['dates'].add(record['capture_date'])
        if record['role']=='train':train_masks.append(mask);training.append(record)
    # Diagnostic uses TRAIN targets only. This is a reconstruction reference,
    # not a proven architecture upper bound or prediction on unseen images.
    import torch
    from torch.nn import functional as F
    torch.set_num_threads(4)
    sys.path.insert(0,str(ROOT/'src'))
    from smart_parking.region_fpn import mask_metrics
    masks=np.stack(train_masks)
    coarse=F.interpolate(torch.from_numpy(masks[:,None].astype('float32')),size=(36,64),mode='area')
    rebuilt=F.interpolate(coarse,size=(144,256),mode='bilinear',align_corners=False)[:,0].numpy()>=.5
    reconstruction=mask_metrics(rebuilt,masks,[r['camera_id'] for r in training])
    patterns={group:{h:dict(images=v['images'],dates=sorted(v['dates'])) for h,v in values.items()}
              for group,values in pattern_groups.items()}
    diagnostic=dict(created_at=datetime.now(timezone.utc).isoformat(),posthoc=True,
        scope='Target-pattern counts and TRAIN-only area/bilinear mask reconstruction,not model/final evaluation or a mathematical upper bound',
        mask_patterns=patterns,train_reconstruction=reconstruction,new_model_calls=0,extra_experiments_counted=0)
    (run/'posthoc_train_diagnostic.json').write_text(json.dumps(diagnostic,indent=2)+'\n',encoding='utf-8')
    records=read(run/'development_records.json')
    with np.load(run/'development_predictions.npz',allow_pickle=False) as data:
        rgb=data['RGB'];actual=data['actual'];new=data['candidate_probability']>=.5
        original=data['original_probability']>=.5;template=data['conditional_template']
    for name, prediction in [('candidate',new),('original',original),('conditional_train_template',template)]:
        assert mask_metrics(prediction,actual,[r['camera_id'] for r in records])==card[name]
    regular=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',22)
    selected=[]
    for camera in sorted({r['camera_id'] for r in records}):
        candidates=[r for r in card['candidate']['per_image'] if r['camera_id']==camera]
        index=min(candidates,key=lambda r:(r['iou'],r['index']))['index']
        source=records[index]; image=Image.new('RGB',(1280,370),'#f7f8fa');draw=ImageDraw.Draw(image)
        draw.text((16,10),f'{camera.upper()} | worst candidate DEVELOPMENT image for this camera',font=title,fill='#14283f')
        draw.text((16,40),source['capture_date']+' | selected after scoring; not a representative sample or fresh final',font=regular,fill='#34485e')
        labels=['Provided bay footprints','New image model','Original U-Net','TRAIN camera template']
        predictions=[actual[index],new[index],original[index],template[index]]
        scores=[1.,card['candidate']['per_image'][index]['iou'],card['original']['per_image'][index]['iou'],card['conditional_train_template']['per_image'][index]['iou']]
        for column,(label,prediction,score) in enumerate(zip(labels,predictions,scores)):
            colors=np.asarray(rgb[index]).astype('float32')*.65
            truth=actual[index]
            for region,color in [(prediction & truth,[35,205,145]),(prediction & ~truth,[235,70,55]),(~prediction & truth,[70,130,250])]:
                colors[region]=.45*colors[region]+.55*np.array(color)
            tile=Image.fromarray(colors.clip(0,255).astype('uint8')).resize((320,180),Image.Resampling.NEAREST)
            image.paste(tile,(column*320,100))
            draw.text((column*320+10,75),label,font=regular,fill='#14283f')
            draw.text((column*320+10,289),'reference' if column==0 else f'Image IoU {score:.3f}',font=regular,fill='#14283f')
        draw.text((16,320),'Green: agreement   Red: extra predicted area   Blue: missed supplied bay area',font=regular,fill='#34485e')
        draw.text((16,346),'PKLot: Almeida et al. / UFPR, CC BY 4.0. Familiar source views; no occupancy or new-camera claim.',font=regular,fill='#34485e')
        path=output/(camera+'_worst_development.png');image.save(path)
        selected.append(dict(camera_id=camera,index=index,source_record=source,png=path.relative_to(ROOT).as_posix(),sha256=sha(path),candidate_image_iou=card['candidate']['per_image'][index]['iou']))
    c=card['candidate'];o=card['original'];t=card['conditional_train_template']
    text=f'''# Image-only region experiment: development improvement, admission failed

Run {rid}. The original app and checkpoints were preserved. A frozen ImageNet
ResNet18 encoder with a 32-channel feature pyramid and binary decoder trained on
200 admitted images. Epoch {card['selected_epoch']} was selected from eight epochs
using equal-camera mean development IoU. Threshold 0.5 and six acceptance gates
were sealed before training. Seed169; batch8; AdamW0.001; no augmentation;
TRAIN-only weighted BCE plus Dice. Four CPU threads, measured execution phase
{card['duration_seconds_this_invocation']:.3f}s, sampled process RSS peak
{card['peak_sampled_process_RSS_bytes']:,} bytes (not a system-wide peak).

| Method | Equal-camera mean IoU | Equal-camera mean Dice | Worst image IoU |
|---|---:|---:|---:|
| New image-only model | {c['macro_camera_iou']:.6f} | {c['macro_camera_dice']:.6f} | {c['minimum_image_iou']:.6f} |
| Original U-Net, common cache input | {o['macro_camera_iou']:.6f} | {o['macro_camera_dice']:.6f} | {o['minimum_image_iou']:.6f} |
| Conditional TRAIN camera template | {t['macro_camera_iou']:.6f} | {t['macro_camera_dice']:.6f} | {t['minimum_image_iou']:.6f} |

There are 30 development images: PUCPR8, UFPR04 six, UFPR05 sixteen. Each camera
has equal weight in the reported mean; these are IoU values, not occupancy
classification accuracy. The original comparator uses the same256x144 cache,
resizes RGB to its native192x112 input, then interpolates probabilities back to
the common mask grid. This is a paired development comparison, not a replay of
its earlier final benchmark or its exact native-image app input pipeline.

Four gates failed: meanIoU >=0.80, every camera mean >=0.75, every image >=0.65,
and camera-wise regression <=0.05 from the TRAIN template. Gain >=0.02 over the
original and no >0.05 camera regression from the original passed. No gate was
relaxed and there is no app promotion. Complete per-image/per-camera numbers
are in comparisons.json. The template scored1.0 on PUCPR/UFPR05 because those
TRAIN and development target masks are identical within each fixed camera view.
This is repeated geometry, not perfect scene understanding. UFPR04 has three
TRAIN mask patterns represented56/8/8times; all six DEV targets match one of the
eight-example patterns. Its majority template IoU is only0.283890. The new model
UFPR04 mean is0.573749. Camera identity alone does not establish a compatible view.

Post-hoc TRAIN-only mask downsampling to36x64 and bilinear reconstruction gives
mean-camera IoU {reconstruction['macro_camera_iou']:.6f}. This is an annotation
reconstruction reference, not a proven decoder ceiling or additional experiment.
The last training loss was still declining; limited optimization and unequal
TRAIN view-pattern frequency are hypotheses for a later controlled trial, not
proven causes. A future recipe could balance TRAIN camera/view patterns and use
a longer fixed budget, sealing unchanged admission gates before fitting. Reusing
this DEV cohort does not make that future result independent final evidence.

The three PNGs select the worst candidate image per camera after scoring. Colors
show errors against supplied bay footprints; omitted/unannotated parking areas
are not exhaustive facility ground truth. No individual slot IDs, vehicle
occupancy, new-camera reliability or future final accuracy are established.

No protected/quarantined pixels or XML were decoded. The learned Singapore study
and all other final boundaries remain closed. Original/best/failed weights are
preserved. The selected failed candidate, last optimizer/RNG/batch checkpoint,
sealed protocol/source hashes, frozen feature cache and exact predictions remain
local. Four new software tests cover frozen BN, decoder gradients, TRAIN-only
template construction and equal-camera metrics; full suite460/OK.

Sources: SRC-DS-001 PKLot (Almeida et al./UFPR, CC BY4.0), SRC-MOD-003 TorchVision
ImageNet ResNet18 (existing local academic pretrained-weight terms). No new
download or redistribution of pretrained weights.
'''
    (output/'EXPLANATION.md').write_text(text,encoding='utf-8')
    evidence=dict(created_at=datetime.now(timezone.utc).isoformat(),run_id=rid,posthoc=True,
        source_hashes={card_path.relative_to(ROOT).as_posix():sha(card_path),
            (run/'development_predictions.npz').relative_to(ROOT).as_posix():sha(run/'development_predictions.npz'),
            'scripts/render_region_fpn_report.py':sha(Path(__file__))},examples=selected,
        explanation_sha256=sha(output/'EXPLANATION.md'),new_model_calls=0,extra_experiments_counted=0)
    (output/'manifest.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(report=output.relative_to(ROOT).as_posix(),train_reconstruction_macro_camera_iou=reconstruction['macro_camera_iou'],selected_images=3)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--card',default=str(ROOT/'models/region_fpn_v1.json'));args=parser.parse_args();main(Path(args.card).resolve())
