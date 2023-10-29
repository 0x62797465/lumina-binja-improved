from .client import LuminaClient

from binaryninja import PluginCommand
from binaryninja.settings import Settings

settings = Settings()

#only register if not in keys already
if 'lumina.host' not in settings.keys():
    settings.register_group('lumina', 'Lumina')
    settings.register_setting('lumina.host', '{"title" : "Lumina Host", "description" : "Host address for the Lumina server", "type" : "string"}')
    settings.register_setting('lumina.port', '{"title" : "Lumina Port", "description" : "Port for the Lumina server", "type" : "string"}')
    settings.register_setting('lumina.key',  '{"title" : "Lumina Key", "description" : "Path to the Key file to connect to the Lumina server with, if any", "type" : "string", "optional" : true}')
    settings.register_setting('lumina.cert', '{"title" : "Lumina TLS Certificate", "description" : "Path to the TLS Certificate for the Lumina server, if any", "type" : "string", "optional" : true}')


#try logging in with configured params
client = LuminaClient()

PluginCommand.register_for_function('Lumina\\Pull current function metadata', 'Obtain function info from Lumina server', client.pull_function_md, client.is_valid)

PluginCommand.register('Lumina\\Pull all function metadata', 'Obtain all function info from Lumina server', client.pull_all_mds, client.is_valid)

PluginCommand.register('Lumina\\Reconnect', 'Reconnect to the lumina server with new configuration', client.reconnect)
