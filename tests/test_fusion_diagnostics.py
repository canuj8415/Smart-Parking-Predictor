import unittest
from smart_parking.fusion_diagnostics import state_from_probability,paired_fusion_metrics,fusion_gates


def row(slot,label,p,vehicle=None):
    state=state_from_probability(p)
    return dict(image='A',slot_id=slot,label=label,probability_occupied=p,
                vehicle_id=vehicle,classifier_state=state,
                fusion_state='uncertain' if state=='vacant' and vehicle is not None else state)


class FusionDiagnosticTests(unittest.TestCase):
    def test_review_tradeoff_has_explicit_denominators(self):
        m=paired_fusion_metrics([row('1',1,.1,0),row('2',0,.1,1),row('3',0,.1),row('4',1,.9)])
        self.assertEqual(m['fusion']['confusion'],[[1,0,1],[0,1,1]])
        self.assertEqual(m['unsafe_vacancies_flagged'],1)
        self.assertEqual(m['correct_vacancies_sent_to_review'],1)
        self.assertEqual(m['fusion']['accuracy_on_decided'],1.)
        self.assertEqual(m['fusion']['correct_fraction_of_all'],.5)
        self.assertEqual(m['correct_vacancy_retention']['fraction'],.5)

    def test_all_review_does_not_get_accuracy_or_retention_credit(self):
        m=paired_fusion_metrics([row('1',1,.5),row('2',0,.5)])
        self.assertIsNone(m['fusion']['accuracy_on_decided'])
        self.assertIsNone(m['correct_vacancy_retention']['fraction'])
        self.assertEqual(m['fusion']['correct_fraction_of_all'],0)
        self.assertFalse(all(fusion_gates(m,dict(occupied_false_vacancy_max=.01,uncertainty_max=.1,correct_vacancy_retention_min=.95,image_correct_vacancy_retention_min=.9)).values()))

    def test_inclusive_endpoints(self):
        self.assertEqual(state_from_probability(.25),'vacant')
        self.assertEqual(state_from_probability(.75),'occupied')

    def test_duplicate_and_unjustified_state_refused(self):
        a=row('1',0,.1)
        with self.assertRaises(ValueError):paired_fusion_metrics([a,a])
        bad=dict(a,fusion_state='occupied')
        with self.assertRaises(ValueError):paired_fusion_metrics([bad])

    def test_bad_probability_and_truth_refused(self):
        for p in [float('nan'),float('inf'),-.1,1.1]:
            with self.assertRaises(ValueError):state_from_probability(p)
        with self.assertRaises(ValueError):paired_fusion_metrics([row('1',2,.1)])
