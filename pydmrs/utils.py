import os
from configparser import ConfigParser, NoSectionError, NoOptionError
import pydmrs

CONFIG_DIR = os.path.normpath(os.path.join(pydmrs.__file__, '../__config__'))

def get_config_option(config, section, option, opt_type=None, default=None):
    """
    Safe read of config option that returns default value if the section or option are not present.
    :param config: ConfigParser object with existing configuration
    :param section: Section name string
    :param option: Option name string
    :param opt_type: Option python type. String by default.
    :param default: Default value to return if section/option do not exist. None by default.
    :return: Option value
    """

    try:
        if opt_type is None:
            return config.get(section, option)
        elif opt_type == int:
            return config.getint(section, option)
        elif opt_type == float:
            return config.getfloat(section, option)
        elif opt_type == bool:
            return config.getboolean(section, option)
        elif opt_type == list:
            return parse_config(config.get(section, option))

    except (NoSectionError, NoOptionError):
        return default


def parse_config(config_string):
    """
    Parse the config string to a list of strings.
     Lines starting with '#' are ignored.
     Strings are split on commas
    :param config_string: String as read from the config file
    :return: List of general predicate strings to filter
    """

    strings = []

    for line in config_string.split('\n'):
        line = line.strip()

        if line == '' or line.startswith('#'):
            continue

        string_group = [x.strip() for x in line.split(',') if x.strip() != '']

        strings.extend(string_group)

    return strings

def load_config(filename, default=True):
    """
    Load a default config file
    :param filename: name of the file (in the config directory)
    :param default: if True, append filename to default config directory
    """
    config = ConfigParser()
    if default:
        filename = os.path.join(CONFIG_DIR, filename) 
    config.read(filename)
    return config


def split_dmrs_string(content):
    """
    Split a string of DMRS read from a file into indvidual DMRS strings.
    :param content: File content
    :return: List of DMRS XML strings
    """

    content_split = content.split('<dmrs')
    content_filter = filter(lambda x: x.strip() != '', content_split)
    content_fixed = [('<dmrs' + x).strip() for x in content_filter]
    return content_fixed