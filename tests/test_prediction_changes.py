"""Synthetic paired predictions only;not actual parking observations."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.prediction_changes import paired_changes
class PredictionChangesTests(unittest.TestCase):
    def rows(self):return [dict(image_sha256='fixture',slot_id=str(i),label=y,probability_occupied=p) for i,(y,p) in enumerate([(1,.9),(0,.8),(1,.25),(0,.25)])]
    def test_pairs_match_identity_not_position_and_reconcile(self):
        before=self.rows();after=[dict(r) for r in before];after[0]['probability_occupied']=.1;after[1]['probability_occupied']=.1
        rows,s=paired_changes(before,list(reversed(after)));self.assertEqual((s['regressed'],s['corrected']),(1,1));self.assertEqual(s['new_false_vacant'],1)
    def test_confidence_endpoints_and_forced_threshold_are_explicit(self):
        rows,s=paired_changes(self.rows(),self.rows());self.assertTrue(rows[2]['false_vacant_before']);self.assertFalse(rows[2]['review_before']);self.assertTrue(rows[3]['correct_confident_vacant_before'])
        one=[dict(self.rows()[0],probability_occupied=.5)];self.assertFalse(paired_changes(one,one)[0][0]['hard_error_before'])
    def test_missing_duplicate_or_changed_target_rejected(self):
        rows=self.rows()
        for other in [rows[:-1],rows+[rows[0]],[dict(r,label=1-r['label']) for r in rows]]:
            with self.assertRaises(ValueError):paired_changes(rows,other)
    def test_invalid_probability_unknown_label_and_empty_cohort_rejected(self):
        for value in [float('nan'),-0.1,1.1]:
            with self.assertRaises(ValueError):paired_changes([dict(self.rows()[0],probability_occupied=value)],self.rows()[:1])
        with self.assertRaises(ValueError):paired_changes([],[])
        with self.assertRaises(ValueError):paired_changes([dict(self.rows()[0],label=None)],self.rows()[:1])
if __name__=='__main__':unittest.main()
