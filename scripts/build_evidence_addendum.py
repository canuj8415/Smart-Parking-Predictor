"""Dated standalone evidence addendum;metadata/results only,no new scoring."""
import csv,hashlib,json,shutil,sys,subprocess
from datetime import datetime,timedelta,timezone
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'reports/evidence_addendum_20261027'
PDF=ROOT/'output/pdf/smart_parking_evidence_addendum_20261027.pdf'


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def generate_figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    state=read(PROJECT/'inputs/data/automation_state.json');final=state['forecast_temporal_final']
    traffic=read(PROJECT/'inputs/models/uvg_detector_development.json');tiles=read(PROJECT/'inputs/models/uvg_tile_development.json');sg=read(PROJECT/'inputs/models/singapore_trend_development.json')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(7,2.5),layout='constrained');xs=range(3);names=['640 full frame','960 full frame','960 + native crops']
    faster=[traffic['baseline_results']['fasterrcnn']['eligible_provided']['matched_positives'],traffic['candidate_results']['fasterrcnn']['eligible_provided']['matched_positives'],tiles['results']['fasterrcnn']['eligible_provided']['matched_positives']]
    masks=[traffic['baseline_results']['maskrcnn']['eligible_provided']['matched_positives'],traffic['candidate_results']['maskrcnn']['eligible_provided']['matched_positives'],tiles['results']['maskrcnn']['eligible_provided']['matched_positives']]
    a=ax.bar([x-.18 for x in xs],faster,.35,label='Faster R-CNN',color='#236a89');b=ax.bar([x+.18 for x in xs],masks,.35,label='Mask R-CNN',color='#dc8359');ax.bar_label(a,padding=2);ax.bar_label(b,padding=2);ax.set(xticks=list(xs),xticklabels=names,ylabel='Matched provided targets / 153',ylim=(0,170));ax.legend(loc='upper left',ncols=2,frameon=False,fontsize=8);fig.savefig(PROJECT/'figures/traffic_comparison.png',dpi=180);plt.close(fig)
    fm=final['metrics'];fig,axes=plt.subplots(1,2,figsize=(7,2.4),layout='constrained')
    for ax,values,labels,title in [(axes[0],[fm['original_lstm_mae_spaces'],fm['persistence_mae_spaces'],fm['candidate_mae_spaces']],['Original','Persistence','Candidate'],'Birmingham: later-date FINAL'),(axes[1],[sg['persistence']['mae_spaces'],sg['candidate']['mae_spaces']],['Persistence','LAD trend'],'Singapore: DEVELOPMENT only')]:
        bars=ax.bar(labels,values,color=['#8895a4','#ce9066','#228578'][:len(values)]);ax.bar_label(bars,labels=[f'{v:.2f}' for v in values],padding=3,fontsize=8);ax.set_title(title,fontsize=10);ax.set_ylabel('MAE in spaces');ax.set_ylim(0,max(values)*1.25);ax.tick_params(axis='x',labelsize=8)
    fig.savefig(PROJECT/'figures/forecast_comparison.png',dpi=180);plt.close(fig)


def main():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
    assert not PROJECT.exists() and not PDF.exists(),'Preserve earlier artifacts;choose a new version'
    PROJECT.mkdir(parents=True);(PROJECT/'inputs').mkdir();(PROJECT/'figures').mkdir();PDF.parent.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc);local=now.astimezone(timezone(timedelta(hours=5,minutes=30)));inputs=[]
    def snapshot(relative):
        source=ROOT/relative;target=PROJECT/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        inputs.append(dict(origin=relative,snapshot=target.relative_to(PROJECT).as_posix(),bytes=target.stat().st_size,sha256=sha(target)))
        return read(target)
    state=snapshot('data/automation_state.json');region=snapshot('models/region_stability_final.json')
    bir=snapshot('models/forecast_final_evaluation.json');sg=snapshot('models/singapore_trend_development.json')
    traffic=snapshot('models/uvg_detector_development.json');tiles=snapshot('models/uvg_tile_development.json');dedup=snapshot('models/uvg_mask_duplicate_development.json')
    groups=snapshot('models/pklot_remaining_group_audit.json');view=snapshot('models/view_compatibility_development.json')
    nd=snapshot('models/ndispark_metadata_card.json');offline=snapshot('reports/offline_refresh_recovery_latest.json');live=snapshot('data/processed/singapore_prospective/summary.json');health=snapshot('reports/singapore_issuance_health_latest.json')
    package=snapshot('reports/offline_demo_latest.json');snapshot('data/manifests/singapore_forecast_reservation_v1.json')
    assert state['completed_recorded_runs_since_schedule']==87 and health['forecasts_logged']==10764 and health['global_origins']==10
    for relative in ['data/source_manifest.csv','data/resource_receipts.jsonl']:
        source=ROOT/relative;target=PROJECT/'inputs'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        inputs.append(dict(origin=relative,snapshot=target.relative_to(PROJECT).as_posix(),bytes=target.stat().st_size,sha256=sha(target)))
    with (PROJECT/'inputs/data/source_manifest.csv').open(encoding='utf-8',newline='') as f:sources=list(csv.DictReader(f))
    assert len(sources)==len({s['source_id'] for s in sources})==62
    # Immutable historical scores are copied,never recomputed from labels.
    final=state['forecast_temporal_final'];occupancy=state['occupancy_final_evaluation'];conditional=state['region_stability']
    subprocess.run(['D:/deep learning/.venv/Scripts/python.exe',str(Path(__file__).resolve()),'--figures'],check=True,timeout=60)
    fm=final['metrics']
    navy=colors.HexColor('#16314c');teal=colors.HexColor('#147f79');muted=colors.HexColor('#526477');pale=colors.HexColor('#edf3f7')
    pdfmetrics.registerFont(TTFont('EvidenceSans','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('EvidenceBold','C:/Windows/Fonts/arialbd.ttf'))
    styles={
        'title':ParagraphStyle('title',fontName='EvidenceBold',fontSize=25,leading=30,textColor=navy,spaceAfter=15),
        'h':ParagraphStyle('h',fontName='EvidenceBold',fontSize=18,leading=23,textColor=navy,spaceAfter=14),
        'sub':ParagraphStyle('sub',fontName='EvidenceBold',fontSize=11,leading=15,textColor=teal,spaceBefore=10,spaceAfter=7),
        'body':ParagraphStyle('body',fontName='EvidenceSans',fontSize=9.4,leading=13.5,textColor=navy,spaceAfter=9),
        'small':ParagraphStyle('small',fontName='EvidenceSans',fontSize=7.8,leading=11,textColor=muted,spaceAfter=7),
        'cell':ParagraphStyle('cell',fontName='EvidenceSans',fontSize=8.1,leading=11,textColor=navy),
        'head':ParagraphStyle('head',fontName='EvidenceBold',fontSize=8.1,leading=11,textColor=colors.white)}
    content=[];story=[]
    def para(text,kind='body'):
        content.append(dict(kind=kind,text=text));return Paragraph(escape(text),styles[kind])
    def page(title):
        if story:story.append(PageBreak())
        story.append(para(title,'h'))
    def p(text,kind='body'):story.append(para(text,kind))
    def table(headers,rows,widths):
        content.append(dict(kind='table',headers=headers,rows=rows))
        data=[[Paragraph(escape(str(v)),styles['head']) for v in headers]]+[[Paragraph(escape(str(v)),styles['cell']) for v in row] for row in rows]
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[pale,colors.white]),('LINEBELOW',(0,0),(-1,0),.5,teal)]));story.append(t);story.append(Spacer(1,10))
    def image(name,height):story.append(Image(str(PROJECT/'figures'/name),width=500,height=height));story.append(Spacer(1,7))
    # 1
    story.append(para('Smart Parking\nEvidence update'.replace('\n',' / '),'title'))
    p('A dated addendum to the earlier technical report. This update records saved experiments and software checks; it does not rerun models or reopen final data.','body')
    p(local.strftime('Input snapshot: %d %B %Y, %H:%M IST')+' | '+now.strftime('%d %B %Y, %H:%M UTC'),'small')
    table(['Verified software','Registered sources','Live study','Scientific status'],[['392 main-project tests','62 permanent IDs','10 logged learned origins','Future accuracy pending']],[126,120,126,128])
    p('What is supported now','sub')
    p('The selected copied demonstration includes transactional result saving, a fresh local 107-package installation, actual hidden app checks, 13 synthetic export-failure cases and a real copied Jupyter kernel. The initial installer and notebook failures remain in the evidence record. [E6]')
    p('Birmingham forecasting has one completed later-date final result that beats persistence. The Singapore trend method improved development MAE, but its reserved future evaluation is still closed. These are separate sources and cohorts. [E4, E5]')
    p('What is not complete','sub')
    p('Vision remains conditional and limited. The stored-geometry region result needs a matching known view; the automatic view checker failed usability. Real traffic mask admission and the paired occupancy promotion gate failed. Production weights remain unchanged. [E1-E3]')
    p('Fresh vision evaluation needs new qualified groups. The six groups previously described as provisional unused dates are now accounted for: three development groups and three consumed final groups. No replacement final set was admitted. [E7]')
    p('Reading this document','sub')
    p('IoU is mask overlap, MAE is forecast error in spaces, provided-target matching is partial-label coverage, and software tests check program behavior. None is a universal parking accuracy percentage. A run counts one completed recorded trial, not a frame, epoch, forecast or test assertion.')
    p('87 recorded trials existed at input freeze; this document review is excluded from that snapshot count. Student mastery, physical offline rehearsal, new-machine behavior and official academic compliance remain unassessed. University documents have not been supplied.','small')
    # 2
    page('1 / Parking regions and occupancy')
    table(['Saved result','Cohort','Measured outcome'],[['Conditional region router','6 photos; 3 known camera/date groups',f"IoU {conditional['final_iou']:.3f}; gate passed conditionally"],['Frozen image-only comparator','Same six photos',f"IoU {conditional['image_only_cnn_iou']:.3f}"],['Automatic view checker','16 matching-camera; 32 wrong-camera pairs','1/16 accepted; 0/32 wrong accepted; usability failed'],['Paired occupancy candidate','336 labelled slots; 6 photos; 3 groups','Aggregate improved, but per-group promotion gate failed']],[151,172,177])
    p('Why the region score is conditional','sub')
    p('PUCPR and UFPR05 use stored training geometry, not neural image segmentation, in the conditional router. UFPR04 uses the frozen CNN and scored about 0.662. Correct camera identity and a compatible view are required. Matching dimensions do not prove the camera has not moved. All three final groups are consumed. [E1]')
    p('The ORB/homography view checker rejected all 32 wrong-camera pairs and 48 synthetic shifted/rotated/flipped cases, but accepted only 1 of 16 matching-camera pairs. Rejecting almost everything does not make a usable view gate. Synthetic changes are not real camera-relocation ground truth. No app integration or threshold retuning followed. [E1]')
    p('Why higher aggregate occupancy scores were not promoted','sub')
    p('The paired candidate reached about 98.81% hard accuracy across 336 labels and zero confident false-vacant decisions on that small final cohort. It still failed the frozen retention rule: on rainy PUCPR, only 13 of 14 previously correct vacant cases were retained (92.86%, below 95%), for both detectors. The original checkpoint was retained. [E2]')
    p('A separate source-transfer study trained heads with 16,448 new-source TRAIN crops plus 10,104 original crops. Plain and teacher-anchored studies produced 20 and 18 development errors versus 12 for the warm comparison. Both kept epoch zero; neither established source-independent or night-time improvement. These are reused development results. [E2]')
    p('Next scientific requirement','sub')
    p('Before evaluating a changed view/region/occupancy method, establish a legitimate fresh camera/session/date reservation with matching labels. Preserve failures and use predeclared per-group gates. Do not recycle different frames from consumed dates.')
    # 3
    page('2 / Real traffic instance-mask evidence')
    p('HighwayView DEVELOPMENT: 11 fixed frames, 194 supplied car/truck observations, 153 eligible targets and 34 road-vehicle tracks. Frames from one clip are correlated. Forty-one smaller observations were outside the eligibility gate; 10 supplied train-class observations were outside the product classes. [E3]')
    image('traffic_comparison.png',180)
    table(['Setting','Mask matches / 153','Zero-inclusive mask IoU'],[['640 full frame','67 / 153',f"{traffic['baseline_results']['maskrcnn']['mask_zero_inclusive_mean_iou']:.3f}"],['960 full frame','87 / 153',f"{traffic['candidate_results']['maskrcnn']['mask_zero_inclusive_mean_iou']:.3f}"],['960 + native crops','113 / 153',f"{tiles['results']['maskrcnn']['mask_zero_inclusive_mean_iou']:.3f}"]],[190,139,171])
    p('Improvement is not the same as acceptance','sub')
    p('Native crops improved provided-target coverage and mask overlap while retaining the full-frame outputs. Mask coverage was still 73.86%, below the frozen 75% gate; the detector-gap and extra-unassigned-output gates also failed. Unassigned predictions are not confirmed false positives without exhaustive labels. No precision, mAP, parking occupancy or independent final accuracy is claimed.')
    p('A later containment-based suppression rule removed 26 crop additions but lost two correct car matches: 113 became 111, and zero-inclusive IoU fell from 0.599 to 0.590. It was rejected. The inspection-only alternative retains all 209 outputs and flags conflicts for review; flags are not confirmed duplicates.')
    p('HighwayDrive remains reserved and unopened. A suitable final claim controller and a candidate passing its fixed development gates are required before any future final evaluation.','small')
    # 4
    page('3 / Forecasts: separate cohorts, separate claims')
    image('forecast_comparison.png',175)
    p('Historical Birmingham: completed final evidence','sub')
    p(f"The frozen candidate scored MAE {fm['candidate_mae_spaces']:.2f} spaces versus persistence {fm['persistence_mae_spaces']:.2f}, an {100*fm['improvement_vs_persistence']:.1f}% reduction on the same 1,853 later-date windows across 8 dates and 29 eligible car parks. The final gate passed; these dates are now consumed. Matched readings arrived 10.02-29.12 minutes after issue, so this is not exact 30-minute accuracy or Singapore validation. The result is available as an archived app report; production weights were not replaced. [E4]")
    p('Singapore: development passed; prospective result pending','sub')
    p(f"The selected source-specific LAD trend is non-neural. On 9,202 development windows from nine global origins, MAE was {sg['candidate']['mae_spaces']:.3f} versus {sg['persistence']['mae_spaces']:.3f} for persistence (about 9.3% lower). An earlier ridge residual candidate failed and remains recorded. Many car parks do not provide many independent days. [E5]")
    p(f"At this snapshot, {health['forecasts_logged']:,} genuine forecasts were logged at {health['global_origins']} origins before their target windows. Learned target matching, coverage and MAE have NOT been evaluated. The reserved evaluation closes 27 October 2026 at 16:21 IST (10:51 UTC). Ten logged origins do not guarantee eight matched origins. The once-only scorer must enforce all frozen coverage and error gates.")
    p(f"The separate rolling persistence study has {live['scores_total']:,} matched outcomes and MAE {live['baseline_mae_spaces']:.6f} spaces. It uses a different rolling cohort; do not compare this number directly with the learned development or prospective result. Missing targets stay unscored, not zero-error. Singapore aggregate availability is not camera ground truth.", 'small')
    # 5
    page('4 / Data roles, provenance and rights')
    table(['Camera','Capture date','Current role'],[[x['camera_id'].upper(),x['capture_date'],'Consumed final' if x['status']=='consumed_final' else 'Development exposed'] for x in groups['groups']],[120,150,230])
    p('What the new metadata audit establishes','sub')
    p('The earlier archive inventory identified six provisional candidates. Current development manifests account for three; durable whole-camera/date claims consume the other three, including failed evaluations. Frozen manifests retain their original unopened flags for provenance; a later durable claim determines whether reuse is permitted. No JPEG, XML semantic labels or archive bodies were opened by this audit. [E7]')
    p('This accounts for those six candidates under the earlier conservative policy. It does not prove that no other camera, source, newly acquired date or independently qualified group exists. Metadata that is merely unaccounted for is not automatically eligible final data.')
    p('Rights and label boundaries','sub')
    p('PKLot is the existing attributed CC BY 4.0 source. UVG-VCM explicitly licenses its annotated dataset under CC BY 4.0; absent raster support remains unknown. The Open-Space source declares author-created photos/labels and CC BY 4.0, but its whole collection is development-exposed because capture groups are unqualified.')
    p('NDISPark inspection verified 259 JPEG names and the README, not image content. The record declares ODC-BY database rights; individual image/annotation rights remain unqualified. No image pixels or annotation bodies were used. CNRPark content rights remain a separate unresolved question. The database licence must not be silently treated as an image-content grant. [E8]')
    p('The source register has 62 permanent IDs, not 62 trained datasets. Original bytes, acquisition receipts, failed runs and best checkpoints are preserved. No new model evaluation or source-content acquisition was performed for this report.','small')
    # 6
    page('5 / Software acceptance and remaining work')
    table(['Area','Executed evidence','Limit'],[['Result saving','13 synthetic fault/integrity cases; real archived exports','Not power-loss recovery'],['Copied environment','107 exact package versions; hash-locked no-index install','Existing Windows/base Python/Tk'],['App + notebook','Hidden app routes; real copied kernel; one plot','Not visible/manual/student acceptance'],['Selected payload',f"{package['files']} files; {package['bytes']:,} bytes",'Notebook08 only; 10 others absent']],[126,227,147])
    p('Preserved failures explain the recovery','sub')
    p('An initial pip bootstrap failed without detailed child output being retained; its cause was not established. The installer now captures bootstrap logs and uses package-local temporary storage. A later notebook check timed out. Phase/stack evidence localized a stall before kernel start in Windows local asyncio socket creation.')
    p('With explicitly approved local-loopback access and the original external-network/workspace-fallback guards, the unchanged copied verifier completed in 18.187 seconds. It executed the original four code cells plus one diagnostic cell, produced one plot, and preserved source/payload hashes. Initial failed reports remain failed. A new hash-linked acceptance record, not an edited failure, now selects the ready copy. No reinstall or detector replay was needed in revalidation. [E6]')
    p('Acceptance still open','sub')
    p('1. Acquire genuinely new, legitimately usable labelled vision groups and reserve them before changed-method evaluation. Keep unknown regions and unsupported labels distinct from background negatives.')
    p('2. Complete a visible/manual export-dialog and physically disconnected rehearsal on the intended machine; assess student explanation independently. The automated copy check does not establish these outcomes.')
    p('3. After the fixed Singapore closure, run the frozen once-only scorer and report its actual matched coverage, MAE and persistence comparison, including failure or non-evaluability.')
    p('4. Audit supplied university documents before claiming official compliance. Use this addendum with the earlier report and preserved experiment records; it is not a substitute for a rubric or a final project-completion certificate.')
    # 7
    page('6 / Evidence index and reproducibility')
    table(['ID','Local saved evidence','Scope'],[
        ['E1','models/region_stability_final.json; models/view_compatibility_development.json','Conditional six-photo final; failed reused-development view gate'],
        ['E2',occupancy['run_id']+'; docs/TRANSFER_LEARNING_EXPLAINED.md','Consumed paired final; rejected source-transfer heads'],
        ['E3','models/uvg_detector_development.json; uvg_tile_development.json; uvg_mask_duplicate_development.json','One traffic development clip; no final access'],
        ['E4','models/forecast_final_evaluation.json; '+final['run_id'],'Completed chronological Birmingham final'],
        ['E5','models/singapore_trend_development.json; singapore_forecast_reservation_v1.json; issuance health snapshot','Development plus prospective logging; future result pending'],
        ['E6','reports/offline_refresh_recovery_latest.json; reports/offline_demo_latest.json','Composite software acceptance; original failures retained'],
        ['E7',groups['run_id'],'Metadata-only reconciliation of six prior candidates'],
        ['E8','models/ndispark_metadata_card.json; data/source_manifest.csv; data/resource_receipts.jsonl','Source/rights/acquisition records; no unqualified image use']],[29,290,181])
    p('Attribution and primary source entry points','sub')
    p('PKLot: Almeida et al., UFPR, CC BY 4.0; https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/ . Birmingham parking: UCI dataset, source SRC-DS-003. UVG-VCM: Tampere University / Ultra Video Group, CC BY 4.0; https://ultravideo.fi/UVG-VCM/index.html . Singapore Carpark Availability: data.gov.sg / HDB, Singapore Open Data Licence 1.0; no government endorsement. NDISPark: Ciampi, Santiago, Costeira, Gennaro and Amato, DOI 10.5281/zenodo.6560823; content use not admitted.','small')
    p('Reproduction and authorship','sub')
    p('The companion report_inputs.json records exact source snapshots and SHA-256 values. report_content.json preserves the authored text/tables; figures and this builder are retained. The PDF is generated with ReportLab and rendered with Poppler for visual review. This addendum uses already saved results only, with no raw final-image or learned prospective-target decoding.','small')
    p('Prepared with Codex assistance. It records agent implementation and executed checks; it does not assert independent student authorship, understanding or presentation mastery. All earlier reports, source bytes, pretrained weights and failed experiments remain preserved.','small')
    def footer(canvas,doc):
        canvas.setStrokeColor(teal);canvas.setLineWidth(1);canvas.line(44,42,551,42);canvas.setFont('EvidenceSans',7);canvas.setFillColor(muted)
        canvas.drawString(44,29,'Smart Parking | dated evidence addendum | not official academic acceptance');canvas.drawRightString(551,29,str(doc.page))
    SimpleDocTemplate(str(PDF),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=43,bottomMargin=55,title='Smart Parking - Evidence Addendum',author='Project evidence, prepared with Codex assistance').build(story,onFirstPage=footer,onLaterPages=footer)
    dump(PROJECT/'report_content.json',content);dump(PROJECT/'report_inputs.json',dict(snapshot_at=now.isoformat(),local_snapshot=local.isoformat(),inputs=inputs,source_count=62,completed_trials_at_snapshot=87,software_tests=392,model_calls=0,learned_future_targets_decoded=False))
    shutil.copyfile(PDF,PROJECT/PDF.name)
    summary=dict(created_at=now.isoformat(),pdf=PDF.relative_to(ROOT).as_posix(),pdf_sha256=sha(PDF),project=PROJECT.relative_to(ROOT).as_posix(),inputs=len(inputs),input_manifest_sha256=sha(PROJECT/'report_inputs.json'),content_sha256=sha(PROJECT/'report_content.json'),builder_sha256=sha(__file__),model_calls=0,raw_final_or_future_targets_decoded=False,older_report_preserved=True,expected_pages=7,engine='ReportLab',official_compliance_claimed=False)
    dump(PROJECT/'build.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':generate_figures() if '--figures' in sys.argv else main()
