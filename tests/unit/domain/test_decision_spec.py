"""Validación de las definiciones de decisión y de petición (data-model.md, «Definiciones»)."""

from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from jevlab.domain.decision_spec import (
    ChoiceSpec,
    DecisionSpec,
    NoulSpec,
    RequestSpec,
    ScoreSpec,
    TriageSpec,
)

_DECISION: TypeAdapter[DecisionSpec] = TypeAdapter(DecisionSpec)


def choice(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "cola-destino",
        "version": "0.1.0",
        "model": "jev-1.13.0",
        "primitive": "choice",
        "instructions": "¿A qué cola de soporte pertenece este ticket?",
        "options": {"facturacion": "Cobros.", "tecnico": "Fallos.", "other": "Ninguna."},
        "escape": "other",
    }
    return data | overrides


def noul(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "urgencia-explicita",
        "version": "0.1.0",
        "model": "jev-1.13.0",
        "primitive": "noul",
        "instructions": "¿El ticket menciona explícitamente un problema urgente?",
        "criteria_true": "Lo dice.",
        "criteria_false": "No lo dice.",
        "uncertain_band": {"low": 0.3, "high": 0.7, "justification": "provisional"},
    }
    return data | overrides


def score(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "prioridad",
        "version": "0.1.0",
        "model": "jev-1.13.0",
        "primitive": "score",
        "instructions": "¿Qué prioridad de atención necesita este ticket?",
        "levels": [
            {"name": "baja", "description": "Puede esperar."},
            {"name": "media", "description": "Esta semana."},
            {"name": "alta", "description": "Hoy."},
            {"name": "critica", "description": "Ya."},
        ],
        "threshold": {"level": "alta", "justification": "provisional"},
    }
    return data | overrides


def request(**overrides: Any) -> RequestSpec:
    data: dict[str, Any] = {
        "name": "triaje",
        "version": "0.1.0",
        "max_chars": 4000,
        "questions": {
            "cola": "cola-destino",
            "urgencia": "urgencia-explicita",
            "prioridad": "prioridad",
        },
    }
    return RequestSpec.model_validate(data | overrides)


def decisions() -> dict[str, DecisionSpec]:
    return {d.name: d for d in (_DECISION.validate_python(x) for x in (choice(), noul(), score()))}


def test_valid_decisions_are_parsed_by_primitive() -> None:
    assert isinstance(_DECISION.validate_python(choice()), ChoiceSpec)
    assert isinstance(_DECISION.validate_python(noul()), NoulSpec)
    assert isinstance(_DECISION.validate_python(score()), ScoreSpec)


def test_choice_without_escape_fails() -> None:
    data = choice()
    del data["escape"]
    with pytest.raises(ValidationError):
        _DECISION.validate_python(data)


@pytest.mark.parametrize("escape", ["facturacion", "ninguna"])
def test_escape_must_be_other_or_none(escape: str) -> None:
    options = {"facturacion": "Cobros.", "ninguna": "Nada.", "other": "Ninguna."}
    with pytest.raises(ValidationError):
        _DECISION.validate_python(choice(options=options, escape=escape))


def test_escape_must_be_an_option() -> None:
    with pytest.raises(ValidationError):
        _DECISION.validate_python(choice(escape="none"))


def test_choice_needs_two_options_counting_escape() -> None:
    with pytest.raises(ValidationError):
        _DECISION.validate_python(choice(options={"other": "Ninguna."}))


@pytest.mark.parametrize(
    "band",
    [
        {"low": 0.8, "high": 0.2, "justification": "provisional"},
        {"low": -0.1, "high": 0.5, "justification": "provisional"},
        {"low": 0.2, "high": 1.1, "justification": "provisional"},
        {"low": 0.3, "high": 0.7, "justification": " "},
    ],
)
def test_noul_band_must_be_ordered_in_range_and_justified(band: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        _DECISION.validate_python(noul(uncertain_band=band))


def test_score_needs_two_levels() -> None:
    with pytest.raises(ValidationError):
        _DECISION.validate_python(
            score(
                levels=[{"name": "alta", "description": "Hoy."}],
                threshold={"level": "alta", "justification": "provisional"},
            )
        )


def test_score_threshold_must_be_a_level() -> None:
    with pytest.raises(ValidationError):
        _DECISION.validate_python(score(threshold={"level": "urgente", "justification": "x"}))


def test_score_level_position_is_its_index() -> None:
    spec = _DECISION.validate_python(score())
    assert isinstance(spec, ScoreSpec)
    assert spec.position("alta") == 2
    assert spec.threshold_position == 2


@pytest.mark.parametrize("model", ["jev-latest", "jev-preview"])
def test_moving_alias_fails(model: str) -> None:
    with pytest.raises(ValidationError):
        _DECISION.validate_python(choice(model=model))


@pytest.mark.parametrize("version", ["0.1", "v0.1.0", "uno"])
def test_version_must_be_semver(version: str) -> None:
    with pytest.raises(ValidationError):
        _DECISION.validate_python(choice(version=version))
    with pytest.raises(ValidationError):
        request(version=version)


@pytest.mark.parametrize("max_chars", [0, -1])
def test_request_max_chars_must_be_positive(max_chars: int) -> None:
    with pytest.raises(ValidationError):
        request(max_chars=max_chars)


def test_request_cannot_repeat_a_decision() -> None:
    with pytest.raises(ValidationError):
        request(questions={"cola": "cola-destino", "otra": "cola-destino"})


def test_triage_spec_resolves_questions_and_versions() -> None:
    spec = TriageSpec.resolve(request(), decisions())

    assert spec.model == "jev-1.13.0"
    assert spec.max_chars == 4000
    assert spec.queue.escape == "other"
    assert spec.urgency.uncertain_band.low == 0.3
    assert spec.priority.threshold_position == 2
    assert spec.spec_versions() == {
        "triaje": "0.1.0",
        "cola-destino": "0.1.0",
        "urgencia-explicita": "0.1.0",
        "prioridad": "0.1.0",
    }


def test_triage_spec_fails_with_missing_decision() -> None:
    available = decisions()
    del available["prioridad"]
    with pytest.raises(ValueError, match="prioridad"):
        TriageSpec.resolve(request(), available)


def test_triage_spec_fails_with_different_models() -> None:
    available = decisions()
    available["prioridad"] = _DECISION.validate_python(score(model="jev-1.12.0"))
    with pytest.raises(ValueError, match="modelo"):
        TriageSpec.resolve(request(), available)


def test_triage_spec_fails_with_wrong_primitive_for_question() -> None:
    swapped = request(
        questions={
            "cola": "urgencia-explicita",
            "urgencia": "cola-destino",
            "prioridad": "prioridad",
        }
    )
    with pytest.raises(TypeError, match="cola"):
        TriageSpec.resolve(swapped, decisions())
