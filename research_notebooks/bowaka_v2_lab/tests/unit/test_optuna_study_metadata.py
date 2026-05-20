"""Study contains config_hash + dataset_hash attrs."""
from __future__ import annotations

from bowaka_v2_lab.optuna.dispatcher import OptunaStudy, build_study_name


def test_study_name_format() -> None:
    name = build_study_name(feed="sip", cost_stress="conservative",
                              dataset_hash="abcdef1234567890")
    assert name.startswith("bowaka_v2_sip_walkforward_conservative_abcdef12_")


def test_study_attrs_set() -> None:
    s = OptunaStudy(feed="sip", cost_stress="conservative",
                     dataset_hash="cafebabecafebabe",
                     config_hash="deadbeefdeadbeef",
                     storage_uri=None, n_trials=1)
    s.create()
    assert s.study.user_attrs["feed"] == "sip"
    assert s.study.user_attrs["cost_stress"] == "conservative"
    assert s.study.user_attrs["config_hash"] == "deadbeefdeadbeef"
    assert s.study.user_attrs["dataset_hash"] == "cafebabecafebabe"
