import argparse
from pydmrs.components import GPred
from pydmrs.serial import loads_xml, dumps_xml
from pydmrs.utils import get_config_option, load_config, split_dmrs_string

DEFAULT_CONFIG_FILE = 'default_simplification.conf'

# If run from the command line, load the specified file
# Otherwise, load the default file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DMRS simplification tool')
    parser.add_argument('-c', '--config', default=None,
                        help='Path to simplifaction configuration file. By default, configuration in __config__/default_simplification.conf is used.')
    parser.add_argument('input_dmrs', help='Specify input DMRS file')
    parser.add_argument('output_dmrs', help='Specify output dmrs file.')
    args = parser.parse_args()
    if args.config is not None:  # Load the given file
        config = load_config(args.config, default=False)
    else:
        config = load_config(DEFAULT_CONFIG_FILE)
else:
    config = load_config(DEFAULT_CONFIG_FILE)

DEFAULT_FILTER = frozenset(GPred.from_string(x) for x in get_config_option(config, 'General Predicate Filtering', 'filter', opt_type=list))
DEFAULT_ALLOW_DISC = get_config_option(config, 'General Predicate Filtering', 'allow_disconnected_dmrs') 

def gpred_filtering(dmrs, gpred_filter=DEFAULT_FILTER, allow_disconnected_dmrs=DEFAULT_ALLOW_DISC):
    """
    Remove general predicate nodes on the filter list from the DMRS.
    :param dmrs_xml: Input DMRS object
    :param gpred_filter: A list of general predicates to filter (as strings)
    :param allow_disconnected_dmrs: Remove gpred nodes even if their removal would result in a disconnected DMRS.
     If DMRS was already disconnected, gpred nodes are removed regardless.
    :return: Output DMRS object
    """

    filterable_nodeids = set()

    # Find general predicate nodes to filter
    for node in dmrs.iter_nodes():
        if node.is_gpred_node and node.pred in gpred_filter:
            filterable_nodeids.add(node.nodeid)

    test_connectedness = not allow_disconnected_dmrs and dmrs.is_connected(ignored_nodeids=filterable_nodeids)

    # If DMRS should remain connected, check that removing filterable nodes will not result in a disconnected DMRS
    if test_connectedness:
        filtered_nodeids = set()
        for nodeid in filterable_nodeids:
            if dmrs.is_connected(removed_nodeids=filtered_nodeids|{nodeid}, ignored_nodeids=filterable_nodeids):
                filtered_nodeids.add(nodeid)

    else:
        filtered_nodeids = filterable_nodeids

    # Remove filtered nodes and their links from the DMRS
    for nodeid in filtered_nodeids:
        dmrs.remove_node(nodeid)

    return dmrs


# If run from the command line, process the given file
if __name__ == '__main__':

    with open(args.input_dmrs, 'r', encoding="utf-8") as fin, open(args.output_dmrs, 'w') as fout:
        content = fin.read().strip()

        for dmrs_string in split_dmrs_string(content):
            dmrs = loads_xml(dmrs_string)
            simplified_dmrs = gpred_filtering(dmrs)
            simplified_dmrs_string = dumps_xml(simplified_dmrs)
            fout.write('{}\n\n'.format(simplified_dmrs_string.decode('utf-8')))
