"""Synthetic claim fixtures verify isolation, not final model accuracy."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.holdouts import evaluate_final_once,assert_holdout_closed

class HoldoutTests(unittest.TestCase):
    def setUp(self):
        folder=Path(__file__).resolve().parents[1]/'.cache/test_tmp';folder.mkdir(parents=True,exist_ok=True)
        self.temporary=tempfile.TemporaryDirectory(dir=folder);self.root=Path(self.temporary.name);self.claims=self.root/'claims'
        self.checkpoint=self.root/'checkpoint.bin';self.checkpoint.write_bytes(b'software fixture, not model weights')
        self.selection=self.root/'selection.json';self.selection.write_text(json.dumps(dict(validation_gate_passed=True,checkpoint_sha256=hashlib.sha256(self.checkpoint.read_bytes()).hexdigest())))
    def tearDown(self):self.temporary.cleanup()
    def manifest(self,name,frames):
        p=self.root/name;p.write_text(json.dumps(dict(frames=[dict(image=f,annotation='never-opened.xml',camera_id='SYNTHETIC',date='2020-01-01') for f in frames])))
        return p
    def call(self,manifest,callback):
        return evaluate_final_once(manifest,self.selection,self.checkpoint,'synthetic-fixture',callback,expected_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),receipt_dir=self.claims,root=self.root)
    def test_claim_exists_before_callback_and_failure_still_consumes_exam(self):
        m=self.manifest('first.json',['images/a.jpg','images/b.jpg'])
        def interrupted(rows):
            self.assertEqual(len(list(self.claims.glob('*.claim.json'))),1)
            self.assertEqual(len(rows),2);raise RuntimeError('simulated interruption')
        with self.assertRaisesRegex(RuntimeError,'simulated interruption'):self.call(m,interrupted)
        with self.assertRaisesRegex(ValueError,'already started'):self.call(m,lambda rows:self.fail('must not read exam again'))
    def test_overlap_is_rejected_even_for_different_manifest_and_subset(self):
        a=self.manifest('one.json',['images/a.jpg','images/b.jpg']);self.call(a,lambda rows:42)
        b=self.manifest('different.json',['images/b.jpg','images/c.jpg'])
        with self.assertRaisesRegex(ValueError,'overlaps'):assert_holdout_closed(b,self.claims,self.root)
    def test_failed_gate_or_changed_weights_cannot_call_loader(self):
        m=self.manifest('exam.json',['images/a.jpg']);self.selection.write_text(json.dumps(dict(validation_gate_passed=False,checkpoint_sha256=hashlib.sha256(self.checkpoint.read_bytes()).hexdigest())))
        with self.assertRaisesRegex(ValueError,'passed frozen'):self.call(m,lambda rows:self.fail('gate must block'))
        self.selection.write_text(json.dumps(dict(validation_gate_passed=True,checkpoint_sha256='wrong')))
        with self.assertRaisesRegex(ValueError,'checkpoint checksum'):self.call(m,lambda rows:self.fail('hash must block'))
    def test_changed_reservation_and_duplicate_or_escaping_frames_are_rejected(self):
        m=self.manifest('exam.json',['images/a.jpg'])
        with self.assertRaisesRegex(ValueError,'reservation checksum'):evaluate_final_once(m,self.selection,self.checkpoint,'fixture',lambda rows:None,expected_manifest_sha256='wrong',receipt_dir=self.claims,root=self.root)
        for frames in [['images/a.jpg','images/a.jpg'],['../outside.jpg']]:
            bad=self.manifest('bad.json',frames)
            with self.assertRaises(ValueError):assert_holdout_closed(bad,self.claims,self.root)
    def test_different_frames_on_same_camera_date_cannot_be_reused_as_fresh(self):
        a=self.manifest('one.json',['images/a.jpg']);self.call(a,lambda _:None)
        b=self.manifest('other.json',['images/completely-different.jpg'])
        with self.assertRaisesRegex(ValueError,'camera/date overlaps'):assert_holdout_closed(b,self.claims,self.root)
        rows=json.loads(b.read_text());rows['frames'][0]['date']='2020-01-02';b.write_text(json.dumps(rows))
        self.assertEqual(len(assert_holdout_closed(b,self.claims,self.root)),1)
    def test_missing_camera_date_metadata_is_rejected(self):
        p=self.root/'missing.json';p.write_text(json.dumps(dict(frames=[dict(image='images/a.jpg')])) )
        with self.assertRaises(ValueError):assert_holdout_closed(p,self.claims,self.root)

if __name__=='__main__':unittest.main()
