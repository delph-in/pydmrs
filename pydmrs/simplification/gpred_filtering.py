def gpred_filtering(dmrs, gpred_filter, allow_disconnected_dmrs=False):
    """
    Remove general predicate nodes on the filter list from the DMRS.
    :param dmrs_xml: Input DMRS object
    :param gpred_filter: A list of general predicates to filter (as strings)
    :param allow_disconnected_dmrs: Remove gpred nodes even if their removal would result in a disconnected DMRS.
     If DMRS was already disconnected, gpred nodes are removed regardless.
    :return: Output DMRS object
    """

    filterable_nodes = set()

    # Find general predicate nodes to filter
    for node in dmrs.iter_nodes():
        if node.is_gpred_node and node.pred.name in gpred_filter:
            filterable_nodes.add(node.nodeid)

    test_connectedness = not allow_disconnected_dmrs and dmrs.is_connected(ignored_nodeids=filterable_nodes)

    # If DMRS should remain connected, check that removing filterable nodes will not result in a disconnected DMRS
    if test_connectedness:
        filtered_node_ids = set()
        for node_id in filterable_nodes:
            if dmrs.is_connected(removed_nodeids=filtered_node_ids | {node_id}, ignored_nodeids=filterable_nodes):
                filtered_node_ids.add(node_id)

    else:
        filtered_node_ids = filterable_nodes

    # Remove filtered nodes and their links from the DMRS
    for node_id in filtered_node_ids:
        dmrs.remove_node(node_id)

    return dmrs
