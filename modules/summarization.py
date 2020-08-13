import nltk
import numpy as np
import os
import pickle
import re
import shutil
import torch
from transformers import AutoModel
from transformers import AutoConfig
from transformers import AutoTokenizer
from summarizer import Summarizer
import sklearn

# Config
from utils.constants import DATA_DIR
PATH_SCIBERT_MODEL = os.path.join(DATA_DIR, 'scibert_scivocab_uncased')

# for interaction with the main script
def discard_sentence(sentence):
    words = set(nltk.word_tokenize(sentence))
    boilerplate_sentence_words = ["license", "CC-BY-NC-ND", "medRxiv", "manuscript"]
    for word in boilerplate_sentence_words:
        if word in words:
            return True
    return False

re_citations1 = re.compile(r"\[[0-9, ]+\]")
re_citations2 = re.compile(r"\(?[a-zA-Z ]+ et al\.?\)?")
re_citations2b = re.compile(r"\(?[a-zA-Z ]+ et al\.,")
re_citations3 = re.compile(r"\([A-Za-z]+, [0-9]+(\)|;)")
re_citations4 = re.compile(r"\([A-Za-z]+ and [A-Za-z]+, [0-9]+(\)|;)")
re_figure = re.compile(r"\([Ff]igure [0-9A-Za-z]+\)")
re_table = re.compile(r"\([Tt]able [0-9A-Za-z]+\)")
re_period = re.compile(r"\s+\.")
re_space = re.compile(r"\s+")
def clean_text(text):
    text = re_citations1.sub("", text)
    text = re_citations2b.sub(".", text)    
    text = re_citations2.sub("", text)
    text = re_citations3.sub("", text)
    text = re_citations4.sub("", text)
    text = re_figure.sub("", text)
    text = re_table.sub("", text)
    text = re_period.sub(".", text)
    text = re_space.sub(" ", text)
    return text.strip()

def clean_summaries(df):
    """Clean summaries in the dataframe"""
    new_summaries = []
    for summary in df["scibert_summary_short"]:
        s = nltk.sent_tokenize(summary)
        new_summary = []
        for sentence in s:
            if not discard_sentence(sentence):
                new_summary.append(clean_text(sentence))
        new_summaries.append(" ".join(new_summary))
    df["scibert_summary_short_cleaned"] = new_summaries

    
def summarize_text(df):
    """Summarize the text in the dataframe. Uses cache where possible

    Fills in the gaps otherwise. 

    Performs this replacement in-place.

    """
    ID_TO_SUMMARY_PATH = "cord_uid_to_summaries_short.pkl"
    with open(os.path.join(DATA_DIR, ID_TO_SUMMARY_PATH), "rb") as f:
        cord_uid_to_summary = pickle.load(f)
    df["scibert_summary_short"] = df["cord_uid"].map(cord_uid_to_summary).fillna("")

    df_missing_summaries = df[df["scibert_summary_short"].str.len() == 0]
    num_missing_summaries = len(df_missing_summaries)

    if num_missing_summaries > 0:
        print(f"Found {num_missing_summaries} missing summaries")

        with open(os.path.join(DATA_DIR, "df_missing_summaries.pkl"), "wb") as f:
            pickle.dump(df_missing_summaries, f)
        # load model to fill in missing summaries
        model = BertSummarizer()

        def f(text):
            target_chars = 500
            if len(text) < 1000: # "papers" with fewer than 1000 characters are often mis-parses. There are 155 such papers.
                return "No summary available."
            if len(text) < target_chars:
                return text
            try:
                summary = model.summarize_text(text, ratio=target_chars/len(text), use_first=True)
                if len(summary) == 0:
                    return "No summary available."
                return summary
            except IndexError:
                return "No summary available."
        additional_summaries = df_missing_summaries.set_index("cord_uid")[
            "text"].apply(f)
        cord_uid_to_summary.update(additional_summaries)

        # backup old summary dictionary
        shutil.move(os.path.join(DATA_DIR, ID_TO_SUMMARY_PATH),
                    os.path.join(DATA_DIR, f"{ID_TO_SUMMARY_PATH}.bak"))

        # update summary dictionary
        with open(os.path.join(DATA_DIR, ID_TO_SUMMARY_PATH), "wb") as f:
            pickle.dump(cord_uid_to_summary, f)

        # sanity check - not always true because sometimes new papers get added
        # assert(len(cord_uid_to_summary) == len(df))

        # fill in missing summaries
        df["scibert_summary"] = df["cord_uid"].map(cord_uid_to_summary)


# Helpers

def create_frequency_table(text_string):

    # Removing stop words
    stop_words = set(nltk.corpus.stopwords.words("english"))

    words = nltk.tokenize.word_tokenize(text_string)

    # Reducing words to their root form
    stem = nltk.stem.PorterStemmer()

    # Creating dictionary for the word frequency table
    frequency_table = dict()
    for wd in words:
        wd = stem.stem(wd)
        if wd in stop_words:
            continue
        if wd in frequency_table:
            frequency_table[wd] += 1
        else:
            frequency_table[wd] = 1

    return frequency_table


def calculate_sentence_scores(text_string, frequency_table):

    # Break text into sentences
    sentences = nltk.tokenize.sent_tokenize(text_string)

    # Algorithm for scoring a sentence by its words
    sentence_scores = dict()

    for sentence in sentences:
        sentence_wordcount = (len(nltk.tokenize.word_tokenize(sentence)))
        sentence_wordcount_without_stop_words = 0
        for word_weight in frequency_table:
            if word_weight in sentence.lower():
                sentence_wordcount_without_stop_words += 1
                if sentence in sentence_scores:
                    sentence_scores[sentence] += frequency_table[word_weight]
                else:
                    sentence_scores[sentence] = frequency_table[word_weight]

        sentence_scores[sentence] = sentence_scores[sentence] / \
            sentence_wordcount_without_stop_words

    return sentence_scores


def build_scibert_objects():

    # Build SciBert model objects so it can be cached when making many summaries

    scibert_config = AutoConfig.from_pretrained(PATH_SCIBERT_MODEL)
    scibert_config.output_hidden_states = True
    scibert_tokenizer = AutoTokenizer.from_pretrained(PATH_SCIBERT_MODEL)
    scibert_model = AutoModel.from_pretrained(
        PATH_SCIBERT_MODEL, config=scibert_config)

    return scibert_model, scibert_tokenizer


class BertSummarizer(object):

    """
    Base handler for BERT models.
    """

    scibert_model, scibert_tokenizer = build_scibert_objects()

    MODELS = {
        'allenai/scibert_scivocab_uncased': (scibert_model, scibert_tokenizer)
    }

    summarizer = None

    def __init__(
        self,
        model: str = 'allenai/scibert_scivocab_uncased',
        custom_model=None,
        custom_tokenizer=None,
        use_coreference_handling: bool = False
    ):
        """
        :param model: Model is the string path for the bert weights. If given a keyword, the s3 path will be used
        :param custom_model: This is optional if a custom bert model is used
        :param custom_tokenizer: Place to use custom tokenizer
        :param use_coreference_handling: whether to use coreference handling
        """

        base_model, base_tokenizer = self.MODELS.get(model, (None, None))

        if custom_model is not None:
            self.model = custom_model
        else:
            self.model = base_model

        if custom_tokenizer is not None:
            self.tokenizer = custom_tokenizer
        else:
            self.tokenizer = base_tokenizer

        self.model.eval()
        self.use_coreference_handling = use_coreference_handling

    # for interaction with the main script
    def discard_sentence(sentence):
        words = set(nltk.word_tokenize(sentence))
        boilerplate_sentence_words = ["license", "CC-BY-NC-ND", "medRxiv", "manuscript"]
        for word in boilerplate_sentence_words:
            if word in words:
                return True
        return False

    def summarize_text(self, text, **kwargs):
        """Summarize text

        :params text: Text to summarize
        :params kwargs: kwargs to pass to tokenizer
        """
        if self.summarizer is None:
            summarizer_kwargs = {
                "custom_model": self.model,
                "custom_tokenizer": self.tokenizer
            }
            # TODO: would be cool to enable this feature
            # if self.use_coreference_handling:
            #     summarizer_kwargs["sentence_handler"] = CoreferenceHandler(
            #         greedyness=0.4)
            self.summarizer = Summarizer(**summarizer_kwargs)
        return self.summarizer(text, **kwargs)

    def tokenize_input(self, text: str, max_tokens=512) -> torch.tensor:
        """
        Tokenizes the text input.
        :param text: Text to tokenize
        :param max_tokens: maximum number of tokens
        :return: Returns a torch tensor
        """
        # add cls and sep identifiers - unsure if this will help or not
        # text = '{} {} {}'.format('[CLS]', text, '[SEP]')
        tokenized_text = self.tokenizer.tokenize(text)
        # check if input is too long
        if len(tokenized_text) > max_tokens:
            tokenized_text = tokenized_text[:max_tokens]
            # tokenized_text.append('[SEP]')
        indexed_tokens = self.tokenizer.convert_tokens_to_ids(tokenized_text)
        return torch.tensor([indexed_tokens])

    def _extract_sentence_embedding(
        self,
        sentence: str,
        hidden: int = -2,
        squeeze: bool = False,
        reduce_option: str = 'mean'
    ):
        """
        Extracts the embeddings for the given sentence

        If the sentence is longer than 512 tokens, truncates to 512.

        :param sentence: The sentence to extract embeddings for.
        :param hidden: The hidden layer to use for a readout handler
        :param squeeze: If we should squeeze the outputs (required for some layers)
        :param reduce_option: How we should reduce the items.
        :return: A numpy array.
        """
        tokens_tensor = self.tokenize_input(sentence, 512)
        pooled, hidden_states = self.model(tokens_tensor)[-2:]

        if -1 > hidden > -12:

            if reduce_option == 'max':
                pooled = hidden_states[hidden].max(dim=1)[0]

            elif reduce_option == 'median':
                pooled = hidden_states[hidden].median(dim=1)[0]

            else:
                pooled = hidden_states[hidden].mean(dim=1)

        if squeeze:
            return pooled.detach().numpy().squeeze()

        return pooled

    def extract_doc_embedding(
        self,
        text: str,
        hidden: int = -2,
        squeeze: bool = True,
        reduce_option: str = 'mean'
    ):
        """
        Extracts the embeddings for the given text.

        Splits into sentences and then takes the mean of the sentences

        :param text: The text to extract embeddings for.
        :param hidden: The hidden layer to use for a readout handler
        :param squeeze: If we should squeeze the outputs (required for some layers)
        :param reduce_option: How we should reduce the items.
        :return: A numpy array.
        """
        sentence_embeddings = []
        for sentence in nltk.sent_tokenize(text):
            if not discard_sentence(sentence):
                sentence_embeddings.append(self._extract_sentence_embedding(
                sentence, hidden, squeeze, reduce_option))
        return np.mean(sentence_embeddings, axis=0)

    def create_matrix(
        self,
        content,
        hidden=-2,
        reduce_option='mean'
    ):
        """
        Create matrix from the embeddings
        :param content: The list of sentences
        :param hidden: Which hidden layer to use
        :param reduce_option: The reduce option to run.
        :return: A numpy array matrix of the given content.
        """

        return np.asarray([
            np.squeeze(self.extract_doc_embedding(t, hidden=hidden,
                                                  reduce_option=reduce_option).data.numpy())
            for t in content
        ])

    def __call__(
        self,
        content,
        hidden=-2,
        reduce_option='mean'
    ):
        return self.create_matrix(content, hidden, reduce_option)

# Summarization


def summarization_tf(text_string, num_sentences=2):

    # Algorithm to score each sentence from the input
    frequency_table = create_frequency_table(text_string)
    sentence_scores = calculate_sentence_scores(text_string, frequency_table)

    # Sort sentences by their scores
    sentences_sorted = sorted(sentence_scores.items(),
                              key=lambda x: x[1], reverse=True)

    # Get ranked sentences and put into final summary
    summary = ''
    counter = 0
    for sentence in sentences_sorted:
        summary += sentence[0] + ' '
        counter += 1
        if counter == num_sentences:
            break

    return summary


def summarization_lsa():
    pass

# Evaluation


def summarization_evaluation(embedding_a, embedding_b):
    cos_similarity = sklearn.metrics.pairwise.cosine_similarity(
        embedding_a.reshape(1, -1), embedding_b.reshape(1, -1))
    return cos_similarity
