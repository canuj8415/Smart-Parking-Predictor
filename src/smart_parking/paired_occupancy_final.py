"""Bind a paired final protocol before the existing durable whole-date claim."""
import json
import math
import os
from pathlib import Path
from .provenance import ROOT,digest
from .holdouts import evaluate_final_once


def _path(root,value):
    path=(Path(root)/value).resolve()
    if not path.is_relative_to(Path(root).resolve()):raise ValueError('Binding outside project')
    return path


def evaluate_paired_once(manifest,selection,protocol,run_id,evaluate,*,root=ROOT,receipt_dir=None):
    """Validate BOTH models, code, settings and passed development cards first.

    The protocol receipt is fsynced before evaluate_final_once claims the groups.
    Its callback cannot run before the original overlap-aware claim is durable.
    Failed callbacks remain consumed; no release or repeat path exists here.
    """
    protocol=Path(protocol);selection=Path(selection);manifest=Path(manifest)
    spec=json.loads(protocol.read_text(encoding='utf-8'))
    chosen=json.loads(selection.read_text(encoding='utf-8'))
    if spec.get('version')!='occupancy-paired-final-v1':raise ValueError('Unsupported paired protocol')
    if digest(protocol)!=chosen.get('protocol_sha256'):raise ValueError('Paired protocol changed')
    if digest(manifest)!=spec['manifest_sha256']:raise ValueError('Reservation changed')
    if chosen.get('validation_gate_passed') is not True:raise ValueError('Development selection failed')
    if set(spec['models'])!={'original','candidate'}:raise ValueError('Both checkpoint roles required')
    for binding in spec['models'].values():
        if digest(_path(root,binding['path']))!=binding['sha256']:raise ValueError('Paired checkpoint changed')
    for path,expected in {**spec['source_hashes'],**spec['detector_weight_hashes']}.items():
        if digest(_path(root,path))!=expected:raise ValueError('Frozen code/detector changed')
    if set(spec['development_cards'])!={'classifier','fusion'}:raise ValueError('Both development gates required')
    for binding in spec['development_cards'].values():
        path=_path(root,binding['path'])
        if digest(path)!=binding['sha256']:raise ValueError('Development evidence changed')
        card=json.loads(path.read_text(encoding='utf-8'))
        if card.get('validation_gate_passed') is not True:raise ValueError('Unqualified development evidence')
        if card['candidate_checkpoint_sha256']!=spec['models']['candidate']['sha256']:
            raise ValueError('Development evidence belongs to another candidate')
    if chosen['checkpoint_sha256']!=spec['models']['candidate']['sha256']:
        raise ValueError('Selected candidate does not match paired protocol')
    directory=Path(receipt_dir or ROOT/'data/holdout_claims');directory.mkdir(parents=True,exist_ok=True)
    binding_path=directory/(digest(protocol)+'.paired_protocol.json')
    binding=dict(run_id=run_id,protocol_sha256=digest(protocol),protocol=spec,
        selection_sha256=digest(selection),note='All paired bindings verified before the durable whole-date final claim')
    with binding_path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(binding,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    return evaluate_final_once(manifest,selection,_path(root,spec['models']['candidate']['path']),run_id,evaluate,
        expected_manifest_sha256=spec['manifest_sha256'],receipt_dir=directory,root=root)


def score(rows):
    n=len(rows)
    if not n:return dict(samples=0,occupied_labels=0,vacant_labels=0,hard_accuracy=None,hard_errors=0,
        false_vacant=0,false_occupied=0,correct_vacant=0,vacant_predictions=0,uncertain=0,
        uncertain_fraction=None,correct_decisions=0,decision_coverage=None,vacancy_precision=None,vacancy_recall=None)
    occupied=sum(r['label']==1 for r in rows);empty=[r for r in rows if r['state']=='vacant']
    wrong_empty=sum(r['label']==1 for r in empty)
    wrong_occupied=sum(r['label']==0 and r['state']=='occupied' for r in rows)
    uncertain=sum(r['state']=='uncertain' for r in rows)
    errors=sum(int(r['occupancy_score']>=.5)!=r['label'] for r in rows)
    correct_empty=len(empty)-wrong_empty
    return dict(samples=n,occupied_labels=occupied,vacant_labels=n-occupied,hard_accuracy=1-errors/n,hard_errors=errors,
        false_vacant=wrong_empty,false_occupied=wrong_occupied,correct_vacant=correct_empty,
        vacant_predictions=len(empty),uncertain=uncertain,uncertain_fraction=uncertain/n,
        correct_decisions=n-uncertain-wrong_empty-wrong_occupied,decision_coverage=(n-uncertain)/n,
        vacancy_precision=correct_empty/len(empty) if empty else None,
        vacancy_recall=correct_empty/(n-occupied) if n>occupied else None)


def acceptance(original,candidate,original_groups,candidate_groups,gates):
    """Prespecified scalar thresholds; unknown labels never enter these rows."""
    n=candidate['samples']
    keys=set(original_groups)
    support=n>=gates['minimum_labels'] and len(keys)==gates['minimum_groups'] and keys==set(candidate_groups)
    support=support and candidate['occupied_labels']>=gates['minimum_each_class'] and candidate['vacant_labels']>=gates['minimum_each_class']
    support=support and all(candidate_groups[k]['samples']>=gates['minimum_group_labels'] for k in keys)
    if not support:return dict(sufficient_support=False,all_other_gates_evaluable=False),False
    pairs=[(original_groups[k],candidate_groups[k]) for k in keys]
    checks=dict(sufficient_support=True,
        classifier_accuracy=candidate['hard_accuracy']>=gates['accuracy_min'] and candidate['hard_accuracy']>=original['hard_accuracy']-gates['accuracy_drop_max'],
        classifier_group_accuracy=all(b['hard_accuracy']>=gates['group_accuracy_min'] and b['hard_accuracy']>=a['hard_accuracy']-gates['group_accuracy_drop_max'] for a,b in pairs),
        no_false_vacant_regression=candidate['false_vacant']<=original['false_vacant'] and all(b['false_vacant']<=a['false_vacant'] for a,b in pairs),
        bounded_false_occupied=candidate['false_occupied']<=original['false_occupied']+math.floor(gates['wrong_occupied_extra_fraction']*n)
            and all(b['false_occupied']<=a['false_occupied']+math.floor(gates['wrong_occupied_extra_fraction']*b['samples']) for a,b in pairs),
        retain_correct_vacancies=candidate['correct_vacant']>=math.ceil(gates['vacancy_retention']*original['correct_vacant'])
            and all(b['correct_vacant']>=math.ceil(gates['vacancy_retention']*a['correct_vacant']) for a,b in pairs),
        review_burden=candidate['uncertain_fraction']<=gates['uncertain_max'] and candidate['uncertain_fraction']<=original['uncertain_fraction']+gates['uncertain_extra_max']
            and all(b['uncertain_fraction']<=gates['group_uncertain_max'] for a,b in pairs),
        correct_decisions_noninferior=candidate['correct_decisions']>=original['correct_decisions']
            and all(b['correct_decisions']>=a['correct_decisions']-math.floor(gates['group_correct_drop_fraction']*b['samples']) for a,b in pairs),
        some_strict_benefit=candidate['false_vacant']<original['false_vacant'] or candidate['false_occupied']<original['false_occupied'] or candidate['correct_vacant']>original['correct_vacant'])
    return checks,all(checks.values())
