import argparse
from configparser import ConfigParser, NoSectionError, NoOptionError

from pydmrs.serial import loads_xml, dumps_xml


DEFAULT_CONFIG_FILE = '../configs/default_simplification.conf'


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

    except (NoSectionError, NoOptionError):
        return default


def parse_gpred_filter_config(gpred_filter_config):
    """
    Parse the general predicated filter config to a list of general predicates to filter.
     Lines starting with '#' are ignored.
    :param gpred_filter_config: String of general predicates as read from the config file
    :return: List of general predicate strings to filter
    """

    gpred_filters = []

    for line in gpred_filter_config.split('\n'):
        line = line.strip()

        if line == '' or line.startswith('#'):
            continue

        gpred_filters.extend([x.strip() for x in line.split(',') if x.strip() != ''])

    return gpred_filters


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


def dmrs_simplification(dmrs, gpred_filter):
    return dmrs


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='DMRS simplification tool')
    parser.add_argument('-c', '--config', default=DEFAULT_CONFIG_FILE,
                        help='Path to simplifaction configuration file. By default, configuration in configs/default_simplification.conf is used.')
    parser.add_argument('input_dmrs', help='Specify input DMRS file')
    parser.add_argument('output_dmrs', help='Specify output dmrs file. Set "-" to output to standard output.')

    args = parser.parse_args()

    config = ConfigParser()
    config.read(args.config)

    gpred_filter_config = get_config_option(config, 'General Predicate Filtering', 'filter')
    gpred_filter = parse_gpred_filter_config(gpred_filter_config)

    with open(args.input_dmrs, 'r', encoding="utf-8") as fin, open(args.output_dmrs, 'w') as fout:
        content = fin.read().strip()

        for dmrs_string in split_dmrs_string(content):
            dmrs = loads_xml(dmrs_string)
            simplified_dmrs = dmrs_simplification(dmrs, gpred_filter)
            simplified_dmrs_string = dumps_xml(simplified_dmrs)
            fout.write('%s\n\n' % (simplified_dmrs_string.decode('utf-8'),))
