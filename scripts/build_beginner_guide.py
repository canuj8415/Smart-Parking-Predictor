"""Create the student's readable progress handout from verified project evidence."""
from pathlib import Path
import hashlib,json
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/smart_parking_beginner_guide.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyGuide',fontName='Helvetica',fontSize=11,leading=16,spaceAfter=11,textColor=colors.HexColor('#213047')))
styles.add(ParagraphStyle(name='TitleGuide',fontName='Helvetica-Bold',fontSize=25,leading=30,spaceAfter=20,textColor=colors.HexColor('#123a56')))
styles.add(ParagraphStyle(name='SubGuide',fontName='Helvetica-Bold',fontSize=14,leading=19,spaceBefore=9,spaceAfter=9,textColor=colors.HexColor('#126b75')))
styles.add(ParagraphStyle(name='SmallGuide',fontName='Helvetica',fontSize=9,leading=13,spaceAfter=8))
story=[]
def p(text):story.append(Paragraph(text,styles['BodyGuide']))
def sub(text):story.append(Paragraph(text,styles['SubGuide']))
def page(number,title):
    if story:story.append(PageBreak())
    story.append(Paragraph(f'YOUR PARKING PROJECT / LESSON {number}',styles['SubGuide']))
    story.append(Paragraph(title,styles['TitleGuide']))
def table(rows,widths):
    data=[[Paragraph(str(c),styles['SmallGuide']) for c in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceef0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#cdd9e2'))]))
    story.extend([t,Spacer(1,12)])

page(1,'Think of a digital parking attendant')
p('Imagine a shopping centre with 40 parking spaces. A human attendant looks around, identifies cars, checks each marked space and tells arriving drivers where they might park. Our Python project is learning to perform parts of that job.')
sub('The project has three separate jobs')
table([['Job','Everyday example','What supplies the answer'],['See the car park','Look through a camera and check marked spaces.','Parking photos, vehicle models and a matching space map.'],['Predict later availability','Estimate how busy it may be in 30 minutes.','Past time-stamped parking counts from Birmingham.'],['Read a live noticeboard','Check the official number of available spaces now.','Singapore public availability feed.']],[90,160,241])
p('These are separate data sources. A Singapore availability reading does not prove that our camera detected a car correctly. Our Birmingham forecasting model has not been validated for Singapore.')
sub('A real application example')
p('One configured 40-space photo produced <b>35 occupied, 2 vacant and 3 uncertain</b>. Uncertain means the evidence is insufficient or conflicting. It does not mean free. A vehicle count can differ from an occupied-space count because a car may be outside the marked spaces or partly hidden.')
p('<b>Your role:</b> learn what goes into each answer, where mistakes happen and what evidence supports a claim. You do not need to understand all the mathematics before trying the application.')

page(2,'Where our real data lives')
p('The project folder is <b>D:\\deep learning\\project001</b>. Original downloads are kept under <b>data/raw</b>. Prepared tables are kept separately, so cleaning does not overwrite the source.')
table([['Source','What we actually collected','Main location inside the project'],['PKLot / UFPR, Brazil','Full original archive; 1,701 working photo/XML pairs. XML describes labelled spaces.','data/raw/pklot_subset/<br/>data/manifests/pklot_frames.csv<br/>data/manifests/pklot_crops.csv'],['UCI Parking Birmingham','35,717 original rows; 35,116 accepted, 601 quarantined.','data/raw/uci_parking_birmingham/dataset.csv<br/>data/splits/birmingham-global-days-v1/'],['Official Singapore feed','6 saved snapshots; 2,005 car parks in the latest snapshot.','data/raw/singapore_live/<br/>data/processed/singapore_live_observations.csv'],['Street traffic / Editor','One licensed moving street recording. It has no parking-space answer labels.','data/raw/wikimedia_street_traffic/Street_traffic.webm']],[106,177,208])
sub('What is a CSV?')
p('A CSV is a plain table: each line is a row and commas separate columns. Excel can open it. A parking row might contain the car-park ID, observation time, capacity and number of occupied spaces. A saved live JSON is the original structured reply received from the provider.')
p('The source ledger is <b>data/source_manifest.csv</b>. Download receipts and checksums are in <b>data/resource_receipts.jsonl</b>. A checksum is a digital fingerprint: it helps us detect whether a file changed. Source and licence explanations are in <b>docs/THIRD_PARTY_SOURCES.md</b>.')

page(3,'What training actually means')
p('Think of teaching a new attendant using photographs with correct answers. The model makes a guess, compares it with a label and adjusts its learned numbers. Repeating that process on training examples is called training. One pass through the training examples is an epoch.')
table([['Group','School analogy','Why we separate it'],['Training','Practice exercises','The model learns from these answers.'],['Validation','A coach checks progress','We choose settings and decide whether a candidate is promising.'],['Final test','An unseen exam','We evaluate the frozen choice. Repeatedly choosing changes using this exam spoils its independence.']],[94,145,252])
p('Nearby photos can look almost identical. We group parking images by capture date and preserve the split when making crops. For forecasts, time moves forward: future rows must never help predict an earlier target.')
sub('What have we trained ourselves?')
p('The project trained an occupancy classification head on ResNet18 features, experimental parking-region U-Nets, historical LSTM forecasters and a small teaching VAE. Faster R-CNN and Mask R-CNN use pretrained upstream vehicle models; we have not trained those detectors ourselves.')
sub('Three useful measurements')
p('<b>Accuracy:</b> 343 correct answers out of 360 labelled test crops is 95.28%. This is a small crop-classification test, not whole-system accuracy.<br/><b>MAE:</b> if 10 spaces are actually available and we predict 7, the error is 3 spaces. MAE averages those absolute errors.<br/><b>IoU:</b> how much the predicted painted region overlaps the correct region. An illustrative intersection of 6 pixels and union of 10 gives IoU 0.6.')

page(4,'What the evidence says today')
p('Snapshot: <b>24 October 2026, India time</b>. Each row answers a different question. They cannot be merged into one overall accuracy percentage.')
table([['Part','Measured result','How to read it'],['Occupancy classifier','343/360 correct; 95.28%','Small held-out crop set. Wider camera and weather reliability remains uncertain.'],['New region segmentation','IoU 0.481 on 6 fresh final frames; old model 0.253 on those same frames.','A simple camera-geometry baseline scored 0.768. Candidate failed its gate; not promoted.'],['Original forecast','Final-test MAE 121.21 spaces versus persistence 61.14.','The original LSTM loses to simply keeping the latest count.'],['Development forecast','Best validation MAE 20.90 versus persistence 40.22.','Promising aggregate result, but some parks fail the gate. No final-test or production promotion.'],['Live baseline','2,174 later matched outcomes; MAE 2.218 spaces.','Non-neural persistence, two issue cohorts, variable 20-45 minute matching rule. Not live camera or neural accuracy.'],['Real moving video','1,050 frames decoded; 18 sampled detections, up to 34 seconds.','Processing works. No labels to measure detection, parking occupancy or entrance/exit accuracy.'],['Software checks','44 automated checks pass.','These check program behaviour; they do not imply 100% model accuracy.']],[98,185,208])
p('On this CPU, the real-video run took a median <b>8.16 seconds per analysed frame</b> (95th percentile 10.55 seconds). It is an offline demonstration, not real-time video. The run also found incorrect reported video frame-rate metadata; sampling now uses presentation timestamps when requested.')

page(5,'Try it, then explain it back')
sub('A short application walkthrough')
p('1. Open <b>launch_parking.cmd</b> in the project folder.<br/>2. In the image/video area, load a supplied parking photo and its matching layout. The layout tells the application where spaces are.<br/>3. Start analysis. Read the occupied, vacant and uncertain counts and look at the overlay.<br/>4. Change the photo or threshold. Old counts should clear before fresh analysis.<br/>5. Try the historical forecast area separately. Compare its error with the persistence baseline in the reports.<br/>6. Open the live area. Check the provider time and any stale/cached indication before trusting the displayed availability.')
p('The video API can analyse vehicles without a layout. It must then report parking occupancy as unavailable, not zero. The current desktop video workflow still expects a matching parking layout; arbitrary road-video testing was performed through the project validation script.')
sub('How Python and Jupyter fit together')
p('Python contains the actual program, models and training work. A Jupyter notebook is a learning workbook: explanatory text sits beside Python cells, results and pictures. Start with <b>notebooks/02_parking_product.ipynb</b>. Run cells in order and read the output before moving on.')
sub('Five quick questions to practise')
p('<b>Why can 10 detected cars occupy only 8 mapped spaces?</b> Some cars may be outside the layout or multiple detections may relate to one space.<br/><b>Is uncertain a free space?</b> No.<br/><b>Does a current Singapore count prove our camera works?</b> No; it is a separate aggregate source.<br/><b>What is persistence?</b> Predicting that the latest known count stays the same.<br/><b>Do 44 passing tests mean perfect AI?</b> No; software correctness and prediction quality require different evidence.')

page(6,'What is done, and what comes next')
table([['Stage','Current position'],['Working','Python desktop app, executed product notebook, real image inference, occupancy head, source records, official live-feed collection and genuine moving-video integration.'],['Experimental','Learned parking regions and historical forecasting. New candidates are preserved but have not passed all promotion gates.'],['Still needed','Labelled parking-video evaluation; detector accuracy benchmark; actual entrance/exit tracking; stronger generalisation and forecasting; broader app/offline rehearsal; final report, presentation and student practice.'],['Official acceptance','The two university documents have not been supplied. We cannot verify the official rubric, dates, template or compliance. Independent product development continues.']],[112,379])
p('Since the schedule was created, <b>9 recorded experiments or validation trials</b> have completed, including the failed first road-video sampling trial. A frame or epoch is not a separate experiment. The separate 100-run live checkpoint is still due at run 100. Real source collection also occurs once per scheduled wakeup when reachable.')
p('There is no honest date at which a system becomes universally 100% accurate. Completion means meeting explicit acceptance checks and explaining remaining limits. We keep failures because they show what was tried and prevent misleading claims.')
sub('Credits and further reading')
for text in [
    'PKLot: Almeida et al. (2015), UFPR dataset, CC BY 4.0. <link href="https://web.inf.ufpr.br/vri/databases/parking-lot-database/" color="#126b75">Official dataset page</link>.',
    'Parking Birmingham: UCI Machine Learning Repository, dataset 482. <link href="https://archive.ics.uci.edu/dataset/482/parking+birmingham" color="#126b75">Dataset and attribution</link>.',
    'Singapore car-park availability: data.gov.sg / HDB, Singapore Open Data Licence. <link href="https://data.gov.sg/open-data-licence" color="#126b75">Licence</link>. Public aggregate availability, not camera labels.',
    'Street traffic: Editor, via Wikimedia Commons, CC BY 3.0. Derived frames/overlays are modified for academic evaluation. No endorsement. <link href="https://commons.wikimedia.org/wiki/File:Street_traffic.webm" color="#126b75">Original source and licence record</link>.',
    'Full upstream model, software, dataset and AI-assistance records are retained in docs/THIRD_PARTY_SOURCES.md, docs/MODEL_PROVENANCE.md and docs/AI_ASSISTANCE_LOG.md. This is an AI-assisted learning guide; independent student understanding has not been assessed.'
]:story.append(Paragraph(text,styles['SmallGuide']))

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#cdd9e2'));canvas.line(52,43,A4[0]-52,43)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526579'))
    canvas.drawString(52,30,'SMART PARKING | Beginner guide | 24 October 2026 IST')
    canvas.drawRightString(A4[0]-52,30,f'{doc.page} / 6')
SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=42,bottomMargin=60,title='Smart Parking: A Beginner Guide',author='Smart Parking project; AI-assisted').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
print(hashlib.sha256(OUT.read_bytes()).hexdigest())
