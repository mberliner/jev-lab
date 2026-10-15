"""Política de enrutado: validación, monotonía por riesgo y huella (data-model.md, «Política»).

FR-009, FR-009a, FR-010 y FR-013 (bandas monótonas).
"""

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from jevlab.domain.diagnostics import InvalidPolicy
from jevlab.domain.policy import ActionName, Policy, PolicyRef, Risk, parse_policy

_SOURCE = "enrutado.yaml"


def data(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "version": "0.1.0",
        "acciones": {
            "mover-a-cola": {"riesgo": "bajo", "umbral": 0.90, "justificacion": "provisional"},
            "reembolsar": {"riesgo": "alto", "umbral": 0.97, "justificacion": "provisional"},
        },
    }
    return base | overrides


def action(name: str, **overrides: Any) -> dict[str, Any]:
    acciones = data()["acciones"]
    acciones[name] = acciones[name] | overrides
    return data(acciones=acciones)


def test_initial_policy_is_valid() -> None:
    policy = parse_policy(data(), _SOURCE)

    move = policy.action(ActionName.MOVER_A_COLA)
    refund = policy.action(ActionName.REEMBOLSAR)
    assert (move.riesgo, move.umbral, move.provisional) == (Risk.BAJO, 0.90, True)
    assert (refund.riesgo, refund.umbral, refund.provisional) == (Risk.ALTO, 0.97, True)
    assert policy.ref == PolicyRef(version="0.1.0", fingerprint=policy.fingerprint)


def test_risks_are_ordered() -> None:
    assert Risk.BAJO.rank < Risk.MEDIO.rank < Risk.ALTO.rank


@pytest.mark.parametrize(
    ("policy_data", "field"),
    [
        (data(acciones={"mover-a-cola": data()["acciones"]["mover-a-cola"]}), "reembolsar"),
        (
            data(acciones=data()["acciones"] | {"borrar": data()["acciones"]["reembolsar"]}),
            "borrar",
        ),
        (action("mover-a-cola", umbral=1.2), "acciones.mover-a-cola.umbral"),
        (action("reembolsar", umbral=-0.1), "acciones.reembolsar.umbral"),
        (action("reembolsar", riesgo="extremo"), "acciones.reembolsar.riesgo"),
        (action("reembolsar", justificacion=" "), "acciones.reembolsar.justificacion"),
        (action("reembolsar", fuente="x"), "acciones.reembolsar.fuente"),
        (data(version="1.0"), "version"),
        ({"acciones": data()["acciones"]}, "version"),
    ],
)
def test_invalid_policy_names_the_field(policy_data: dict[str, Any], field: str) -> None:
    with pytest.raises(InvalidPolicy) as error:
        parse_policy(policy_data, _SOURCE)

    message = str(error.value)
    assert message.startswith(f"política no válida ({_SOURCE}): ")
    assert field in message


def test_not_a_mapping_is_invalid() -> None:
    with pytest.raises(InvalidPolicy, match="política no válida"):
        parse_policy(["version"], _SOURCE)


def test_higher_risk_with_lower_threshold_names_both_actions() -> None:
    with pytest.raises(InvalidPolicy) as error:
        parse_policy(action("reembolsar", umbral=0.85), _SOURCE)

    assert str(error.value) == (
        "política no válida (enrutado.yaml): acciones.reembolsar.umbral 0,85 es menor que el "
        "de mover-a-cola 0,90 con más riesgo"
    )


def test_equal_thresholds_with_different_risk_are_valid() -> None:
    parse_policy(action("reembolsar", umbral=0.90), _SOURCE)


_RISKS = st.sampled_from(list(Risk))
_THRESHOLDS = st.floats(min_value=0, max_value=1, allow_nan=False)


@given(_RISKS, _THRESHOLDS, _RISKS, _THRESHOLDS)
def test_valid_if_and_only_if_monotonic(
    move_risk: Risk, move_threshold: float, refund_risk: Risk, refund_threshold: float
) -> None:
    candidate = data(
        acciones={
            "mover-a-cola": {
                "riesgo": move_risk.value,
                "umbral": move_threshold,
                "justificacion": "provisional",
            },
            "reembolsar": {
                "riesgo": refund_risk.value,
                "umbral": refund_threshold,
                "justificacion": "provisional",
            },
        }
    )
    monotonic = not (
        (refund_risk.rank > move_risk.rank and refund_threshold < move_threshold)
        or (move_risk.rank > refund_risk.rank and move_threshold < refund_threshold)
    )
    try:
        policy = parse_policy(candidate, _SOURCE)
    except InvalidPolicy:
        assert not monotonic
    else:
        assert monotonic
        pairs = [(a.riesgo.rank, a.umbral) for a in policy.acciones.values()]
        for risk_a, threshold_a in pairs:
            for risk_b, threshold_b in pairs:
                if risk_a > risk_b:
                    assert threshold_a >= threshold_b


def _fingerprint(policy_data: dict[str, Any]) -> str:
    return parse_policy(policy_data, _SOURCE).fingerprint


def test_fingerprint_is_eight_hex_chars() -> None:
    fingerprint = _fingerprint(data())
    assert len(fingerprint) == 8
    int(fingerprint, 16)


@pytest.mark.parametrize(
    "changed",
    [
        action("mover-a-cola", umbral=0.91),
        action("reembolsar", riesgo="medio"),
        action("reembolsar", justificacion="evaluación 004"),
        data(version="0.1.1"),
    ],
)
def test_fingerprint_changes_with_any_rule(changed: dict[str, Any]) -> None:
    assert _fingerprint(changed) != _fingerprint(data())


def test_fingerprint_ignores_key_order() -> None:
    original = data()
    reordered = {
        "acciones": {
            "reembolsar": dict(reversed(original["acciones"]["reembolsar"].items())),
            "mover-a-cola": original["acciones"]["mover-a-cola"],
        },
        "version": "0.1.0",
    }
    assert _fingerprint(reordered) == _fingerprint(original)


def test_same_version_with_other_threshold_has_other_fingerprint() -> None:
    a = parse_policy(data(), _SOURCE)
    b = parse_policy(action("mover-a-cola", umbral=0.8), _SOURCE)
    assert a.version == b.version
    assert a.ref != b.ref


def test_policy_is_immutable() -> None:
    policy: Policy = parse_policy(data(), _SOURCE)
    with pytest.raises(ValueError):
        policy.version = "9.9.9"
