import configparser
import os


_default_configuration = '''
[whim.service]
host = localhost
port = 58765

[whim.settings]
config_file = ${settings_dir}/settings.cfg

[whim.cookie]
cookie_file = ${settings_dir}/cookie.txt
'''


class SectionSettings(object):
    def __init__(self, *,
                 config: configparser.ConfigParser,
                 section: str):
        self._config = config
        self._section = section

    def get_int(self, option: str):
        return self._config.getint(self._section, option)

    def get_boolean(self, option: str):
        return self._config.getboolean(self._section, option)

    def get_float(self, option: str):
        return self._config.getfloat(self._section, option)

    def get_string(self, option: str):
        return self._config.get(self._section, option)


class Settings(object):
    def __init__(self, *, settings_dir: str):
        self._config = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation()
        )
        self._config['DEFAULT']['settings_dir'] = settings_dir
        self._settings = self.get_section(__name__)
        self._load_settings(self._config)

    def get_section(self, section: str) -> SectionSettings:
        return SectionSettings(
            config=self._config,
            section=section,
        )

    def _load_settings(self, config: configparser.ConfigParser):
        config.read_string(
            _default_configuration,
            source='<default>',
        )
        config_filename = self._settings.get_string('config_file')

        if not config.read(config_filename):
            os.makedirs(os.path.dirname(config_filename))
            with open(config_filename, 'w') as f:
                config.write(f)

        config.read(config_filename)
