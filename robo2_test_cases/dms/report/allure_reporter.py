"""Small Allure adapter for this project's custom Selenium runner (no pytest)."""
from __future__ import annotations

import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from allure_commons import plugin_manager
from allure_commons.lifecycle import AllureLifecycle
from allure_commons.logger import AllureFileLogger
from allure_commons.model2 import Label, Link, StatusDetails
from allure_commons.types import AttachmentType
from allure_commons.utils import now, uuid4


_LOGGERS: dict[str, AllureFileLogger] = {}


def _logger_for(results_dir: Path) -> AllureFileLogger:
    key = str(results_dir.resolve())
    if key not in _LOGGERS:
        results_dir.mkdir(parents=True, exist_ok=True)
        logger = AllureFileLogger(str(results_dir), clean=False)
        plugin_name = f"report-allure-file-logger-{abs(hash(key))}"
        if plugin_manager.get_plugin(plugin_name) is None:
            plugin_manager.register(logger, name=plugin_name)
        _LOGGERS[key] = logger
    return _LOGGERS[key]


class AllureReporter:
    """Writes Allure 2 results using the official allure-python-commons lifecycle."""

    def __init__(self, results_dir: Path):
        self.results_dir = results_dir
        _logger_for(results_dir)
        self.lifecycle = AllureLifecycle()
        self.test_uuid: str | None = None

    def start_test(self, test_id: str, title: str, feature: str, description: str, url: str) -> None:
        self.test_uuid = uuid4()
        with self.lifecycle.schedule_test_case(self.test_uuid) as result:
            result.name = f"{test_id} - {title}"
            result.fullName = f"Report.{feature}.{test_id}"
            result.testCaseId = test_id
            result.description = description
            result.start = now()
            result.labels.extend([
                Label(name="suite", value="Report"),
                Label(name="feature", value=feature),
                Label(name="parentSuite", value="Robo2mation"),
                Label(name="framework", value="custom-selenium"),
            ])
            if url:
                result.links.append(Link(name="Report page", url=url, type="link"))

    @contextmanager
    def step(self, name: str) -> Iterator[None]:
        if not self.test_uuid:
            raise RuntimeError("Allure test has not been started.")
        step_uuid = uuid4()
        with self.lifecycle.start_step(parent_uuid=self.test_uuid, uuid=step_uuid) as step_result:
            step_result.name = name
            step_result.start = now()
            try:
                yield
                step_result.status = "passed"
            except AssertionError as exc:
                step_result.status = "failed"
                step_result.statusDetails = StatusDetails(message=str(exc), trace=traceback.format_exc())
                raise
            except Exception as exc:
                step_result.status = "broken"
                step_result.statusDetails = StatusDetails(message=str(exc), trace=traceback.format_exc())
                raise
            finally:
                step_result.stop = now()
                self.lifecycle.stop_step(uuid=step_uuid)

    def attach_file(self, path: Path, name: str, attachment_type: AttachmentType) -> None:
        if self.test_uuid and path.is_file():
            self.lifecycle.attach_file(
                uuid4(), str(path), name=name, attachment_type=attachment_type,
                parent_uuid=self.test_uuid,
            )

    def attach_text(self, body: str, name: str) -> None:
        if self.test_uuid:
            self.lifecycle.attach_data(
                uuid4(), body, name=name, attachment_type=AttachmentType.TEXT,
                parent_uuid=self.test_uuid,
            )

    def finish(self, status: str, message: str = "", error: BaseException | None = None) -> None:
        if not self.test_uuid:
            return
        with self.lifecycle.update_test_case(self.test_uuid) as result:
            result.status = status
            result.stop = now()
            if message or error:
                result.statusDetails = StatusDetails(
                    message=message or str(error),
                    trace=(
                        "".join(traceback.format_exception(type(error), error, error.__traceback__))
                        if error else None
                    ),
                )
        self.lifecycle.write_test_case(self.test_uuid)
        self.test_uuid = None
