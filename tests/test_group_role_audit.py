import unittest
from smart_parking.group_role_audit import audit_groups


class GroupRoleAuditTests(unittest.TestCase):
    def test_claim_consumes_whole_group_even_with_failure_status(self):
        r=audit_groups([dict(camera_id='CAM',capture_date='2020-01-01')],[],[dict(run_id='FAILED',status='failed',source_groups=[['cam','2020-01-01']])])
        self.assertEqual(r['consumed_final'],1);self.assertEqual(r['groups'][0]['claim_runs'],['FAILED'])

    def test_relabelled_frame_cannot_free_development_group(self):
        r=audit_groups([dict(camera_id='cam',capture_date='2020-01-01')],[dict(camera_id='cam',date='2020-01-01',image='some-other-frame.jpg')],[])
        self.assertEqual(r['development_exposed'],1);self.assertEqual(r['newly_qualified_final_groups'],0)

    def test_unaccounted_metadata_does_not_grant_final_admission(self):
        r=audit_groups([dict(camera_id='cam',capture_date='2020-01-01')],[],[])
        self.assertEqual(r['not_accounted_for'],1);self.assertEqual(r['newly_qualified_final_groups'],0)

    def test_invalid_or_duplicate_groups_are_rejected(self):
        for rows in [[dict(camera_id='cam',capture_date='2020-02-30')],[dict(camera_id='cam',capture_date='2020-01-01')]*2]:
            with self.assertRaises(ValueError):audit_groups(rows,[],[])
