"""Test code used to extract various topics"""
import unittest

import papers_diagnosis
import papers_epidemiology
import papers_prevention
import papers_transmission
import papers_treatment
import papers_vaccine

from utils.topic_extraction_utils import *


class TestTopicExtraction(unittest.TestCase):
    """Test code used to extract various topics"""

    def _test_category(self, module):
        """Test the given module"""
        df = module.get_papers()
        self.assertGreater(len(df), 0)
        sample_sentences = get_sample_sentences(df.iloc[0:1], module.RE_TOPIC)
        self.assertGreater(len(sample_sentences[0]), 0)

    def test_diagnosis_papers(self):
        """Test getting diagnosis papers"""
        self._test_category(papers_diagnosis)

    def test_epidemiology_papers(self):
        """Test getting epidemiology papers"""
        self._test_category(papers_epidemiology)

    def test_prevention_papers(self):
        """Test getting prevention papers"""
        self._test_category(papers_prevention)

    def test_transmission_papers(self):
        """Test getting transmission papers"""
        self._test_category(papers_transmission)

    def test_treatment_papers(self):
        """Test getting treatment papers"""
        self._test_category(papers_treatment)

    def test_vaccine_papers(self):
        """Test getting vaccine papers"""
        self._test_category(papers_vaccine)


if __name__ == "__main__":
    unittest.main()
