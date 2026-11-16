"""Typeset current saved evidence into a PDF and an editable LaTeX counterpart.

No models are rerun and no raw final observations are opened. The standalone PDF
uses ReportLab; main.tex contains the same content for the desktop/Overleaf compiler.
"""
import csv,hashlib,io,json,shutil
from pathlib import Path
from datetime import datetime,timezone
from xml.sax.saxutils import escape
import subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'reports/technical_report_v003'
OUT=ROOT/'output/pdf/smart_parking_technical_report_v003.pdf'
E=ROOT/'experiments/evidence/HEARTBEAT-20261025T161532Z'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def generate_figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from PIL import Image as PILImage
    figures=PROJECT/'figures'
    forecast=json.loads((PROJECT/'inputs/models/forecast_final_evaluation.json').read_text(encoding='utf-8'))
    dev=json.loads((PROJECT/'inputs/models/flow_continuation_development.json').read_text(encoding='utf-8'))
    fm=forecast['final_evaluation']['metrics']
    plt.rcParams.update({'font.size':10,'axes.titlesize':11,'axes.labelsize':10,'font.family':'DejaVu Sans'})
    fig,ax=plt.subplots(figsize=(6.5,2.8),layout='constrained')
    values=[fm['original_lstm_mae_spaces'],fm['persistence_mae_spaces'],fm['candidate_mae_spaces']]
    bars=ax.bar(['Original LSTM','Last reading','Frozen candidate'],values,color=['#8d99a6','#bb8751','#367aa0'])
    ax.bar_label(bars,labels=[f'{v:.2f}' for v in values],padding=3)
    ax.set(ylabel='MAE in parking spaces',title='Same 1,853 later-date target windows',ylim=(0,max(values)*1.2))
    ax.spines[['top','right']].set_visible(False);fig.savefig(figures/'forecast_comparison.png',dpi=180);plt.close(fig)
    path=PROJECT/'inputs/experiments/results'/dev['run_id']/'observations.csv'
    with path.open(encoding='utf-8',newline='') as f:rows=[r for r in csv.DictReader(f) if int(r['frame_index'])>=5]
    fig,ax=plt.subplots(figsize=(6.5,2.5),layout='constrained')
    xs=[int(r['frame_index']) for r in rows]
    ax.step(xs,[float(r['baseline_track_id']) if r['baseline_track_id'] else float('nan') for r in rows],where='post',linestyle='--',color='#ae6b22',label='Original tracker')
    ax.step(xs,[float(r['candidate_track_id']) if r['candidate_track_id'] else float('nan') for r in rows],where='post',color='#2364a5',label='Identity continuation')
    ax.axvline(26,color='#777777',linestyle=':',label='Confidence dip')
    ax.set(xlabel='Development frame index (fps unknown)',ylabel='Identity ID',yticks=[1,3],ylim=(.7,3.3),title='One selected car, reused development sequence')
    ax.legend(fontsize=8,loc='center right');fig.savefig(figures/'identity_comparison.png',dpi=180);plt.close(fig)
    cache_relative='experiments/results/DAVIS-FOREGROUND-20261025T113304928428Z/frame_records.json'
    records=json.loads((PROJECT/'inputs'/cache_relative).read_text(encoding='utf-8'));row=records[22];image_path=ROOT/'data/raw/davis2017_subset/DAVIS/JPEGImages/480p/car-turn/00022.jpg'
    # Development pixels only. Do not open the consumed car-roundabout final.
    with PILImage.open(image_path) as im:photo=im.convert('RGB').copy()
    fig,ax=plt.subplots(figsize=(6.5,3.5),layout='constrained');ax.imshow(photo)
    box=row['reference_objects'][0]['box'];ax.add_patch(Rectangle((box[0],box[1]),box[2]-box[0],box[3]-box[1],fill=False,edgecolor='#16824d',linewidth=2,label='Publisher foreground box'))
    ax.axvline(694,color='#2364a5',linewidth=2,label='Setup-only image line');ax.axis('off');ax.legend(loc='lower left',fontsize=8)
    ax.set_title('Development illustration, frame 22');fig.savefig(figures/'development_example.png',dpi=180);plt.close(fig)


def main():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether

    now=datetime.now(timezone.utc);as_of=now.strftime('%d October %Y, %H:%M UTC')
    figures=PROJECT/'figures';figures.mkdir(parents=True,exist_ok=True)
    inputs=[]
    def saved(relative):
        path=ROOT/relative;target=PROJECT/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        inputs.append(dict(origin=relative,snapshot=target.relative_to(PROJECT).as_posix(),sha256=sha(target)))
        return json.loads(target.read_text(encoding='utf-8'))
    state=saved('data/automation_state.json');vision=saved('models/vision_model_card.json');seg=saved('models/segmentation_model_card.json')
    forecast=saved('models/forecast_final_evaluation.json');original_forecast=saved('models/lstm_30min_model_card.json')
    region=saved('models/region_stability_final.json');dev=saved('models/flow_continuation_development.json');final=saved('models/davis_sequence_final.json')
    package=saved('models/local_demo_package.json');live=saved('data/processed/singapore_prospective/summary.json')
    for relative,name in [('data/source_manifest.csv','source_manifest_snapshot.csv'),('data/resource_receipts.jsonl','resource_receipts_snapshot.jsonl')]:
        shutil.copy2(ROOT/relative,PROJECT/name);inputs.append(dict(origin=relative,snapshot=name,sha256=sha(PROJECT/name)))
    with (PROJECT/'source_manifest_snapshot.csv').open(encoding='utf-8-sig',newline='') as f:sources=list(csv.DictReader(f))
    assert len(sources)==45 and state['completed_recorded_runs_since_schedule']==34
    fm=forecast['final_evaluation']['metrics'];dm=dev['metrics'];tm=final['metrics'];vm=vision['classifier_metrics']
    report_metrics=dict(occupancy_correct=vm['confusion_matrix'][0][0]+vm['confusion_matrix'][1][1],occupancy_total=vm['samples'],
        occupancy_accuracy=vm['accuracy'],original_region_iou=seg['metrics']['pixel_iou'],conditional_iou=region['final_evaluation']['hybrid']['overall']['pixel_iou'],
        forecast_metrics=fm,development_tracking=dm,final_tracking=tm,live=live,completed_trials=34,software_tests=167)
    cache_relative='experiments/results/DAVIS-FOREGROUND-20261025T113304928428Z/frame_records.json'
    saved(cache_relative)
    relative='experiments/results/'+dev['run_id']+'/observations.csv'
    target=PROJECT/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,target)
    inputs.append(dict(origin=relative,snapshot=target.relative_to(PROJECT).as_posix(),sha256=sha(target)))
    subprocess.run(['D:/deep learning/.venv/Scripts/python.exe',str(Path(__file__).resolve()),'--figures'],check=True)
    image_path=ROOT/'data/raw/davis2017_subset/DAVIS/JPEGImages/480p/car-turn/00022.jpg'
    inputs.append(dict(origin=image_path.relative_to(ROOT).as_posix(),snapshot=None,note='Development original retained in main project; only derived figure included',sha256=sha(image_path)))
    cov=live['forecast_coverage'];pending=cov['pending_before_window']+cov['pending_in_window']+cov['awaiting_late_delivery']
    pages=[]
    def page(title,*blocks):pages.append(dict(title=title,blocks=list(blocks)))
    def p(text):return dict(kind='paragraph',text=text)
    def t(headers,rows,widths):return dict(kind='table',headers=headers,rows=rows,widths=widths)
    def fig(name,caption,height):return dict(kind='figure',name=name,caption=caption,height=height)
    page('Smart Parking with Deep Learning',
        p('Implementation, measured results and remaining validation. Technical report draft v003. Evidence snapshot: '+as_of+'. Python/Jupyter development project; AI-assisted development and document preparation. Student identity, independent contribution and mastery have not been verified.'),
        p('Abstract. The product detects vehicles with pretrained Faster R-CNN/ResNet50 and Mask R-CNN, combines configured parking-space geometry with a trained ResNet18 crop classifier, predicts experimental parking regions, displays historical availability forecasts and integrates an official public Singapore feed. It also demonstrates representative 2D/3D convolution arithmetic. Real observations, pretrained weights, project-trained models and synthetic teaching/software fixtures are kept distinct.'),
        p('The original occupancy classifier correctly classified 343 of 360 held-out crops. A later-date forecasting candidate reduced MAE from 39.07 to 31.72 spaces on identical historical targets. A conditional region method reached IoU 0.910 on six known-camera images, with two views using stored geometry. A tracking candidate fixed an observed development identity break, but its final sequence had no labelled crossings of the frozen line. That final counting gate did not pass. These results support a working prototype, not universal accuracy or deployment readiness.'),
        t(['Evidence area','Current position'],[
            ['Implemented product','Python desktop, seven executed notebooks, local image/video processing and dated progress exports'],
            ['Software verification','167 passing tests; 34 recorded trials include explicit software integration studies'],
            ['Local demo','184 verified files, 544,600,770 bytes; installed Python runtime reused'],
            ['Unfinished acceptance','Fresh meaningful crossing evidence, native/manual and physical-offline checks, final submission requirements'],
        ],[.25,.75]),
        p('Two university source documents and the official rubric/template remain unavailable. This draft does not invent an institution, supervisor, deadline, student authorship or official compliance. The scientific claims below remain limited to their recorded populations and protocols.'))
    page('1. Product question and system design',
        p('A driver needs to know whether a particular space is usable now and how aggregate availability may change later. These are different questions. A camera detector finding a vehicle does not by itself identify a numbered parking space or establish that another space is vacant.'),
        t(['Path','Input and processing','Output and boundary'],[
            ['Camera','Image/video; pretrained detections; matching configured polygons; crop probabilities and geometric support','Occupied, vacant or uncertain slot states. A layout must match the camera view.'],
            ['Historical','Recorded Birmingham counts; causal chronological windows; frozen model and persistence comparator','Predicted counts on matching historical targets. No transfer claim to the camera or Singapore.'],
            ['Live','Official Singapore JSON; bounds, timestamps, duplicates and source/capacity checks','Actual provider availability; separately frozen persistence forecasts scored only after later observations arrive.'],
            ['Teaching','Real-image 2D response and an explicitly synthetic 3D numeric volume','Representative convolution arithmetic, not a trained 3D temporal vehicle model.'],
        ],[.17,.43,.40]),
        p('The Python desktop separates image/video, entrance/exit setup, availability forecasting, live parking, convolution lessons and sources/progress. Analysis exports retain the processed-pixel identity, geometry and model versions. An experimental semantic preview is stored separately so its picture is not mistaken for the occupancy result.'),
        p('Faster R-CNN uses region proposals and classification/regression heads [1]; the selected implementation has a ResNet50 backbone [3]. Mask R-CNN adds actual instance masks [2]. These weights are pretrained and loaded locally. The project does not claim to have trained either detector or to have benchmarked YOLO. Faster R-CNN is the implemented branch of the requested YOLO/Faster R-CNN choice.'),
        p('No live feed is converted into invented camera labels. Occupancy changes are not treated as proof of a car crossing a parking entrance. Camera motion, occlusion, uncertain crop decisions and missing observations remain material limitations.'))
    page('2. Real data, original storage and attribution',
        t(['Source','Acquired evidence and use','Original location / source'],[
            ['PKLot [4]','Original archive retained; 1,701 working image/XML pairs. Original classifier uses a smaller 60-frame/20-date study. Layouts preserve geometry and IDs.','data/raw/pklot_subset/; data/manifests/; configs/layouts/'],
            ['Birmingham [5]','35,717 original rows; 35,116 accepted and 601 quarantined. Historical forecasting only.','data/raw/uci_parking_birmingham/; data/splits/birmingham-global-days-v1/'],
            ['DAVIS2017 [6]','155 original image/mask pairs from two sequences: 80 development and 75 final. Partial foreground labels, not every traffic participant.','data/raw/davis2017_subset/; data/manifests/davis_car_sequences_v2.json'],
            ['Singapore [7]','Official timestamped availability snapshots and normalized observations; delayed persistence scoring.','data/raw/singapore_live/; data/processed/singapore_live_observations.csv'],
            ['Street traffic [8]','Original licensed moving street clip; bounded decoder/export integration checks. No supplied occupancy/crossing truth.','data/raw/wikimedia_street_traffic/Street_traffic.webm'],
        ],[.18,.43,.39]),
        p('The full 45-entry source register is copied beside this report as source_manifest_snapshot.csv. It includes original creators, URLs, licences, local paths, purpose and unresolved issues. Some entries are research candidates or inspection-only sources; they are not all acquired datasets. Every acquisition receipt is preserved in resource_receipts_snapshot.jsonl, with actual URL, time, bytes and checksum.'),
        p('Originals, failed experiments and weights are retained. Prepared observations are distinct from originals and synthetic fixtures. Invalid dates/polygons are excluded or quarantined without inventing corrected source values. The DAVIS source-ID collision was repaired explicitly: canonical SRC-DS-012, original records and append-only correction links preserved. TRANCOS remains a separate unacquired candidate.'),
        p('Licence statements are recorded source evidence, not an assertion that every possible future redistribution is cleared. PKLot attribution is retained; DAVIS aggregate CC BY-NC 4.0 governs local academic use here; the street clip is CC BY 3.0; Singapore use was explicitly authorized under its public licence. Source and rights distinctions remain visible in the register.'))
    page('3. Methods, training and controlled evaluation',
        t(['Component','Actual implementation / fitting','Evaluation boundary'],[
            ['Vehicle models','Frozen TorchVision Faster R-CNN/ResNet50FPNv2 and Mask R-CNN/ResNet50FPN [1-3,11]. No project detector fine-tuning.','Selected-object frame coverage is available; exhaustive traffic mAP and instance-mask accuracy are not established.'],
            ['Occupancy','Project-trained ResNet18 transfer head: Adam, learning rate0.003, 30 head epochs, seed42. 2,605 training/360 validation/360 test crops.','Date-separated original study, not a full PKLot benchmark. Some wider labels are unknown; uncertainty is retained.'],
            ['Region masks','Original small U-Net-family model [9], 50 epochs, seed43. Later frozen image-only and conditional known-camera candidates are separate.','Configured geometry is not automatic slot discovery. Stable-camera routing uses priors in two views.'],
            ['Forecast','Capacity-normalized causal LSTM, six input steps; original18epochs/seed42. Qualified group-relative candidate selected using training-only folds.','Chronological/source-consistent targets; compare candidates with persistence on identical rows.'],
            ['Flow candidate','High-confidence births0.7; weak continuation0.5 only for unambiguous existing identities. Weak boxes erase crossing memory.','No weak births or inferred crossings through missing frames. Real time/fps is not fabricated.'],
        ],[.19,.44,.37]),
        p('Frozen protocols, seeds, split/config/code hashes, durations, exact source snapshots and actual outcomes accompany experiments. An epoch, frame or loop iteration is not a recorded run. Software fixtures and the 500 randomized weak-observation cases test rules; they do not measure real-world accuracy.'),
        p('Final data are one-use resources. Durable claims are written before final decoding, and a failed/interrupted evaluation still consumes its source group. Image camera/date groups, Birmingham later dates and the entire DAVIS car-roundabout sequence are now consumed. Changed methods require genuinely fresh final groups. This report reads archived results, not raw final observations.'),
        p('Source metadata and architecture citations explain implementation context. Bibliographic inclusion does not imply complete methodological review of every paper. The reports and code distinguish original pretrained weights, project fitting, cached inference replays and software integration.'))
    page('4. Occupancy, region and forecasting results',
        t(['Measurement','Recorded result','Population / interpretation'],[
            ['Original occupancy classifier',f"343/360 correct ({vm['accuracy']*100:.2f}%)",'Original held-out slot crops,60frames over20valid dates in the full small study. Not whole-project accuracy.'],
            ['Original region preview',f"IoU {seg['metrics']['pixel_iou']:.3f}",'10test frames in the original region study; weak experimental model remains in the default preview.'],
            ['Conditional region router',f"IoU {report_metrics['conditional_iou']:.3f}",'Six known-camera final images; two views geometry-only, one CNN. No automatic slot IDs or unseen-camera claim.'],
            ['Later-date candidate / persistence',f"{fm['candidate_mae_spaces']:.2f} / {fm['persistence_mae_spaces']:.2f} spaces MAE",'Identical1,853windows over8later dates and29eligible parks. Lower error is better.'],
        ],[.28,.28,.44]),
        fig('forecast_comparison.png','Figure 1. Saved results on identical later-date Birmingham targets [5]. The original LSTM is replayed as a frozen comparator; this is not a comparison between unrelated test populations.',170),
        p(f"The later-date candidate reduces MAE by {fm['improvement_vs_persistence']*100:.2f}% relative to persistence. The actual matched target readings arrive10.02-29.12minutes after the origin; a half-hour grid label is not exact30-minute sensor accuracy. Windows are correlated and source-specific."),
        p(f"In its original, different204-window test, the original LSTM MAE was {original_forecast['metrics']['mae_slots']:.2f} versus {original_forecast['metrics']['persistence_mae_slots']:.2f} for persistence. Do not compare that population directly with the new1,853-window result. Archived view selection keeps the two reports distinct; original runtime weights were not silently replaced."))
    page('5. Vehicle identity, crossing evidence and final limit',
        p('DAVIS car-turn provides publisher foreground masks for one selected car. Frames0-4 set a vertical line using a fixed initial-motion/half-box-width rule; frames5-79 are scored. Detection/track matching uses box IoU at least0.5. Reference events use publisher identity and finite-line geometry; predicted/reference event matching allows two frames.'),
        t(['Saved check','Original tracker','Continuation candidate'],[
            ['Development matched frames','74/75','75/75'],['Development dominant identity','53/75','75/75'],
            ['Development recovered crossings','1/1','1/1'],['Final matched/dominant identity','70/70','70/70'],
            ['Final labelled crossings','0','0'],['Final crossing recovery','Not evaluable','Not evaluable'],
        ],[.46,.27,.27]),
        fig('identity_comparison.png','Figure 2. One repeatedly observed development car [6]. ID numbers are arbitrary labels. The candidate bridges one confidence dip; this is reused development evidence, not75independent vehicles.',155),
        p('At development frame26the detector still produced a box close to the selected object, but scores around0.637 fell below the original tracker cutoff. The new policy keeps an unambiguous existing identity without inflating scores or using weak observations to infer crossings. Original default tracking remains separate.'),
        p('The guarded car-roundabout final used five setup and70scored frames. Both trackers retained the selected car, but it never crossed the frozen line. The recovery score is unavailable and the overall final gate did not pass. One unmatched predicted event cannot be graded using partial labels. The entire sequence remains consumed; the line is not moved and changed methods are not rerun on it. Camera motion and unknown fps prevent parking-entrance, physical-speed or real-time claims.'))
    page('6. What the recorded crossing picture means',
        fig('development_example.png','Figure 3. Real DAVIS car-turn development image, frame22. Green is the publisher-selected foreground box; blue is the setup-only image line. Derived annotation overlay. DAVIS authors, Pont-Tuset et al.(2017), Perazzi et al.(2016), davischallenge.org, CC BY-NC4.0 [6].',270),
        p('A guard can correctly notice a car crossing a painted line yet lose its identity on a later unclear image. Fixing that identity break and counting an entrance are different requirements. A camera following the car can also make its image coordinates move differently from its physical route.'),
        p('The picture illustrates one recorded development event. It does not establish that a car entered a particular parking facility, nor does it label every background vehicle. The separately held final was judged by its previously frozen rule and produced zero reference crossings. Zero events is not perfect counting; it is missing positive evidence for that metric.'),
        p('Fresh legitimate fixed-camera footage with independent positive-crossing labels is needed for stronger final flow validation. Any new annotation process must disclose who created the labels, what vehicles/events are included, timing uncertainty and how the final groups were protected.'))
    page('7. Live source quality and prospective availability checks',
        p('The Singapore feed supplies aggregate car-park availability, not camera ground truth [7]. Raw responses remain immutable JSON; accepted observations are normalized into CSV with source IDs, car-park/type keys, capacities and timestamps. Nonpositive capacities and out-of-bounds counts are excluded, and duplicates/freshness are checked.'),
        t(['Snapshot measurement','Actual value'],[
            ['Collection/check time (UTC)',live['checked_at']],['Matched later persistence outcomes',f"{live['scores_total']:,}"],
            ['Matched-only persistence MAE',f"{live['baseline_mae_spaces']:.6f} spaces"],['Expired missing targets',f"{cov['expired_missing_target']:,}"],
            ['Pending outcomes',f'{pending:,}'],['Matched / resolved target coverage',f"{cov['matched_fraction_of_resolved_forecasts']*100:.2f}%"],
        ],[.58,.42]),
        p('A persistence forecast is frozen at issue time, then scored only against a genuinely later, fresh, same-source/same-capacity observation in the prescribed20-45minute window. Missing targets are not assigned invented zero error. Pending outcomes are excluded from the resolved coverage denominator. Observed collection gaps remain documented.'),
        p('Target-matching coverage measures data availability, not forecasting accuracy. The MAE above applies only to matched outcomes. The Birmingham neural predictor is not presented as validated for Singapore; source-consistent history and chronological future evaluation would be needed for such a claim.'),
        p('The app shows provider time and age and labels stale/cached observations. A saved snapshot remains available locally, but is never described as current merely because its file exists. The minimum one-minute polling interval is respected; actual collection is at a sensible planned cadence.'),
        p('Exact latest source files, receipt hashes and normalized-history locations are pinned in report_inputs.json and the copied source/receipt register. The feed licence and user authorization remain attached to the project record.'))
    page('8. Application, exports and relocated local demo',
        p('The Python desktop supports configured image/video processing, explicit entrance/exit setup, saved historical comparisons, cached/live provider readings, convolution lessons and source/progress views. Export metadata binds the actual analysis overlay and JSON; a separate display preview cannot silently replace the measured analysis image.'),
        t(['Check','Actual evidence'],[
            ['Software suite','167passing tests, including geometry, uncertainty, causal windows, holdout guards, CSV/export identity, weak-observation rules and shutdown cleanup.'],
            ['Local relocated folder','184hash-verified files,544,600,770bytes. Original data/weights copied, not moved. Existing Python runtime reused.'],
            ['Runtime path isolation','Product modules/assets load from the copied folder. Python reads back into the original workspace are denied.'],
            ['Network / display scope','Zero normal Python network attempts; explicit block probe passed. Widgets hidden and save dialogs mocked; OS networking unchanged.'],
            ['Actual workflows','Both detector routes and exports on training image; semantic preview; two archived forecasts; stale live display; convolution/progress; two local video samples.'],
        ],[.27,.73]),
        p('The default demo image is explicitly from the prepared training split, with100geometry-only spaces and stored image/layout hashes. It is not a new independent accuracy test. The first package revealed a nonfatal pending Tk callback on close. It is preserved; the corrected version cancels the callback and has empty validation stderr.'),
        p('This establishes a relocated local software path with the installed environment. It is not a fresh offline installation, physical disconnection, new-machine test, cross-platform validation or visible/manual-dialog acceptance. Full training datasets and the Python runtime are not redistributed in this selected local bundle.'),
        p('The dated Excel/progress snapshot remains clearly labelled. Editing its cells does not train a model or alter source data. Reproducibility uses exact run/config/code/data/checkpoint hashes, not a promise that every future machine is already supported.'))
    page('9. Convolution lessons, remaining work and student explanation',
        p('A 2D kernel visits spatial neighborhoods in a real grayscale image. The implementation compares the convolution response with explicit arithmetic. A 3D kernel additionally spans a depth/time axis and two spatial axes. The 3D lesson uses a labelled numeric teaching volume, not fabricated parking footage or a trained temporal detector.'),
        p('The separate NumPy MLP uses synthetic XOR to teach gradients and optimization; the real-crop VAE teaches reconstruction and latent sampling [12]. Neither is counted as evidence that synthetic images improve parking detection. Seven executed notebooks retain actual outputs and explicit limits.'),
        t(['Remaining acceptance area','Next evidence needed'],[
            ['Vision reliability','Fresh source groups, broader parking conditions, stronger image-only regions/slot representation and selective vacancy reliability.'],
            ['Vehicle flow','Meaningful independent positive-crossing labels on fresh fixed-camera footage; no reuse of consumed sequences.'],
            ['Availability','Maintain source-consistent history, strong persistence comparison and strictly later targets. No camera/live neural transfer claim.'],
            ['Product delivery','Fresh offline installation, physical disconnection, visible/native dialogs, new-machine/performance coverage and report/presentation rehearsal.'],
            ['Academic submission','Actual university documents, rubric/template, student metadata and independent learning/contribution evidence.'],
        ],[.28,.72]),
        p('Student practice: explain why343/360cropped decisions do not mean a whole car park is95.28%reliable; why a configured polygon is different from automatic slot discovery; why a smaller forecasting MAE is useful only against the same targets; why zero final crossings gives an unavailable recovery score; and why a passed software check does not complete scientific validation.'),
        p('Conclusion. The project is an implemented, traceable Python/Jupyter prototype with real data and measurable strengths. It also has substantive unresolved limits. Universal100%accuracy, deployment readiness, official academic compliance and student mastery are not claimed. Final completion requires the explicit remaining gates and an honest account of any residual limitations.'))
    references=[
        ('1','Ren et al. (2015). Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks.','https://arxiv.org/abs/1506.01497'),
        ('2','He et al. (2017). Mask R-CNN.','https://arxiv.org/abs/1703.06870'),
        ('3','He et al. (2015 preprint). Deep Residual Learning for Image Recognition.','https://arxiv.org/abs/1512.03385'),
        ('4','Almeida et al. (2015). PKLot - A robust dataset for parking lot classification. Dataset and original author context.','https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/'),
        ('5','Stolfi, D. (2017). Parking Birmingham. UCI repository, DOI10.24432/C51K5Z; original council provenance retained.','https://archive.ics.uci.edu/dataset/482/parking+birmingham'),
        ('6','DAVIS authors; Pont-Tuset et al. (2017), Perazzi et al. (2016). Original image/foreground annotations; aggregate CC BY-NC4.0.','https://davischallenge.org/davis2017/code.html'),
        ('7','Singapore official car-park availability API. Singapore Open Data Licence1.0; local use authorized in project record.','https://api.data.gov.sg/v1/transport/carpark-availability'),
        ('8','Editor. Street traffic (recorded28May2011), via Wikimedia Commons, CC BY3.0; original footage unchanged, derived overlays disclosed.','https://commons.wikimedia.org/wiki/File:Street_traffic.webm'),
        ('9','Ronneberger et al. (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation. Architecture context.','https://arxiv.org/abs/1505.04597'),
        ('10','Hochreiter and Schmidhuber (1997). Long Short-Term Memory. Neural Computation9(8),1735-1780.','https://doi.org/10.1162/neco.1997.9.8.1735'),
        ('11','TorchVision maintainers/contributors. Implementations and pretrained-weight documentation; observed project runtime pinned separately.','https://github.com/pytorch/vision'),
        ('12','Kingma and Welling (2013). Auto-Encoding Variational Bayes. Separate teaching-lab context.','https://arxiv.org/abs/1312.6114'),
    ]
    page('10. References and assistance disclosure',*[dict(kind='reference',number=n,text=text,url=url) for n,text,url in references],
        p('The complete source register includes additional inspected candidates, libraries and tools. This reference list focuses on implemented methods and acquired evidence. Metadata verification and citations do not imply a full paper review. Authoring/debugging/research/document help is AI-assisted and logged separately from student contributions. Figures use Matplotlib; this standalone PDF uses ReportLab. The editable LaTeX counterpart is generated from the same structured content; their layouts may differ.'))
    index=[
        ['Classifier / original mask','models/vision_model_card.json; models/segmentation_model_card.json'],
        ['Forecast final','models/forecast_final_evaluation.json'],['Conditional region final','models/region_stability_final.json'],
        ['Flow development / final','models/flow_continuation_development.json; models/davis_sequence_final.json'],
        ['One-use protection','data/holdout_claims/; data/forecast_holdout_claims/; data/sequence_holdout_claims/'],
        ['Latest demo','reports/demo_package_latest.json; models/local_demo_package.json'],
        ['CSV/JSON outcomes','experiments/results/; individual run.json, protocol.json, observations.csv and source snapshots'],
        ['Original / prepared data','data/raw/; data/processed/; data/manifests/; data/splits/'],
        ['Every source / receipt','source_manifest_snapshot.csv; resource_receipts_snapshot.jsonl beside this report'],
        ['Report reproducibility','report_content.json; report_inputs.json; main.tex; figures/'],
    ]
    page('Appendix. Exact evidence, preservation and reproducibility',
        p('All paths below are relative to the main project folder: D:/deep learning/project001. The copied local demo is selected runtime material, not the full training dataset. Figures1-3are newly typeset illustrations of saved metrics/development evidence; no model or raw final evaluation is rerun.'),
        t(['Evidence','Location'],index,[.28,.72]),
        p('report_inputs.json records each copied input and SHA-256. The original checkpoint hashes below remain distinct from experimental candidates. Large datasets and weights are retained locally outside ordinary Git history.'),
        t(['Original checkpoint','SHA-256'],[
            ['Occupancy classifier',vision['checkpoint_sha256']],['Region preview',seg['checkpoint_sha256']],
            ['Historical LSTM',original_forecast['checkpoint_sha256']],
        ],[.24,.76]),
        p('The public feed latest snapshot and all source file paths are recorded as actual observations, not inferred recording dates. DAVIS physical fps remains unknown. Failed neural/data/software attempts and the first demo shutdown warning remain preserved. No public publishing, credentials, private CCTV or paid services were required.'),
        p('A student handoff should reproduce the declared steps, explain source/split/time boundaries and demonstrate unaided changes on fresh permitted data. The existence of code, reports and passing tests does not establish student mastery or official submission approval.'))
    # Improve digit/word spacing in authored prose only; identifiers/paths/URLs stay intact.
    import re
    def readable(text):
        protected={}
        for i,token in enumerate(['ResNet50FPNv2','ResNet50FPN','ResNet50','ResNet18','2D','3D','v003']):
            tag='CANONICALMODEL'+chr(65+i);protected[tag]=token;text=text.replace(token,tag)
        text=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',text)
        for tag,token in protected.items():text=text.replace(tag,token)
        return text.replace('project 001','project001').replace('%accuracy','% accuracy').replace('%reliable','% reliable')
    for pg in pages:
        for block in pg['blocks']:
            if block['kind']=='paragraph' and 'checkpoint is7227' not in block['text'] and 'SHA-256' not in block['text']:
                block['text']=readable(block['text'])
            elif block['kind']=='table':
                block['rows']=[[str(c) if any(prefix in str(c) for prefix in ['data/','models/','reports/','experiments/','configs/','.json']) or re.fullmatch('[0-9a-f]{64}',str(c)) or str(c).startswith('2026-') else readable(str(c)) for c in row] for row in block['rows']]
            elif block['kind']=='reference':
                block['text']=block['text'].replace('DOI10.24432','DOI 10.24432').replace('Licence1.0','Licence 1.0').replace('CC BY-NC4.0','CC BY-NC 4.0').replace('recorded28May2011','recorded 28 May 2011').replace('CC BY3.0','CC BY 3.0').replace('Computation9(8),1735','Computation 9(8), 1735')
    content=dict(title='Smart Parking with Deep Learning',version='v003',as_of=as_of,pages=pages,metrics=report_metrics)
    (PROJECT/'report_content.json').write_text(json.dumps(content,indent=2)+'\n',encoding='utf-8')
    (PROJECT/'report_inputs.json').write_text(json.dumps(dict(created_at=now.isoformat(),inputs=inputs,scope='Saved evidence plus development-only illustration; no new model accuracy evaluation'),indent=2)+'\n',encoding='utf-8')
    # Embed common system fonts when available; the report uses ASCII punctuation.
    font='Helvetica';bold='Helvetica-Bold'
    if Path('C:/Windows/Fonts/arial.ttf').exists():
        pdfmetrics.registerFont(TTFont('ReportArial','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('ReportArialBold','C:/Windows/Fonts/arialbd.ttf'))
        font='ReportArial';bold='ReportArialBold'
    body=ParagraphStyle('Body',fontName=font,fontSize=10.1,leading=14,spaceAfter=8,splitLongWords=True)
    heading=ParagraphStyle('Heading',fontName=bold,fontSize=16,leading=20,spaceAfter=13)
    cell=ParagraphStyle('Cell',fontName=font,fontSize=8.8,leading=11.5,splitLongWords=True)
    head=ParagraphStyle('TableHead',parent=cell,fontName=bold,textColor=colors.white)
    caption=ParagraphStyle('Caption',fontName=font,fontSize=8.4,leading=11,spaceAfter=9,textColor=colors.HexColor('#52606d'))
    reference=ParagraphStyle('Reference',parent=body,fontSize=9,leading=12.3,spaceAfter=8)
    width=A4[0]-96
    def para(text,style=body):return Paragraph(escape(text),style)
    story=[]
    for i,pg in enumerate(pages):
        if i:story.append(PageBreak())
        story.append(para(pg['title'],heading))
        for block in pg['blocks']:
            kind=block['kind']
            if kind=='paragraph':story.append(para(block['text']))
            elif kind=='reference':
                story.append(Paragraph(escape('['+block['number']+'] '+block['text'])+'<br/><link href="'+escape(block['url'],{'"':'&quot;'})+'" color="#245c88">'+escape(block['url'])+'</link>',reference))
            elif kind=='figure':
                image=Image(str(figures/block['name']));ratio=image.imageWidth/image.imageHeight
                image.drawWidth=min(width,block['height']*ratio);image.drawHeight=image.drawWidth/ratio
                story.append(KeepTogether([image,Spacer(1,5),para(block['caption'],caption)]))
            elif kind=='table':
                data=[[para(h,head) for h in block['headers']]]+[[para(str(c),cell) for c in row] for row in block['rows']]
                table=Table(data,colWidths=[width*x for x in block['widths']],repeatRows=1,hAlign='LEFT')
                table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#273d52')),('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#eef2f6'),colors.white]),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#52606d'))]))
                story.extend([table,Spacer(1,10)])
    def chrome(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#bcc7d1'));canvas.line(48,A4[1]-32,A4[0]-48,A4[1]-32)
        canvas.setFont(font,8);canvas.setFillColor(colors.HexColor('#52606d'))
        canvas.drawString(48,A4[1]-25,'Smart Parking | Technical report draft v003')
        canvas.drawRightString(A4[0]-48,A4[1]-25,'25 October 2026')
        canvas.drawString(48,28,'AI-assisted development evidence. Official submission and student mastery unverified.')
        canvas.drawRightString(A4[0]-48,28,str(doc.page));canvas.restoreState()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=48,bottomMargin=45,
        title='Smart Parking with Deep Learning - Technical Report Draft v003',author='Python/Jupyter project; AI-assisted technical draft').build(story,onFirstPage=chrome,onLaterPages=chrome)
    # Editable counterpart shares content/figures and requires no raw data access.
    def tex(text):
        mapping={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
        return ''.join(mapping.get(c,c) for c in text)
    lines=[r'\documentclass[10pt,a4paper]{article}',r'\usepackage[margin=23mm]{geometry}',r'\usepackage[T1]{fontenc}',r'\usepackage{lmodern,graphicx,booktabs,longtable,array,xcolor}',r'\usepackage[hidelinks]{hyperref}',r'\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}',r'\begin{document}']
    for i,pg in enumerate(pages):
        if i:lines.append(r'\clearpage')
        lines.append(r'\section*{'+tex(pg['title'])+'}')
        for b in pg['blocks']:
            if b['kind']=='paragraph':lines.append(tex(b['text'])+'\n')
            elif b['kind']=='reference':lines.append('['+b['number']+'] '+tex(b['text'])+r'\par\url{'+b['url']+r'}\par')
            elif b['kind']=='figure':lines.extend([r'\begin{center}\includegraphics[width=.95\linewidth,height='+str(b['height'])+r'pt,keepaspectratio]{figures/'+b['name']+'}',r'\par\small '+tex(b['caption'])+r'\end{center}'])
            elif b['kind']=='table':
                spec=''.join('p{'+str(round(x*.90,3))+r'\linewidth}' for x in b['widths'])
                lines.extend([r'\begin{longtable}{'+spec+'}',r'\toprule '+' & '.join(tex(h) for h in b['headers'])+r'\\\midrule\endhead'])
                lines.extend(' & '.join(tex(str(c)) for c in row)+r'\\' for row in b['rows']);lines.append(r'\bottomrule\end{longtable}')
    lines.append(r'\end{document}')
    (PROJECT/'main.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    shutil.copy2(ROOT/'reports/overleaf/smart_parking_draft/references.bib',PROJECT/'references.bib')
    (PROJECT/'README.md').write_text('''# Technical report draft v003

report_content.json is the shared semantic content. The standalone PDF at
output/pdf/smart_parking_technical_report_v003.pdf is typeset with ReportLab.
main.tex is an editable LaTeX counterpart using the same paragraphs/tables/figures;
its compiler preview can have a different layout. references.bib preserves earlier
bibliographic metadata; main.tex contains the explicit numbered source list.
report_inputs.json pins saved inputs and source-register/receipt snapshots. No
model or raw final evaluation was rerun. The only source photo opened for the
new figure is development car-turn frame22. Earlier report versions are retained.
The PDF is a technical draft, not an official university-template submission.
''',encoding='utf-8')
    result=dict(pdf=str(OUT),pdf_sha256=sha(OUT),main_tex_sha256=sha(PROJECT/'main.tex'),content_sha256=sha(PROJECT/'report_content.json'),
        expected_sections=len(pages),input_records=len(inputs),source_entries=len(sources),as_of=as_of,
        standalone_pdf_engine='ReportLab',latex_counterpart='reports/technical_report_v003/main.tex',model_experiments_added=0)
    (E/'report_build.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':
    generate_figures() if '--figures' in sys.argv else main()
