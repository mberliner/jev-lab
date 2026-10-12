import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from jevlab.domain.diagnostics import (
    CheckResult,
    CheckStatus,
    DoctorReport,
    ProviderRejected,
    ProviderUnavailable,
    Scope,
)


def _result(scope: Scope, status: CheckStatus) -> CheckResult:
    fix = None if status is CheckStatus.OK else "arreglo"
    return CheckResult(name="x", scope=scope, status=status, detail="d", fix=fix)


_valid_results = st.one_of(
    st.builds(
        _result,
        st.just(Scope.LOCAL),
        st.sampled_from([CheckStatus.OK, CheckStatus.FAIL]),
    ),
    st.builds(_result, st.just(Scope.REMOTE), st.sampled_from(list(CheckStatus))),
)


@given(results=st.lists(_valid_results, max_size=6), remote=st.booleans())
def test_exit_code_follows_the_rule(results: list[CheckResult], remote: bool) -> None:
    report = DoctorReport(results=tuple(results), remote_requested=remote)

    any_fail = any(r.status is CheckStatus.FAIL for r in results)
    remote_unavailable = any(
        r.scope is Scope.REMOTE and r.status is CheckStatus.UNAVAILABLE for r in results
    )
    expected = 1 if any_fail or (remote and remote_unavailable) else 0
    assert report.exit_code() == expected


def test_exit_code_is_zero_when_everything_is_ok() -> None:
    report = DoctorReport(results=(_result(Scope.LOCAL, CheckStatus.OK),), remote_requested=False)
    assert report.exit_code() == 0


def test_exit_code_is_one_with_a_failure() -> None:
    report = DoctorReport(
        results=(_result(Scope.LOCAL, CheckStatus.OK), _result(Scope.LOCAL, CheckStatus.FAIL)),
        remote_requested=False,
    )
    assert report.exit_code() == 1


def test_remote_unavailable_fails_only_when_remote_was_requested() -> None:
    results = (_result(Scope.REMOTE, CheckStatus.UNAVAILABLE),)
    assert DoctorReport(results=results, remote_requested=True).exit_code() == 1
    assert DoctorReport(results=results, remote_requested=False).exit_code() == 0


def test_local_check_cannot_be_unavailable() -> None:
    with pytest.raises(ValidationError, match="local"):
        CheckResult(
            name="env-keys",
            scope=Scope.LOCAL,
            status=CheckStatus.UNAVAILABLE,
            detail="d",
            fix="arreglo",
        )


@pytest.mark.parametrize("status", [CheckStatus.FAIL, CheckStatus.UNAVAILABLE])
def test_fix_is_required_unless_ok(status: CheckStatus) -> None:
    with pytest.raises(ValidationError, match="fix"):
        CheckResult(name="typesafe", scope=Scope.REMOTE, status=status, detail="d")


def test_ok_result_needs_no_fix() -> None:
    result = CheckResult(name="azure", scope=Scope.REMOTE, status=CheckStatus.OK, detail="d")
    assert result.fix is None


def test_results_are_immutable() -> None:
    result = _result(Scope.LOCAL, CheckStatus.OK)
    with pytest.raises(ValidationError):
        result.status = CheckStatus.FAIL


def test_provider_errors_carry_their_cause() -> None:
    assert ProviderRejected(401).status == 401
    assert ProviderRejected(None).status is None
    assert ProviderUnavailable("sin conexion").reason == "sin conexion"
