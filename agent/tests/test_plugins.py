from fastapi.testclient import TestClient

from prodeck_agent.core.config import ConfigStore
from prodeck_agent.core.engine import ActionEngine
from prodeck_agent.core.models import DeckConfig, PluginAction, Profile
from prodeck_agent.core.pairing import Pairing
from prodeck_agent.core.plugins import (
    ActionPlugin,
    PluginField,
    load_plugins,
    plugin_executor,
    plugins_metadata,
)
from prodeck_agent.server.app import create_app


def test_load_plugins_finds_builtin_notify():
    plugins = load_plugins()
    assert "notify" in plugins
    assert plugins["notify"].label == "Notificação"


def test_plugin_executor_dispatches_params():
    calls: list[dict] = []
    registry = {
        "demo": ActionPlugin(
            name="demo", label="Demo", icon="mdi:x", run=lambda p: calls.append(p)
        )
    }
    execute = plugin_executor(registry)
    execute(PluginAction(name="demo", params={"k": "v"}))
    assert calls == [{"k": "v"}]


def test_plugin_executor_unknown_raises():
    execute = plugin_executor({})
    try:
        execute(PluginAction(name="sumiu"))
    except RuntimeError as exc:
        assert "plugin não encontrado" in str(exc)
    else:
        raise AssertionError("deveria ter levantado RuntimeError")


def test_plugins_metadata_shape():
    registry = {
        "demo": ActionPlugin(
            name="demo",
            label="Demo",
            icon="mdi:x",
            run=lambda p: None,
            fields=(PluginField("k", "Campo", "ph"),),
        )
    }
    assert plugins_metadata(registry) == [
        {
            "name": "demo",
            "label": "Demo",
            "icon": "mdi:x",
            "color": "#6366f1",
            "fields": [{"key": "k", "label": "Campo", "placeholder": "ph"}],
        }
    ]


def test_plugins_endpoint_requires_token(tmp_path):
    store = ConfigStore(tmp_path)
    store.save_config(DeckConfig(active_profile="t", profiles=[Profile(id="t", name="T")]))
    app = create_app(store, ActionEngine(), Pairing(store), http_port=8710)
    client = TestClient(app)

    assert client.get("/plugins").status_code == 401

    ok = client.get(f"/plugins?token={store.pair_token()}")
    assert ok.status_code == 200
    assert any(p["name"] == "notify" for p in ok.json())
