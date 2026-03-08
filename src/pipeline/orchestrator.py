"""Pipeline orchestration stubs for the Guest Hub project."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


@dataclass(slots=True)
class PipelineStage:
    """Describes one named stage in the ordered pipeline."""

    name: str
    handler: Callable[[], None]


@dataclass(slots=True)
class PipelineOrchestrator:
    """Coordinates high-level pipeline execution order.

    The stage order should follow the project skeleton's 18-step pipeline.
    """

    stages: list[PipelineStage] = field(default_factory=list)

    def register_stage(self, stage: PipelineStage) -> None:
        """Register a stage to be executed later in order."""
        self.stages.append(stage)

    def run(self) -> None:
        """Run registered stages sequentially.

        TODO:
        - add run context + manifest handling
        - add structured logging and exception strategy
        - persist per-stage QA summaries
        """
        for stage in self.stages:
            stage.handler()


def build_default_stages() -> Iterable[str]:
    """Return default stage names from the markdown spec order."""
    return (
        "load_raw_sources",
        "load_reference_tables",
        "parse_rooms_xml",
        "parse_spa_pdf",
        "parse_dining_csv",
        "standardize_shared_fields",
        "expand_room_guests",
        "enrich_room_lookups",
        "write_canonical_outputs",
        "run_qa_validations",
        "build_guest_phone_dimensions",
        "run_exact_matching",
        "run_fuzzy_matching",
        "apply_support_signals",
        "build_hub_tables",
        "export_deliverables",
        "write_run_manifest",
    )
