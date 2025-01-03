from meshroom.decorators import setup
from meshroom.model import Tenant
from meshroom.model import Plug
from meshroom.model import Integration
from ...api import SekoiaAPI
import yaml
import json

@setup(title="Create custom intake format 'example'", order=2)
def create_custom_intake_format(integration: Integration, plug: Plug, tenant: Tenant):
    """A setup hook that setup a custom Sekoia.io intake format from integration's files"""
    api = SekoiaAPI(tenant.settings.get('region', 'fra1'), tenant.get_secret('API_KEY'))
    name = integration.target_product
    path = integration.path.parent / 'dist' / 'formats' / name
    try:
        with open(path / 'ingest/parser.yml', 'r') as f:
            parser = yaml.safe_load(f)
    except FileNotFoundError:
        parser = None
    try:
        with open(path / '_meta/fields.yml', 'r') as f:
            taxonomy = yaml.safe_load(f) or {}
    except FileNotFoundError:
        taxonomy = {}
    try:
        with open(path / '_meta/smart-descriptions.json', 'r') as f:
            smart_descriptions = json.load(f)
    except FileNotFoundError:
        smart_descriptions = None
    with open(path / '_meta/manifest.yml', 'r') as f:
        manifest = yaml.safe_load(f)
    data_sources = list(manifest.get('data_sources', {}).keys())
    api.create_or_update_custom_intake_format(manifest['uuid'], name, manifest.get('description', ''), parser, data_sources, manifest.get('slug') or name, list(taxonomy.values()), smart_descriptions, logo=path / '_meta/logo.png', automation_module_uuid=manifest.get('automation_module_uuid') or integration.intake_format_uuid if integration.mode == 'pull' else None, automation_connector_uuid=manifest.get('automation_connector_uuid') or integration.intake_format_uuid if integration.mode == 'pull' else None)
    print(f'✓ Custom intake format {name} successfully pushed')

@setup(title="Create intake 'example'", order=3)
def create_intake_key(integration: Integration, plug: Plug, tenant: Tenant):
    """Create an intake key to consume events"""
    if (intake_key := plug.get_secret('intake_key')):
        print('🚫 Intake key already exists')
        return intake_key
    api = SekoiaAPI(tenant.settings.get('region', 'fra1'), tenant.get_secret('API_KEY'))
    if not getattr(integration, 'intake_format_uuid', None):
        raise ValueError("Intakes can't be created without an intake format, see example/products/sekoia/templates/event_consumer for inspiration")
    intake_name = integration.target_product.replace('_', ' ')
    entity_uuid = api.get_or_create_main_entity()['uuid']
    if integration.mode == 'pull':
        if not getattr(integration, 'automation_module_uuid', None):
            raise ValueError('Pull intakes require a connector, see example/products/sekoia/templates/event_consumer_pull for inspiration')
        module_configuration = plug.dst_config.get('module_configuration') or {}
        connector_configuration = plug.dst_config.get('connector_configuration') or {}
        module_configuration_uuid = api.get_or_create_module_configuration(integration.automation_module_uuid, 'Meshroom', module_configuration)['uuid']
        intake = api.create_intake_key(entity_uuid, integration.intake_format_uuid, intake_name, connector_configuration=connector_configuration, connector_module_configuration_uuid=module_configuration_uuid)
    else:
        intake = api.create_intake_key(entity_uuid, integration.intake_format_uuid, intake_name)
    plug.set_secret('intake_key', intake['intake_key'])
    plug.settings['intake_uuid'] = intake['uuid']
    plug.save()
    print(f'✓ Intake {intake_name} created')