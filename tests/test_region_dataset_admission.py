import unittest
from smart_parking.region_dataset_admission import qualify_hashes,select_frames

def frame(member,group,role='train'):return dict(image_member=member,group_id=group,role=role)
def record(member,group,sha):return dict(member=member,group_id=group,sha256=sha)

class RegionDatasetAdmissionTests(unittest.TestCase):
    def test_closed_alias_protects_entire_training_group(self):
        rows=[record('a','T','shared'),record('b','F','shared'),record('c','T','other')]
        q=qualify_hashes(rows,[frame('c','T')],{'T':'training_exposed','F':'consumed_durable_final'})
        self.assertFalse(q['accepted']);self.assertEqual(len(q['rejected']),1)

    def test_development_alias_excludes_training_not_development(self):
        rows=[record('a','T','same'),record('b','V','same')]
        q=qualify_hashes(rows,[frame('a','T'),frame('b','V','development')],{'T':'training_exposed','V':'development_exposed'})
        self.assertEqual([f['role'] for f in q['accepted']],['development'])

    def test_unknown_member_alias_and_transitive_closure(self):
        rows=[record('a','T','x'),record('b','Q','x'),record('c','Q','y'),record('d','U','y')]
        q=qualify_hashes(rows,[frame('a','T')],{'T':'training_exposed','Q':'training_exposed'})
        self.assertFalse(q['accepted'])

    def test_duplicate_selected_bytes_do_not_inflate_cohort(self):
        q=qualify_hashes([record('a','T','x'),record('b','T','x')],[frame('a','T'),frame('b','T')],{'T':'training_exposed'})
        self.assertEqual(len(q['accepted']),1);self.assertEqual(len(q['rejected']),1)

    def test_seeded_selection_uses_only_admitted_roles(self):
        groups=[dict(camera_id='c',capture_date='2012-01-01',status='training_exposed'),dict(camera_id='c',capture_date='2012-01-02',status='historical_metadata_excluded')]
        pairs=[dict(camera_id='c',capture_date=day,image_member=str(i)+day) for day in ['2012-01-01','2012-01-02'] for i in range(10)]
        a=select_frames(pairs,groups);self.assertEqual(a,select_frames(pairs,groups));self.assertEqual(len(a),4);self.assertTrue(all(f['role']=='train' for f in a))
