import json
import stat

from prodeck_agent.core.config import ConfigStore


def test_load_creates_default_config(tmp_path):
    store = ConfigStore(tmp_path)
    config = store.load_config()
    assert store.profiles_path.exists()
    assert config.version == 1
    assert config.profiles and config.profiles[0].pages[0].buttons


def test_save_and_reload_round_trip(tmp_path):
    store = ConfigStore(tmp_path)
    config = store.load_config()
    config.active_profile = config.profiles[0].id
    store.save_config(config)
    assert store.load_config() == config


def test_migrate_adds_version(tmp_path):
    store = ConfigStore(tmp_path)
    store.profiles_path.parent.mkdir(parents=True, exist_ok=True)
    store.profiles_path.write_text(
        json.dumps({"active_profile": "x", "profiles": []}), encoding="utf-8"
    )
    assert store.load_config().version == 1


def test_save_keeps_backup(tmp_path):
    store = ConfigStore(tmp_path)
    config = store.load_config()
    store.save_config(config)
    assert store.profiles_path.with_suffix(".json.bak").exists()


def test_pair_token_is_persistent_and_private(tmp_path):
    store = ConfigStore(tmp_path)
    token = store.pair_token()
    assert token == store.pair_token()
    mode = stat.S_IMODE(store.token_path.stat().st_mode)
    assert mode == 0o600


def test_reset_pairing_changes_token(tmp_path):
    store = ConfigStore(tmp_path)
    old = store.pair_token()
    store.reset_pairing()
    assert store.pair_token() != old
