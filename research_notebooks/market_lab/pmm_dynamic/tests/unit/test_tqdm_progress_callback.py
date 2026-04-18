"""Tests for TqdmProgressCallback."""

from unittest.mock import MagicMock

from pmm_lab.optuna.callbacks import TqdmProgressCallback


def test_tqdm_progress_callback_advances_bar():
    bar = MagicMock()
    cb = TqdmProgressCallback(bar)
    study, trial = MagicMock(), MagicMock()
    cb(study, trial)
    bar.update.assert_called_once_with(1)


def test_tqdm_progress_callback_no_postfix_by_default():
    bar = MagicMock()
    cb = TqdmProgressCallback(bar)
    cb(MagicMock(), MagicMock())
    bar.set_postfix_str.assert_not_called()


def test_tqdm_progress_callback_with_best_updates_postfix():
    import optuna

    bar = MagicMock()
    cb = TqdmProgressCallback(bar, show_best=True)

    study = MagicMock()
    # Build mock trials with COMPLETE state and float values
    trial_a = MagicMock()
    trial_a.state = optuna.trial.TrialState.COMPLETE
    trial_a.value = 0.12

    trial_b = MagicMock()
    trial_b.state = optuna.trial.TrialState.COMPLETE
    trial_b.value = 0.34

    study.trials = [trial_a, trial_b]

    cb(study, MagicMock())
    # Postfix should be set with the max (0.34)
    bar.set_postfix_str.assert_called_once()
    call_arg = bar.set_postfix_str.call_args[0][0]
    assert "0.34" in call_arg
