import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.provenance import digest
from smart_parking.paired_occupancy_final import evaluate_paired_once,score,acceptance
from smart_parking.holdouts import assert_holdout_closed


class PairedFinalTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(__file__).resolve().parents[1]/'outputs/test_fixtures';self.base.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=self.base);self.root=Path(self.tmp.name)
        self.claims=self.root/'claims'
        for name in ['old.pt','new.pt','controller.py','detector.pt']:(self.root/name).write_bytes(name.encode())
        frames=[dict(camera_id=f'camera{i//2}',date=f'2013-01-0{i//2+1}',image=f'frames/{i}.jpg') for i in range(6)]
        self.manifest=self.save('manifest.json',dict(frames=frames))
        h=digest(self.root/'new.pt')
        self.cards={k:self.save(k+'.json',dict(validation_gate_passed=True,candidate_checkpoint_sha256=h)) for k in ['classifier','fusion']}
        self.spec=dict(version='occupancy-paired-final-v1',manifest_sha256=digest(self.manifest),
            models={k:dict(path=p,sha256=digest(self.root/p)) for k,p in [('original','old.pt'),('candidate','new.pt')]},
            source_hashes={'controller.py':digest(self.root/'controller.py')},detector_weight_hashes={'detector.pt':digest(self.root/'detector.pt')},
            development_cards={k:dict(path=p.name,sha256=digest(p)) for k,p in self.cards.items()},thresholds=[.5,.25,.75])
        self.protocol=self.save('protocol.json',self.spec);self.select()

    def save(self,name,value):
        path=self.root/name;path.write_text(json.dumps(value),encoding='utf-8');return path

    def select(self):
        self.selection=self.save('selection.json',dict(validation_gate_passed=True,
            checkpoint_sha256=digest(self.root/'new.pt'),protocol_sha256=digest(self.protocol)))

    def run_pair(self,callback):
        return evaluate_paired_once(self.manifest,self.selection,self.protocol,'synthetic-paired-test',callback,root=self.root,receipt_dir=self.claims)

    def tearDown(self):
        self.assertTrue(self.root.resolve().is_relative_to(self.base.resolve()));self.tmp.cleanup()

    def test_binding_receipt_and_group_claim_exist_before_loader(self):
        def loader(rows):
            self.assertEqual(len(rows),6)
            self.assertEqual(len(list(self.claims.glob('*.paired_protocol.json'))),1)
            self.assertEqual(len(list(self.claims.glob('*.claim.json'))),1)
            return 'synthetic only'
        self.assertEqual(self.run_pair(loader),'synthetic only')
        with self.assertRaises(ValueError):assert_holdout_closed(self.manifest,self.claims,root=self.root)

    def test_failure_consumes_whole_group_even_under_new_frame_path(self):
        with self.assertRaises(RuntimeError):self.run_pair(lambda rows:(_ for _ in ()).throw(RuntimeError('fixture failure')))
        other=self.save('other.json',dict(frames=[dict(camera_id='camera0',date='2013-01-01',image='different/else.jpg')]))
        with self.assertRaises(ValueError):assert_holdout_closed(other,self.claims,root=self.root)

    def test_original_or_candidate_changes_block_loader(self):
        for name in ['old.pt','new.pt']:
            path=self.root/name;old=path.read_bytes();path.write_bytes(b'changed')
            with self.assertRaises(ValueError):self.run_pair(lambda rows:self.fail('No loader allowed'))
            path.write_bytes(old)
        self.assertFalse(list(self.claims.glob('*.claim.json')))

    def test_protocol_or_code_changes_block_loader(self):
        self.save('protocol.json',{**self.spec,'thresholds':[.6,.2,.8]})
        with self.assertRaises(ValueError):self.run_pair(lambda rows:self.fail('No loader allowed'))
        self.save('protocol.json',self.spec);self.select();(self.root/'controller.py').write_bytes(b'new implementation')
        with self.assertRaises(ValueError):self.run_pair(lambda rows:self.fail('No loader allowed'))

    def test_failed_or_foreign_development_card_blocks_loader(self):
        for patch in [dict(validation_gate_passed=False),dict(candidate_checkpoint_sha256='other')]:
            card=dict(validation_gate_passed=True,candidate_checkpoint_sha256=digest(self.root/'new.pt'),**{})
            card.update(patch);self.save('fusion.json',card)
            self.spec['development_cards']['fusion']['sha256']=digest(self.cards['fusion'])
            self.save('protocol.json',self.spec);self.select()
            with self.assertRaises(ValueError):self.run_pair(lambda rows:self.fail('No loader allowed'))

    def test_empty_ground_truth_does_not_create_perfect_accuracy(self):
        m=score([]);self.assertEqual(m['samples'],0);self.assertIsNone(m['hard_accuracy']);self.assertIsNone(m['vacancy_precision'])

    def test_vacancy_error_cannot_hide_behind_better_hard_accuracy(self):
        original=score([dict(label=int(i>=50),occupancy_score=.01 if i<50 else .99,state='vacant' if i<50 else 'occupied') for i in range(100)])
        candidate=dict(original,false_vacant=1,correct_vacant=51)
        gates=dict(minimum_labels=1,minimum_groups=1,minimum_each_class=1,minimum_group_labels=1,
            accuracy_min=.9,accuracy_drop_max=.01,group_accuracy_min=.9,group_accuracy_drop_max=.01,
            wrong_occupied_extra_fraction=.01,vacancy_retention=.95,uncertain_max=.1,uncertain_extra_max=.02,
            group_uncertain_max=.15,group_correct_drop_fraction=.025)
        checks,passed=acceptance(original,candidate,{'group':original},{'group':candidate},gates)
        self.assertFalse(checks['no_false_vacant_regression']);self.assertFalse(passed)
