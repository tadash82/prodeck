import asyncio

from prodeck_agent.core.actions import open_app, open_path, open_url
from prodeck_agent.core.engine import ActionEngine
from prodeck_agent.core.models import OpenAppAction, OpenPathAction, OpenUrlAction


def run(coro):
    return asyncio.run(coro)


def test_engine_runs_registered_executor():
    engine = ActionEngine()
    calls = []
    engine.register("open_url", calls.append)
    ok, message = run(engine.run(OpenUrlAction(url="https://example.com")))
    assert ok and message == "" and len(calls) == 1


def test_engine_reports_executor_failure():
    engine = ActionEngine()

    def boom(action):
        raise RuntimeError("explodiu")

    engine.register("open_url", boom)
    ok, message = run(engine.run(OpenUrlAction(url="https://example.com")))
    assert not ok and "explodiu" in message


def test_engine_without_executor():
    ok, message = run(ActionEngine().run(OpenUrlAction(url="https://example.com")))
    assert not ok and "open_url" in message


def test_open_app_expands_home_and_skips_shell(monkeypatch):
    captured = {}

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs

    monkeypatch.setattr("subprocess.Popen", fake_popen)
    open_app.execute(OpenAppAction(command=["editor", "~/Projetos"]))
    assert captured["command"][1].startswith("/")
    assert "shell" not in captured["kwargs"]


def test_open_app_program_missing(monkeypatch):
    def fake_popen(command, **kwargs):
        raise FileNotFoundError(command[0])

    monkeypatch.setattr("subprocess.Popen", fake_popen)
    try:
        open_app.execute(OpenAppAction(command=["nao-existe-xyz"]))
    except RuntimeError as exc:
        assert "nao-existe-xyz" in str(exc)
    else:
        raise AssertionError("deveria ter levantado RuntimeError")


def test_open_path_requires_existing_path(tmp_path):
    try:
        open_path.execute(OpenPathAction(path=str(tmp_path / "fantasma")))
    except RuntimeError as exc:
        assert "fantasma" in str(exc)
    else:
        raise AssertionError("deveria ter levantado RuntimeError")


def test_open_url_validates_scheme():
    try:
        open_url.execute(OpenUrlAction(url="file:///etc/passwd"))
    except RuntimeError as exc:
        assert "http" in str(exc)
    else:
        raise AssertionError("deveria ter levantado RuntimeError")
