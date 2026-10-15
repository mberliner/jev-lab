"""Respuestas genéricas y su forma de triaje (data-model.md de la 002, «Respuestas»)."""

from jevlab.domain.triage import Answers, ChoiceAnswer, NoulAnswer, ScoreAnswer, TriageAnswers

_QUEUE = ChoiceAnswer(choice="facturacion", confidence=0.84, probabilities={"facturacion": 0.9})
_URGENCY = NoulAnswer(probability=0.12)
_PRIORITY = ScoreAnswer(score=1.1, confidence=0.5, probabilities={0: 0.2, 1: 0.8})


def test_triage_answers_derived_from_answers_keep_each_question() -> None:
    answers = Answers(
        model="jev-1.13.0",
        by_question={"cola": _QUEUE, "urgencia": _URGENCY, "prioridad": _PRIORITY},
    )

    derived = TriageAnswers.from_answers(answers)

    assert derived == TriageAnswers(
        model="jev-1.13.0", queue=_QUEUE, urgency=_URGENCY, priority=_PRIORITY
    )


def test_missing_question_or_other_primitive_is_none() -> None:
    answers = Answers(model="jev-1.13.0", by_question={"cola": _URGENCY, "prioridad": None})

    derived = TriageAnswers.from_answers(answers)

    assert derived.queue is None
    assert derived.urgency is None
    assert derived.priority is None


def test_choice_returns_only_choice_answers() -> None:
    answers = Answers(model="m", by_question={"cola": _QUEUE, "urgencia": _URGENCY})

    assert answers.choice("cola") == _QUEUE
    assert answers.choice("urgencia") is None
    assert answers.choice("solicitud") is None
