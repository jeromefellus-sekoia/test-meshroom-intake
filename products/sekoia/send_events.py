import json
from meshroom.decorators import send
from .api import SekoiaAPI
from meshroom.model import Plug, Tenant


@send("events")
def send_events(
    tenant: Tenant,
    data: str | bytes | dict,
    plug: Plug | None = None,
):
    """Watch events received by a Sekoia intake (when plug is provided) or by a whole Sekoia.io community otherwise."""
    api = SekoiaAPI(
        tenant.settings.get("region", "fra1"),
        tenant.get_secret("API_KEY"),
    )

    if isinstance(data, bytes):
        data = data.decode()
    if not isinstance(data, str):
        data = json.dumps(data)
    print(f"Send event to intake {plug.settings['intake_uuid']}:\n\n{data}\n\n")
    return api.send_event_http(plug.get_secret("intake_key"), data)
