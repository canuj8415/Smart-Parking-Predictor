"""Synthetic whole-sequence isolation fixtures; not detector accuracy runs."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.sequence_holdouts import evaluate_sequence_once,assert_sequence_closed


class SequenceHoldoutTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).resolve().parents[1]/'.cache/test_tmp'
        base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base)
        self.root=Path(self.temp.name)
        self.claims=self.root/'claims'
        self.parent=self.root/'parent.json'
        self.manifest=self.root/'reserved.json'
        self.protocol=self.root/'protocol.json'
        self.selection=self.root/'selection.json'
        self.protocol.write_text('{}')
        (self.root/'model.bin').write_bytes(b'synthetic checkpoint fixture')
        (self.root/'implementation.py').write_text('# synthetic fixture')
        self.collection='https://example.invalid/licensed-collection-v1.zip'
        self.rows=[dict(sequence='fixture',role='reserved_final',frame_index=i,
            image=f'frames/{i}.jpg',annotation=f'labels/{i}.png',image_sha256=hashlib.sha256(f'image{i}'.encode()).hexdigest(),
            annotation_sha256=hashlib.sha256(f'mask{i}'.encode()).hexdigest()) for i in range(3)]
        self.save_manifests()
        self.chosen=dict(counting_final_qualified=True,metrics=dict(reference_events=1),
            collection_identity=self.collection,protocol_sha256=self.sha(self.protocol),
            source_hashes={'implementation.py':self.sha(self.root/'implementation.py')},
            checkpoint_hashes={'model.bin':self.sha(self.root/'model.bin')})
        self.save_selection()

    def tearDown(self):
        self.temp.cleanup()

    def sha(self,path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def save_selection(self):
        self.selection.write_text(json.dumps(self.chosen))

    def save_manifests(self,source_id='SYNTHETIC-SOURCE'):
        self.parent.write_text(json.dumps(dict(source_id=source_id,frames=self.rows)))
        self.manifest.write_text(json.dumps(dict(source_id=source_id,reserved_sequences=['fixture'],
            frames=self.rows,parent_manifest_sha256=self.sha(self.parent))))

    def call(self,callback):
        return evaluate_sequence_once(self.manifest,self.parent,self.selection,self.protocol,'synthetic-only',callback,
            collection_identity=self.collection,expected_manifest_sha256=self.sha(self.manifest),
            expected_selection_sha256=self.sha(self.selection),receipt_dir=self.claims,root=self.root)

    def test_claim_precedes_callback_and_failure_consumes_whole_sequence(self):
        def failure(rows):
            self.assertEqual(len(list(self.claims.glob('*.claim.json'))),1)
            self.assertEqual(len(rows),3)
            raise InterruptedError('simulated interruption')
        with self.assertRaises(InterruptedError):
            self.call(failure)
        with self.assertRaisesRegex(ValueError,'already started'):
            self.call(lambda _:self.fail('no re-evaluation'))

    def test_new_paths_and_source_id_do_not_reset_same_sequence(self):
        self.call(lambda _:None)
        for row in self.rows:
            row['image']='alternate/'+row['image']
            row['annotation']='alternate/'+row['annotation']
        self.save_manifests(source_id='ALIAS-SOURCE')
        with self.assertRaisesRegex(ValueError,'Whole source sequence'):
            self.call(lambda _:self.fail('whole sequence consumed'))

    def test_relabelled_sequence_with_same_assets_is_blocked(self):
        self.call(lambda _:None)
        for row in self.rows:row['sequence']='renamed'
        self.parent.write_text(json.dumps(dict(source_id='SYNTHETIC',frames=self.rows)))
        self.manifest.write_text(json.dumps(dict(source_id='SYNTHETIC',reserved_sequences=['renamed'],
            frames=self.rows,parent_manifest_sha256=self.sha(self.parent))))
        with self.assertRaisesRegex(ValueError,'assets overlap'):
            self.call(lambda _:self.fail('same content'))

    def test_incomplete_reservation_or_escaping_assets_are_rejected_without_callback(self):
        bad=json.loads(self.manifest.read_text());bad['frames']=bad['frames'][:2]
        self.manifest.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError,'complete parent'):
            self.call(lambda _:self.fail('incomplete reservation'))
        self.rows[0]['image']='../outside.jpg'
        self.save_manifests()
        with self.assertRaisesRegex(ValueError,'outside project'):
            self.call(lambda _:self.fail('unsafe path'))

    def test_unqualified_empty_reference_or_changed_protocol_and_weights_block_loader(self):
        for change in [dict(counting_final_qualified=False),dict(metrics=dict(reference_events=0))]:
            original=dict(self.chosen);self.chosen.update(change);self.save_selection()
            with self.assertRaisesRegex(ValueError,'positive-reference'):
                self.call(lambda _:self.fail('failed validation'))
            self.chosen=original
        self.save_selection();self.protocol.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError,'protocol checksum'):
            self.call(lambda _:self.fail('changed protocol'))
        self.protocol.write_text('{}');(self.root/'model.bin').write_bytes(b'changed weights')
        with self.assertRaisesRegex(ValueError,'checkpoint checksum'):
            self.call(lambda _:self.fail('changed checkpoint'))

    def test_stale_lock_fails_closed_and_reads_no_assets(self):
        self.claims.mkdir();(self.claims/'claim.lock').write_text('unresolved interrupted claim lock')
        with self.assertRaises(FileExistsError):
            self.call(lambda _:self.fail('locked'))
        self.assertTrue((self.claims/'claim.lock').exists())
        # The synthetic image/mask paths never existed: validation reads metadata only.
        self.assertEqual(len(assert_sequence_closed(self.manifest,self.parent,self.collection,receipt_dir=self.claims,root=self.root)),3)
