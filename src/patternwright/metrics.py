"""Neutral, configurable prose measurements without quality verdicts."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass


WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
FIRST_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
SENTENCE_SPLIT = re.compile(r'''(?<=[.!?])["'”’）)\]]*\s+''')
TIME_COLON = re.compile(r"(?<=\d):(?=\d)")
NEGATION = re.compile(
    r"\b(?:not|no|never|nobody|nothing|none|nor|neither|cannot)\b|n't\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class MetricConfig:
    long_sentence_words: int = 40
    short_sentence_words: int = 10
    long_word_letters: int = 8
    repeated_opening_minimum: int = 2

    def __post_init__(self):
        for name, value in (
            ("long_sentence_words", self.long_sentence_words),
            ("short_sentence_words", self.short_sentence_words),
            ("long_word_letters", self.long_word_letters),
            ("repeated_opening_minimum", self.repeated_opening_minimum),
        ):
            if type(value) is not int or value < 1:
                raise ValueError("%s must be a positive integer" % name)


@dataclass(frozen=True, slots=True)
class TextMetrics:
    characters: int
    words: int
    paragraphs: int
    sentences: int
    sentence_words_mean: float
    sentence_words_median: float
    sentence_words_minimum: int
    sentence_words_maximum: int
    long_sentences: int
    short_sentences: int
    long_words: int
    long_word_share: float
    comma_and: int
    semicolons: int
    colons: int
    negations: int
    comma_and_per_1000: float
    semicolons_per_1000: float
    colons_per_1000: float
    negations_per_1000: float
    repeated_openings: tuple[tuple[str, int], ...]
    thresholds: MetricConfig

    def to_dict(self) -> dict[str, object]:
        return {
            "characters": self.characters,
            "words": self.words,
            "paragraphs": self.paragraphs,
            "sentences": self.sentences,
            "sentence_words": {
                "mean": self.sentence_words_mean,
                "median": self.sentence_words_median,
                "minimum": self.sentence_words_minimum,
                "maximum": self.sentence_words_maximum,
                "long": self.long_sentences,
                "short": self.short_sentences,
            },
            "long_words": {
                "count": self.long_words,
                "share": self.long_word_share,
            },
            "punctuation": {
                "comma_and": self.comma_and,
                "semicolons": self.semicolons,
                "colons": self.colons,
            },
            "negations": self.negations,
            "rates_per_1000_words": {
                "comma_and": self.comma_and_per_1000,
                "semicolons": self.semicolons_per_1000,
                "colons": self.colons_per_1000,
                "negations": self.negations_per_1000,
            },
            "repeated_openings": [
                {"word": word, "count": count}
                for word, count in self.repeated_openings
            ],
            "thresholds": {
                "long_sentence_words": self.thresholds.long_sentence_words,
                "short_sentence_words": self.thresholds.short_sentence_words,
                "long_word_letters": self.thresholds.long_word_letters,
                "repeated_opening_minimum": self.thresholds.repeated_opening_minimum,
            },
        }


def _paragraphs(text: str) -> list[str]:
    return [
        " ".join(block.split()) for block in re.split(r"\n\s*\n", text)
        if block.strip()
    ]


def _sentences(paragraph: str) -> list[str]:
    return [part.strip() for part in SENTENCE_SPLIT.split(paragraph) if part.strip()]


def measure(text: str, config: MetricConfig | None = None) -> TextMetrics:
    """Measure neutral surface distributions for one supplied text string."""
    config = config or MetricConfig()
    paragraphs = _paragraphs(text)
    sentences = [sentence for paragraph in paragraphs for sentence in _sentences(paragraph)]
    tokens = WORD.findall(text)
    sentence_lengths = [len(WORD.findall(sentence)) for sentence in sentences]
    openings: dict[str, int] = {}
    for sentence in sentences:
        match = FIRST_WORD.search(sentence)
        if match:
            word = match.group(0).casefold()
            openings[word] = openings.get(word, 0) + 1
    repeated = tuple(sorted(
        (
            (word, count) for word, count in openings.items()
            if count >= config.repeated_opening_minimum
        ),
        key=lambda item: (-item[1], item[0]),
    ))
    words = len(tokens)
    scale = 1000.0 / words if words else 0.0
    comma_and = len(re.findall(r",\s+and\b", text, re.IGNORECASE))
    semicolons = text.count(";")
    colons = text.count(":") - len(TIME_COLON.findall(text))
    negations = len(NEGATION.findall(text))
    long_words = sum(
        1 for token in tokens
        if sum(character.isalpha() for character in token) >= config.long_word_letters
    )
    return TextMetrics(
        characters=len(text),
        words=words,
        paragraphs=len(paragraphs),
        sentences=len(sentences),
        sentence_words_mean=(
            sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0.0
        ),
        sentence_words_median=(
            float(statistics.median(sentence_lengths)) if sentence_lengths else 0.0
        ),
        sentence_words_minimum=min(sentence_lengths, default=0),
        sentence_words_maximum=max(sentence_lengths, default=0),
        long_sentences=sum(
            length >= config.long_sentence_words for length in sentence_lengths
        ),
        short_sentences=sum(
            length < config.short_sentence_words for length in sentence_lengths
        ),
        long_words=long_words,
        long_word_share=(long_words / words if words else 0.0),
        comma_and=comma_and,
        semicolons=semicolons,
        colons=colons,
        negations=negations,
        comma_and_per_1000=comma_and * scale,
        semicolons_per_1000=semicolons * scale,
        colons_per_1000=colons * scale,
        negations_per_1000=negations * scale,
        repeated_openings=repeated,
        thresholds=config,
    )
