"""La confianza recalculada coincide con la del servicio en todas las grabaciones (FR-006, SC-003).

Cada grabación se reproduce con el mismo cliente y el mismo decodificador que en vivo.
"""

import pytest

from jevlab.adapters.typesafe_judge import TypeSafeJudge
from jevlab.adapters.yaml_files import YamlSpecLoader
from jevlab.application.triage import TRIAGE_REQUEST
from jevlab.domain.confidence import choice_confidence, score_confidence
from jevlab.domain.examples import Recording

# La API devuelve probabilidades y confianzas con 2 decimales (research.md R3, hallazgo al grabar).
_TOLERANCE = 0.01


def test_recomputed_confidence_matches_service(real_recordings: list[Recording]) -> None:
    spec = YamlSpecLoader().load_request(TRIAGE_REQUEST)
    levels = len(spec.priority.levels)
    for recording in real_recordings:
        with TypeSafeJudge.replay(recording) as judge:
            answers = judge.ask(spec, recording.text)
        if answers.queue is not None:
            recomputed = choice_confidence(answers.queue.probabilities)
            assert recomputed == pytest.approx(answers.queue.confidence, abs=_TOLERANCE), (
                recording.name
            )
        if answers.priority is not None:
            probabilities = [answers.priority.probabilities.get(i, 0.0) for i in range(levels)]
            assert score_confidence(probabilities) == pytest.approx(
                answers.priority.confidence, abs=_TOLERANCE
            ), recording.name
