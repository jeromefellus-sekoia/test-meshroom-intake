from meshroom.decorators import trigger
from meshroom.model import Integration, Tenant


@trigger("action")
def trigger_action(tenant: Tenant, integration: Integration, action: str | None = None, data: dict | None = None):
    """Trigger a Sekoia.io playbook action, given its UUID or name"""
    from .api import SekoiaAPI

    api = SekoiaAPI(
        tenant.settings.get("region", "fra1"),
        tenant.get_secret("API_KEY"),
    )

    module_uuid = getattr(integration, "automation_module_uuid", None)
    action_uuid = getattr(integration, "automation_action_uuid", None)

    if not action_uuid:
        if not action:
            raise ValueError("An action name or UUID must be provided")
        action_uuid = api.get_action_uuid(action)

    if not action_uuid:
        raise ValueError(f"No such action {action}")

    return api.trigger_action(module_uuid, action_uuid, data)
