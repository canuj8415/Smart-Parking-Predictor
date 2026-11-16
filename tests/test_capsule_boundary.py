import hashlib,json,stat,sys,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from capsule_lesson_guard import path_decision
from capsule_payload import MANIFEST,verify_payload,create_zip,extract_checked,safe_names,digest


class CapsuleBoundaryTests(unittest.TestCase):
    def test_original_project_is_blocked_but_capsule_scratch_and_external_runtime_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder)/'project';root=project/'outputs/capsule';scratch=project/'outputs/private'
            self.assertIsNone(path_decision(root/'data/manifests/lesson.json',False,root,scratch,project))
            self.assertIsNone(path_decision(scratch/'history.sqlite',True,root,scratch,project))
            self.assertIsNotNone(path_decision(project/'docs/progress.md',False,root,scratch,project))
            self.assertIsNotNone(path_decision(root/'../outside.txt',False,root,scratch,project))
            self.assertIsNone(path_decision(Path(folder)/'external_python/site.py',False,root,scratch,project))

    def test_capsule_raw_weights_and_project_writes_are_denied(self):
        root=Path.cwd()/'fixture_capsule';scratch=Path.cwd()/'fixture_scratch'
        for name in ['data/raw/x.json','data/processed/targets.jsonl','models/checkpoints/x.pt','experiments/results/SG-FINAL-real/run.json']:
            self.assertIsNotNone(path_decision(root/name,False,root,scratch))
        self.assertIsNotNone(path_decision(root/'notebooks/lesson.ipynb',True,root,scratch))

    def fixture(self,parent):
        root=Path(parent)/'payload';root.mkdir();(root/'lesson.txt').write_bytes(b'archived teaching fixture')
        body=dict(files={'lesson.txt':dict(sha256=digest(root/'lesson.txt'),bytes=(root/'lesson.txt').stat().st_size)})
        (root/MANIFEST).write_text(json.dumps(body));return root

    def test_manifest_detects_corruption_missing_and_extra_members(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);verify_payload(root)
            (root/'lesson.txt').write_bytes(b'changed')
            with self.assertRaises(ValueError):verify_payload(root)
            (root/'extra.txt').write_bytes(b'extra')
            with self.assertRaises(ValueError):verify_payload(root)
            manifest=json.loads((root/MANIFEST).read_text());manifest['files']['missing.txt']=manifest['files']['lesson.txt'];(root/MANIFEST).write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):verify_payload(root)

    def test_unsafe_duplicate_and_private_member_names_fail_closed(self):
        for names in [['.'],['../x'],['/x'],['C:/x'],['a\\b'],['A.txt','a.txt'],['data/raw/x.json'],['models/checkpoints/x.pt'],['runtime/key.json']]:
            with self.subTest(names=names),self.assertRaises(ValueError):safe_names(names)

    def test_exact_zip_roundtrip_and_manifest_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);archive=Path(folder)/'lesson.zip';create_zip(root,archive)
            result=extract_checked(archive,Path(folder)/'relocated',digest(root/MANIFEST));self.assertEqual(result['files'],1)
            self.assertEqual((Path(folder)/'relocated/lesson.txt').read_bytes(),(root/'lesson.txt').read_bytes())
            with self.assertRaises(ValueError):extract_checked(archive,Path(folder)/'wrong', '0'*64)

    def test_zip_traversal_and_symlink_are_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            for kind in ['traversal','symlink']:
                archive=Path(folder)/(kind+'.zip');target=Path(folder)/(kind+'_target')
                with zipfile.ZipFile(archive,'x') as out:
                    info=zipfile.ZipInfo('../escape.txt' if kind=='traversal' else 'link.txt')
                    if kind=='symlink':info.external_attr=(stat.S_IFLNK|0o777)<<16
                    out.writestr(info,b'outside')
                with self.assertRaises(ValueError):extract_checked(archive,target,'0'*64)
                self.assertFalse(target.exists())
