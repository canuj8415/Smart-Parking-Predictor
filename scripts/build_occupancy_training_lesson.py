"""Create a pinned, read-only teaching notebook from a completed training study."""
import argparse
import json
from pathlib import Path
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revise-unexecuted',action='store_true');args=parser.parse_args()
    card=json.loads((ROOT/'models/occupancy_expansion_candidate.json').read_text(encoding='utf-8'))
    data_run=json.loads((ROOT/'models/occupancy_expansion_data_card.json').read_text(encoding='utf-8'))['run_id']
    path=ROOT/'notebooks/09_occupancy_training_and_tradeoffs.ipynb'
    if path.exists():
        old=nbf.read(path,as_version=4)
        assert args.revise_unexecuted and all(not c.get('outputs') and c.get('execution_count') is None for c in old.cells if c.cell_type=='code'),'Preserve the existing executed lesson'
        previous=ROOT/'experiments/evidence/HEARTBEAT-20261026T011741Z/notebook_initial_source.json'
        assert not previous.exists();previous.write_text(path.read_text(encoding='utf-8'),encoding='utf-8')
    notebook=nbf.v4.new_notebook()
    notebook.metadata.update(kernelspec=dict(name='smart-parking-python',display_name='Python (Smart Parking)',language='python'),
        language_info=dict(name='python',version='3.12.10'),pinned_training_run=card['run_id'])
    markdown=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    notebook.cells=[markdown('''# 09 — Training a parking attendant, then checking its mistakes

Imagine teaching an attendant with photos from three different car parks. **Training** photos are practice questions with answers. **Validation** photos help choose the model and decide whether it is useful. **Final-test** photos are the sealed exam: we leave them closed while developing the model.

Our first classifier trained on two camera views. This study adds previously designated training dates from the third view. It trains only the small decision layer on frozen ResNet image features. The original model stays intact. This notebook reads a completed experiment; running it does **not** repeat training or open final-test photos.'''),
        code(f'''from pathlib import Path
import json, sys
from IPython.display import display, HTML
from html import escape
import matplotlib.pyplot as plt
ROOT = Path.cwd() if (Path.cwd()/'src').exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT/'src'))
from smart_parking.holdouts import assert_holdout_closed
PINNED_RUN = {card['run_id']!r}
folder = ROOT/'experiments/results'/PINNED_RUN
study = json.loads((folder/'run.json').read_text(encoding='utf-8'))
data = json.loads((ROOT/'experiments/results'/{data_run!r}/'run.json').read_text(encoding='utf-8'))
assert study['final_images_or_labels_read'] == 0
later_final = ROOT/'models/occupancy_expansion_final.json'
if later_final.exists():
    final_record = json.loads(later_final.read_text(encoding='utf-8'))
    assert final_record['all_final_groups_now_consumed']
    print('Training used no final images. A later paired final is now complete; those date groups are consumed.')
else:
    assert_holdout_closed(ROOT/'data/manifests/pklot_fresh_final_v2.json', root=ROOT)
print('Recorded experiment:', PINNED_RUN)
print('Archived development evidence only. This lesson does not repeat training or final evaluation.')'''),
        code('''def table(records, columns=None):
    records = list(records)
    if not records:
        print('No rows.'); return
    columns = columns or list(records[0])
    def value(item):
        return escape(f'{item:.4f}' if isinstance(item,float) else str(item))
    header = '<tr>' + ''.join('<th>'+escape(c)+'</th>' for c in columns) + '</tr>'
    body = ''.join('<tr>'+''.join('<td>'+value(r.get(c,''))+'</td>' for c in columns)+'</tr>' for r in records)
    display(HTML('<table>'+header+body+'</table>'))'''),
        markdown('''## 1. Which examples did we use?

All photos and original occupancy labels come from **PKLot, SRC-DS-001**. The ResNet starting features are attributed to **TorchVision/ImageNet, SRC-MOD-003**. Exact URLs, rights, archive-member names and checksums are in the source registry, resource receipts and qualification card.

A missing label means “we do not know the answer.” It must never be silently changed to “empty.” Several slots share the same photo, and repeated photos show the same spaces; these are correlated observations.'''),
        code('''coverage = data['summary']['label_coverage']
table(coverage,['role','camera_id','frames','explicit_labels','unknown_labels','vacant_labels','occupied_labels'])
print('Training dates:', data['summary']['train_dates'], '| Validation dates:', data['summary']['validation_dates'])
print('Missing labels excluded:', sum(r['unknown_labels'] for r in coverage))
table(study['training_strata'])'''),
        markdown('''## 2. What happened during learning?

An epoch is one pass over the training examples. It is not a new experiment. The best epoch is selected by the validation loss, with early stopping after six epochs without a sufficient improvement. Camera/class balancing uses training counts only.

The two loss curves use different weighting, so compare their trends rather than treating their numerical sizes as the same measurement.'''),
        code('''curves = json.loads((folder/'curves.json').read_text(encoding='utf-8'))
fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
for ax, column, title in zip(axes,
    ['train_weighted_cross_entropy','validation_macro_camera_cross_entropy'],
    ['Training loss (camera/class weighted)','Validation loss (mean across cameras)']):
    ax.plot([r['epoch'] for r in curves], [r[column] for r in curves], color='#147d92')
    ax.axvline(study['selected_epoch'], color='#a74d35', linestyle='--', label='Selected epoch')
    ax.set(xlabel='Epoch', ylabel='Cross-entropy', title=title)
    ax.grid(alpha=.2); ax.legend()
fig.tight_layout(); plt.show()
print('Completed epochs:', study['epochs_completed'], '| Selected epoch:', study['selected_epoch'])'''),
        markdown('''## 3. Is the new model actually better?

**Wrong empty** means directing a driver to an occupied space. **Wrong occupied** means overlooking a usable empty space. **Needs review** means the model has not made a definite decision. We report all three; refusing more answers must not be presented as universal accuracy.

The first table uses all 2,028 labelled validation spaces. The second uses the same 720 recently reserved development examples from the earlier comparison. Neither table is a final-test or live camera score.'''),
        code('''def row(name, values):
    return {'Model':name, 'Examples':values['samples'], 'Forced yes/no errors':values['hard_errors'],
            'Forced yes/no accuracy':values['hard_accuracy'], 'Wrong empty':values['false_vacant'],
            'Correct empty':values['correct_vacant_predictions'], 'Wrong occupied':values['false_occupied'],
            'Needs review':values['uncertain']}
table([row('Original',study['baseline']['overall']),row('Candidate',study['candidate']['overall'])])
table([row('Original: fresh development',study['fresh12_baseline']),row('Candidate: fresh development',study['fresh12_candidate'])])
table([{'Check set before training':key, 'Passed':value} for key,value in study['checks'].items()])
print('All development checks passed:', study['validation_gate_passed'])
print('Installed as the app default:', study['production_promoted'])'''),
        markdown('''## 4. Look at the remaining errors

A model can improve the overall total while making a particular date worse. That is why the experiment also checks individual camera views and dates. A failed check stays in the record; we do not change its rule after seeing the results.'''),
        code('''before = study['baseline']['per_date']
after = {(r['camera_id'],r['date']):r for r in study['candidate']['per_date']}
table([{'Camera':r['camera_id'],'Date':r['date'],'Examples':r['samples'],
    'Original errors':r['hard_errors'],'Candidate errors':after[(r['camera_id'],r['date'])]['hard_errors'],
    'Original wrong empty':r['false_vacant'],'Candidate wrong empty':after[(r['camera_id'],r['date'])]['false_vacant']} for r in before])
predictions = json.loads((folder/'candidate_validation_predictions.json').read_text(encoding='utf-8'))
wrong_empty = [r for r in predictions if r['label']==1 and r['probability_occupied']<=.25]
table(wrong_empty[:10],['camera_id','date','slot_id','label','probability_occupied'])
print('Final-test images or labels read:', study['final_images_or_labels_read'])'''),
        markdown('''## Explain it in your own words

1. Why must photos from one date stay together?
2. Why is an unknown label different from an empty space?
3. Could the candidate make fewer total mistakes but give more wrong “empty” directions?
4. If a check failed, why do we keep the original app model?
5. What fresh evidence would we need before claiming live camera accuracy?

No student answers or mastery are assumed. The Singapore feed measures aggregate availability, not the answers to these camera-photo questions. All previous failed experiments, checkpoints and raw source files remain preserved.''')]
    nbf.validate(notebook);nbf.write(notebook,path)
    print(path)


if __name__=='__main__':main()
