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

        gpred_filter_group = [x.strip() for x in line.split(',') if x.strip() != '']
        gpred_filters_abbv = ['_'.join(gpred.split('_')[:-1]) if gpred.endswith('_rel') else gpred for gpred in gpred_filter_group]

        gpred_filters.extend(gpred_filters_abbv)

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


def gpred_filtering(dmrs, gpred_filter):
    '''
    Remove general predicate nodes on the filter list from the DMRS.
    :param dmrs_xml: Input DMRS object
    :param gpred_filters: A list of general predicates to filter
    :return: Output DMRS object
    '''

    print(gpred_filter)

    filterable_nodes = []

    # Find general predicate nodes to filter
    for node in dmrs.iter_nodes():
        if node.is_gpred_node and node.pred.name in gpred_filter:
            filterable_nodes.append(node)


    return dmrs
    # for entity in dmrs_xml:
    #     if entity.tag == 'node':
    #         node = entity
    #         node_id = node.attrib['nodeid']
    #         gpred_rel = None
    #
    #         for node_info in node:
    #             if node_info.tag == 'realpred':
    #                 break
    #             elif node_info.tag == 'gpred':
    #                 gpred_rel = node_info.text
    #                 break
    #
    #         if gpred_rel and gpred_rel in gpred_filter:
    #             remove_nodes[node_id] = node
    #
    # # Test whether removing a node would result in a disconnected graph. Remove only the ones that do not.
    # removed_nodes = dict()
    # removed_node_ids = set()
    #
    # already_disconnected = not is_connected(dmrs_xml)
    #
    # for node_id, node in remove_nodes.items():
    #     if not already_disconnected and not is_connected(dmrs_xml, removed_nodes=(removed_node_ids | {node_id}),
    #                                                      to_remove=remove_nodes):
    #         # print 'Removing node with id %s would result in a disconnected graph, so we are not.' % node_id
    #         continue
    #     else:
    #         removed_node_ids.add(node_id)
    #         removed_nodes[node_id] = node
    #
    # # Actually remove nodes
    # for _, node in removed_nodes.items():
    #     dmrs_xml.remove(node)
    #
    # # Find links to or from general predicate nodes to filter
    # for entity in dmrs_xml:
    #     if entity.tag == 'link':
    #         link = entity
    #         if link.attrib['from'] in removed_nodes or link.attrib['to'] in removed_nodes:
    #             remove_links.add(link)
    #
    # for link in remove_links:
    #     dmrs_xml.remove(link)
    #
    # return dmrs_xml


def dmrs_simplification(dmrs, gpred_filter):

    if gpred_filter is not None:
        dmrs = gpred_filtering(dmrs, gpred_filter)

    return dmrs


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='DMRS simplification tool')
    parser.add_argument('-c', '--config', default=DEFAULT_CONFIG_FILE,
                        help='Path to simplifaction configuration file. By default, configuration in configs/default_simplification.conf is used.')
    parser.add_argument('input_dmrs', help='Specify input DMRS file')
    parser.add_argument('output_dmrs', help='Specify output dmrs file.')

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
            break

