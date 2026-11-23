"""Documented exclusions must not spill into TCP or turn warnings into exclusions."""
import unittest
from fc_pipeline_v2.cohort_policy import is_excluded, participant_decision


class CohortPolicyTests(unittest.TestCase):
    def test_exclusions_are_study_qualified(self):
        for number in ['103','104','107','202','210']:
            self.assertTrue(is_excluded('PCD'+number))
            self.assertFalse(is_excluded('TCP'+number))
            self.assertFalse(is_excluded(number))

    def test_noise_warnings_do_not_become_documented_exclusions(self):
        for participant in ['PCD119','PCD206','PCD218']:
            self.assertFalse(is_excluded(participant))
            self.assertTrue(participant_decision(participant)['quality_review_required'])
