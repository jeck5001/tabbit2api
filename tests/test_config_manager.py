from core.config import ConfigManager


def test_set_region_global_rewrites_known_china_base_url(tmp_path):
    config_path = tmp_path / "config.json"
    cfg = ConfigManager(config_path)

    cfg.set_val("tabbit", "region", "global")
    cfg.set_val("tabbit", "base_url", "https://web.tabbit-ai.com")

    assert cfg.get("tabbit", "region") == "global"
    assert cfg.get("tabbit", "base_url") == "https://web.tabbit.ai"
