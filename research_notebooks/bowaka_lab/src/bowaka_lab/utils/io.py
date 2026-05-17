"""Path resolution: locate the QuantLab repo root or the standalone Bowaka root."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathResolution:
    repo_root: Path | None
    bowaka_root: Path
    data_root: Path
    output_root: Path
    is_quantlab_host: bool


class PathResolver:
    """Resolve data and output roots from environment and disk layout.

    Order of precedence:

    1. Explicit ``data_root`` / ``output_root`` constructor arguments.
    2. ``BOWAKA_DATA_ROOT`` / ``BOWAKA_OUTPUT_ROOT`` env vars.
    3. If the QuantLab repo is detected (parent contains both ``app/`` and
       ``research_notebooks/``), use ``app/data/bowaka_lab`` and
       ``app/outputs/bowaka_lab``.
    4. Otherwise fall back to ``<bowaka_root>/data`` and ``<bowaka_root>/artifacts``.
    """

    def __init__(
        self,
        bowaka_root: Path | str | None = None,
        *,
        data_root: Path | str | None = None,
        output_root: Path | str | None = None,
        env: dict[str, str] | None = None,
    ):
        self._bowaka_root = Path(bowaka_root) if bowaka_root else self._auto_detect_bowaka_root()
        self._data_root_override = Path(data_root) if data_root else None
        self._output_root_override = Path(output_root) if output_root else None
        self._env = env if env is not None else dict(os.environ)

    @staticmethod
    def _auto_detect_bowaka_root() -> Path:
        here = Path(__file__).resolve()
        for ancestor in [here, *here.parents]:
            if ancestor.name == "bowaka_lab" and (ancestor / "src").is_dir():
                return ancestor
        return here.parents[3]

    def _detect_repo_root(self) -> Path | None:
        for ancestor in [self._bowaka_root, *self._bowaka_root.parents]:
            if (ancestor / "app").is_dir() and (ancestor / "research_notebooks").is_dir():
                if ancestor != self._bowaka_root:
                    return ancestor
        return None

    def resolve(self) -> PathResolution:
        repo_root = self._detect_repo_root()
        bowaka_root = self._bowaka_root
        is_quantlab_host = repo_root is not None

        data_root: Path
        if self._data_root_override is not None:
            data_root = self._data_root_override
        elif self._env.get("BOWAKA_DATA_ROOT"):
            data_root = Path(self._env["BOWAKA_DATA_ROOT"])
        elif is_quantlab_host:
            assert repo_root is not None
            data_root = repo_root / "app" / "data" / "bowaka_lab"
        else:
            data_root = bowaka_root / "data"

        output_root: Path
        if self._output_root_override is not None:
            output_root = self._output_root_override
        elif self._env.get("BOWAKA_OUTPUT_ROOT"):
            output_root = Path(self._env["BOWAKA_OUTPUT_ROOT"])
        elif is_quantlab_host:
            assert repo_root is not None
            output_root = repo_root / "app" / "outputs" / "bowaka_lab"
        else:
            output_root = bowaka_root / "artifacts"

        return PathResolution(
            repo_root=repo_root,
            bowaka_root=bowaka_root,
            data_root=data_root,
            output_root=output_root,
            is_quantlab_host=is_quantlab_host,
        )

    def ensure_dirs(self) -> PathResolution:
        res = self.resolve()
        res.data_root.mkdir(parents=True, exist_ok=True)
        res.output_root.mkdir(parents=True, exist_ok=True)
        return res
