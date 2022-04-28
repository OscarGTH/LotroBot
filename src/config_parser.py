import configargparse

# Parses configuration file
def get_configuration():
    p = configargparse.ArgParser(
        default_config_files=['/etc/app/conf.d/*.conf', '~/.my_settings'])
    p.add('-c', '--my-config', required=True,
          is_config_file=True, help='config file path')
    p.add('--test', required=True, help='Test configuration object.')
    options = p.parse_args()

    return options