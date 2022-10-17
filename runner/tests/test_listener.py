import pytest
from celery.app.control import Inspect

from runner.listener import _has_available_worker


@pytest.fixture
def get_inspect() -> Inspect:
    """Return empty Inspect object"""
    return Inspect()


def test_has_all_available_workers(mocker, get_inspect):
    def mock_worker_tasks(inspect: Inspect = get_inspect):
        return []

    def mock_worker_concurrency():
        return 4

    mocker.patch("runner.listener._get_current_worker_tasks", mock_worker_tasks)
    mocker.patch("runner.listener._get_worker_concurrency", mock_worker_concurrency)

    assert _has_available_worker(get_inspect)

    worker_tasks = mock_worker_tasks()
    worker_concurrency = mock_worker_concurrency()
    assert len(worker_tasks) < worker_concurrency


def test_has_some_available_workers(mocker, get_inspect):
    def mock_worker_tasks(inspect: Inspect = get_inspect):
        return [1, 2]

    def mock_worker_concurrency():
        return 4

    mocker.patch("runner.listener._get_current_worker_tasks", mock_worker_tasks)
    mocker.patch("runner.listener._get_worker_concurrency", mock_worker_concurrency)
    assert _has_available_worker(get_inspect)

    worker_tasks = mock_worker_tasks()
    worker_concurrency = mock_worker_concurrency()
    assert len(worker_tasks) < worker_concurrency


def test_has_no_available_workers(mocker, get_inspect):
    def mock_worker_tasks(inspect: Inspect = get_inspect):
        return [1, 2, 3, 4]

    def mock_worker_concurrency():
        return 4

    mocker.patch("runner.listener._get_current_worker_tasks", mock_worker_tasks)
    mocker.patch("runner.listener._get_worker_concurrency", mock_worker_concurrency)
    assert not _has_available_worker(get_inspect)

    worker_tasks = mock_worker_tasks()
    worker_concurrency = mock_worker_concurrency()
    assert len(worker_tasks) == worker_concurrency
