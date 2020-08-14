import unittest

from arg_mine.api import classify


class TestDocumentMetadata(unittest.TestCase):
    def setUp(self) -> None:
        self.url = "https://www.cnn.com/politics/foo/bar.html"
        self.doc_id = "f285e6a93ee7d536f8b701739704fcec"
        # metadata output dict from API reply
        self.metadata_dict = {
            "computeAttention": True,
            "language": "en",
            "modelVersion": 0.1,
            "predictStance": True,
            "removeDuplicates": True,
            "showOnlyArguments": False,
            "sortBy": "argumentConfidence",
            "timeArgumentPrediction": 0.44077515602111816,
            "timeAttentionComputation": -1,
            "timeLogging": 0.1060018539428711,
            "timePreprocessing": 3.24249267578125e-05,
            "timeStancePrediction": -1,
            "timeTotal": 1.1884894371032715,
            "topic": "climate change",
            "totalArguments": 5,
            "totalClassifiedSentences": 37,
            "totalContraArguments": 3,
            "totalNonArguments": 32,
            "totalProArguments": 2,
            "userMetadata": self.url,
        }

    def test_from_dict(self):
        meta_out = classify.DocumentMetadata.from_dict(self.metadata_dict)
        self.assertIsInstance(meta_out, classify.DocumentMetadata)
        self.assertEqual(meta_out.url, self.url)
        # check that the document id is the same as what we expect
        self.assertEqual(meta_out.doc_id, self.doc_id)


class TestClassifiedSentence(unittest.TestCase):
    def setUp(self) -> None:
        self.url = "https://www.cnn.com/politics/foo/bar.html"
        self.doc_id = "f285e6a93ee7d536f8b701739704fcec"
        self.topic = "climate change"

        self.sentence_dict_contra = {
            "argumentConfidence": 0.8321625888347626,
            "argumentLabel": "argument",
            "sentenceOriginal": "Mr Zimmerman said climate change clearly underlined the bushfires being experienced this summer.",
            "sentencePreprocessed": "Mr Zimmerman said climate change clearly underlined the bushfires being experienced this summer.",
            "sortConfidence": 0.8809053269273679,
            "stanceConfidence": 0.9296480650199731,
            "stanceLabel": "contra",
        }

        self.sentence_dict_noarg = {
            "argumentConfidence": 0.03175872564315796,
            "argumentLabel": "no argument",
            "sentenceOriginal": '"And we are in for longer, hotter, drier summers.',
            "sentencePreprocessed": '"And we are in for longer, hotter, drier summers.',
            "sortConfidence": 0.03175872564315796,
        }

    def test_from_dict(self):
        sentence_out = classify.ClassifiedSentence.from_dict(
            self.url, self.topic, self.sentence_dict_contra
        )
        self.assertIsInstance(sentence_out, classify.ClassifiedSentence)
        self.assertEqual(sentence_out.url, self.url)
        # check that the document id is the same as what we expect
        self.assertEqual(sentence_out.doc_id, self.doc_id)
        self.assertEqual(sentence_out.stance_label, classify.StanceLabel.CON)
        self.assertEqual(sentence_out.argument_label, classify.ArgumentLabel.ARGUMENT)
        self.assertEqual(sentence_out.is_argument, True)

    # TODO: add sentence with no argument and with no stance
    def test_no_arg(self):
        sentence_out = classify.ClassifiedSentence.from_dict(
            self.url, self.topic, self.sentence_dict_noarg
        )
        self.assertIsInstance(sentence_out, classify.ClassifiedSentence)
        self.assertEqual(sentence_out.url, self.url)
        # check that the document id is the same as what we expect
        self.assertEqual(sentence_out.doc_id, self.doc_id)
        self.assertEqual(sentence_out.stance_label, classify.StanceLabel.NA)
        self.assertEqual(
            sentence_out.argument_label, classify.ArgumentLabel.NO_ARGUMENT
        )
        self.assertEqual(sentence_out.is_argument, False)


if __name__ == "__main__":
    unittest.main()
