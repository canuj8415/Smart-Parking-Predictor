import unittest
from smart_parking.pklot_group_ledger import identity,member_identity,build_ledger

def pair(camera='pucpr',folder='parking2',day='2012-10-01'):
    stem=f'PKLot/PKLot/{folder}/sunny/{day}/{day}_10_00_00'
    return dict(camera_id=camera,capture_date=day,image_member=stem+'.jpg',annotation_member=stem+'.xml')
def exposure(day,role,sha=None):return dict(camera_id='PUCPR',date=day,role=role,source='fixture.json',image_sha256=sha)

class PKLotGroupLedgerTests(unittest.TestCase):
    def test_known_aliases_and_invalid_dates(self):
        self.assertEqual(identity(' Parking1A ','2012-12-24'),('ufpr04','2012-12-24'))
        self.assertEqual(member_identity(pair()['image_member']),('pucpr','2012-10-01'))
        for camera,day in [('unknown','2012-10-01'),('pucpr','2012-02-30')]:
            with self.assertRaises(ValueError):identity(camera,day)

    def test_missing_claim_does_not_reopen_historical_test(self):
        m=build_ledger([pair()],[exposure('2012-10-01','test'),exposure('2012-10-01','train')],[],[])
        self.assertEqual(m['groups'][0]['status'],'historical_test_protected')
        self.assertFalse(m['groups'][0]['byte_alias_to_protected'])
        self.assertEqual(m['protected_role_overlap_groups'],1)
        self.assertEqual(m['new_training_groups_admitted'],0)

    def test_failed_claim_overrides_reservation_and_training(self):
        claim=dict(run_id='failed-final',source_groups=[['parking2','2012-10-01']])
        m=build_ledger([pair()],[exposure('2012-10-01','train')],[claim],[])
        self.assertEqual(m['groups'][0]['status'],'consumed_durable_final')
        self.assertFalse(m['groups'][0]['new_final_admitted'])

    def test_cross_group_hash_alias_blocks_related_training(self):
        m=build_ledger([pair(),pair(day='2012-10-02'),pair(day='2012-10-03')],[exposure('2012-10-01','test','same'),exposure('2012-10-02','train','same'),exposure('2012-10-02','train','second'),exposure('2012-10-03','train','second')],[],[])
        self.assertEqual(m['groups'][1]['status'],'byte_alias_to_protected_quarantine')
        self.assertEqual(m['groups'][2]['status'],'byte_alias_to_protected_quarantine')
        self.assertEqual(len(m['known_cross_group_byte_aliases']),2)

    def test_unknown_metadata_and_member_duplicates_never_auto_admitted(self):
        m=build_ledger([pair()],[],[],[dict(path='configs/layouts/example.json',excluded_dates=['2012-10-01'])])
        self.assertEqual(m['groups'][0]['status'],'historical_metadata_excluded')
        self.assertFalse(m['groups'][0]['new_final_admitted'])
        with self.assertRaises(ValueError):build_ledger([pair(),pair()],[],[],[])
        with self.assertRaises(ValueError):member_identity('../'+pair()['image_member'])
