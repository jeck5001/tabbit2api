from dataclasses import dataclass

CN_REGION = "cn"
GLOBAL_REGION = "global"
DEFAULT_REGION = CN_REGION

CN_BASE_URL = "https://web.tabbit-ai.com"
GLOBAL_BASE_URL = "https://web.tabbit.ai"
DEFAULT_CLIENT_ID = "2dd8eb4c1ed9c344d173"

REGION_PRESETS = {
    CN_REGION: {
        "label": "国内版",
        "base_url": CN_BASE_URL,
        "client_id": DEFAULT_CLIENT_ID,
    },
    GLOBAL_REGION: {
        "label": "国际版",
        "base_url": GLOBAL_BASE_URL,
        "client_id": DEFAULT_CLIENT_ID,
    },
}


@dataclass(frozen=True)
class TabbitEndpoint:
    region: str
    base_url: str
    client_id: str


def normalize_region(region: str | None) -> str:
    if region in REGION_PRESETS:
        return region
    return DEFAULT_REGION


def normalize_base_url(base_url: str) -> str:
    return base_url.strip().rstrip("/")


def resolve_tabbit_endpoint(tabbit_config: dict | None) -> TabbitEndpoint:
    tabbit_config = tabbit_config or {}
    region = normalize_region(tabbit_config.get("region"))
    preset = REGION_PRESETS[region]
    configured_base_url = normalize_base_url(tabbit_config.get("base_url", ""))
    preset_base_urls = {value["base_url"] for value in REGION_PRESETS.values()}
    if configured_base_url and configured_base_url not in preset_base_urls:
        base_url = configured_base_url
    else:
        base_url = preset["base_url"]
    client_id = (tabbit_config.get("client_id") or preset["client_id"]).strip()

    return TabbitEndpoint(region=region, base_url=base_url, client_id=client_id)


def get_region_presets() -> dict:
    return {
        key: {
            "label": value["label"],
            "base_url": value["base_url"],
            "client_id": value["client_id"],
        }
        for key, value in REGION_PRESETS.items()
    }
