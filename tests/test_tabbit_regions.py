from core.tabbit_regions import CN_BASE_URL, GLOBAL_BASE_URL, resolve_tabbit_endpoint


def test_resolve_default_region_uses_china_endpoint():
    endpoint = resolve_tabbit_endpoint({})

    assert endpoint.region == "cn"
    assert endpoint.base_url == CN_BASE_URL
    assert endpoint.client_id == "2dd8eb4c1ed9c344d173"


def test_resolve_global_region_uses_global_endpoint():
    endpoint = resolve_tabbit_endpoint({"region": "global"})

    assert endpoint.region == "global"
    assert endpoint.base_url == "https://web.tabbit.ai"
    assert endpoint.client_id == "2dd8eb4c1ed9c344d173"


def test_known_preset_base_url_follows_selected_region():
    endpoint = resolve_tabbit_endpoint(
        {"region": "global", "base_url": CN_BASE_URL}
    )

    assert endpoint.region == "global"
    assert endpoint.base_url == "https://web.tabbit.ai"


def test_custom_base_url_and_client_id_override_region_preset():
    endpoint = resolve_tabbit_endpoint(
        {
            "region": "global",
            "base_url": "https://custom.example.com/",
            "client_id": "custom-client",
        }
    )

    assert endpoint.region == "global"
    assert endpoint.base_url == "https://custom.example.com"
    assert endpoint.client_id == "custom-client"
