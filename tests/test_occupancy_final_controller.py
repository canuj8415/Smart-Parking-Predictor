"""Synthetic controller checks; no real dataset pixels or learned model scoring."""
import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image

PROJECT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(PROJECT/'src'))
from smart_parking.provenance import digest
from smart_parking.paired_occupancy_final import evaluate_paired_once


class FixtureClassifier:
    def load_state_dict(self,state):self.role=state['fixture_role']
    def eval(self):return self


class FixtureEngine:
    def __init__(self,**kwargs):self.classifier=FixtureClassifier()
    def analyze(self,image,geometry,**kwargs):
        rows=[]
        assert all('ground_truth_occupied' not in s for s in geometry['slots'])
        for s in geometry['slots']:
            occupied=int(s['id'])%2==1
            # Known synthetic error, independent of any real camera/model.
            if self.classifier.role=='original' and s['id']=='0':occupied=True
            rows.append(dict(slot_id=s['id'],state='occupied' if occupied else 'vacant',
                occupancy_score=.99 if occupied else .01,vehicle_id=None,slot_overlap=0))
        return dict(detections=[],slots=rows,counts={k:sum(r['state']==k for r in rows) for k in ['occupied','vacant','uncertain']}),image


class FinalControllerFixtureTests(unittest.TestCase):
    def case(self,unknown):
        base=PROJECT/'outputs/test_fixtures';base.mkdir(parents=True,exist_ok=True)
        temporary=tempfile.TemporaryDirectory(dir=base);root=Path(temporary.name)
        try:
            spec=importlib.util.spec_from_file_location('fixture_final_controller',PROJECT/'scripts/evaluate_occupancy_expansion_final.py')
            controller=importlib.util.module_from_spec(spec);spec.loader.exec_module(controller)
            def save(relative,value):
                p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8');return p
            frames=[]
            for i in range(6):
                camera='fixture'+str(i//2);day=f'2013-01-0{i//2+1}'
                image=root/f'fixture/{i}.jpg';image.parent.mkdir(exist_ok=True);Image.new('RGB',(100,30),'gray').save(image)
                annotation=image.with_suffix('.xml');spaces=[]
                for slot in range(20):
                    x=slot*5;label='' if unknown else f' occupied="{slot%2}"'
                    spaces.append(f'<space id="{slot}"{label}><contour><point x="{x}" y="0"/><point x="{x+3}" y="0"/><point x="{x+3}" y="20"/><point x="{x}" y="20"/></contour></space>')
                annotation.write_text(f'<parking id="{camera}">'+''.join(spaces)+'</parking>',encoding='utf-8')
                frames.append(dict(camera_id=camera,date=day,image=image.relative_to(root).as_posix(),annotation=annotation.relative_to(root).as_posix(),image_sha256=digest(image),annotation_sha256=digest(annotation)))
            manifest=save('manifest.json',dict(frames=frames))
            rid='OCCUPANCY-PAIRED-FINAL-SYNTHETIC';folder=root/'experiments/results'/rid;folder.mkdir(parents=True)
            models={}
            for name in ['original','candidate']:
                p=root/(name+'.pt');p.write_bytes(name.encode());models[name]=dict(path=p.name,sha256=digest(p))
            cards={}
            for name in ['classifier','fusion']:
                p=save(name+'.json',dict(validation_gate_passed=True,candidate_checkpoint_sha256=models['candidate']['sha256']))
                cards[name]=dict(path=p.name,sha256=digest(p))
            source=root/'scripts/evaluate_occupancy_expansion_final.py';source.parent.mkdir();source.write_bytes((PROJECT/'scripts/evaluate_occupancy_expansion_final.py').read_bytes())
            protocol=dict(version='occupancy-paired-final-v1',run_id=rid,source_ids=['SYNTHETIC-FIXTURE'],seed=1,
                source_hashes={source.relative_to(root).as_posix():digest(source)},detector_weight_hashes={},models=models,development_cards=cards,
                manifest='manifest.json',manifest_sha256=digest(manifest),detectors=['fasterrcnn','maskrcnn'],resolution=640,
                detection_confidence=.5,uncertain_low=.25,uncertain_high=.75,
                gates=dict(minimum_labels=120,minimum_groups=3,minimum_group_labels=20,minimum_each_class=10,
                    accuracy_min=.95,accuracy_drop_max=.005,group_accuracy_min=.9,group_accuracy_drop_max=.025,
                    wrong_occupied_extra_fraction=.01,vacancy_retention=.95,uncertain_max=.1,uncertain_extra_max=.02,
                    group_uncertain_max=.15,group_correct_drop_fraction=.025))
            p=save(f'experiments/results/{rid}/protocol.json',protocol)
            save(f'experiments/results/{rid}/selection.json',dict(validation_gate_passed=True,checkpoint_sha256=models['candidate']['sha256'],protocol_sha256=digest(p)))
            save('data/automation_state.json',dict(active_training_jobs=[],active_validation_jobs=[],completed_run_ids=[],completed_recorded_runs_since_schedule=0))
            registry=root/'experiments/EXPERIMENT_REGISTRY.csv'
            registry.write_text('experiment_id,run_type,evaluation_metrics\n',encoding='utf-8')
            def git(args,**kwargs):
                if args[1]=='rev-parse':return SimpleNamespace(stdout='synthetic-frozen-revision\n')
                return SimpleNamespace(stdout=(root/args[2].removeprefix('HEAD:')).read_bytes())
            def pair(*args,**kwargs):
                # Explicit test-local receipt directory; never the real claims.
                return evaluate_paired_once(*args,**kwargs,receipt_dir=root/'data/holdout_claims')
            import torch
            import smart_parking.vision as vision
            with patch.object(controller,'ROOT',root),patch.object(controller.subprocess,'run',side_effect=git),\
                 patch.object(controller,'evaluate_paired_once',side_effect=pair),\
                 patch.object(torch,'load',side_effect=lambda path,**kw:dict(state_dict=dict(fixture_role=Path(path).stem),run_id='fixture-only')),\
                 patch.object(vision,'VisionEngine',FixtureEngine),contextlib.redirect_stdout(io.StringIO()):
                controller.run(rid)
            result=json.loads((folder/'run.json').read_text())
            self.assertEqual(result['paired_final_gate_passed'],not unknown)
            self.assertEqual(result['all_final_groups_now_consumed'],True)
            self.assertEqual(len(list((root/'data/holdout_claims').glob('*.claim.json'))),1)
            self.assertEqual(json.loads((root/'data/automation_state.json').read_text())['completed_recorded_runs_since_schedule'],1)
            if unknown:
                self.assertEqual(result['detectors']['fasterrcnn']['overall']['candidate']['samples'],0)
                self.assertIsNone(result['detectors']['fasterrcnn']['overall']['candidate']['hard_accuracy'])
        finally:
            self.assertTrue(root.resolve().is_relative_to(base.resolve()));temporary.cleanup()

    def test_full_controller_synthetic_paired_scoring_and_registry(self):self.case(False)
    def test_full_controller_unknown_answers_fail_without_fabricated_accuracy(self):self.case(True)
