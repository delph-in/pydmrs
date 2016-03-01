

def gpred_filtering(dmrs, gpred_filter, allow_disconnected_dmrs=False):
    """
    Remove general predicate nodes on the filter list from the DMRS.
    :param dmrs_xml: Input DMRS object
    :param gpred_filters: A list of general predicates to filter
    :param allow_disconnected_dmrs: Remove gpred nodes even if their removal would result in a disconnected DMRS.
     If DMRS was already disconnected, gpred nodes are removed regardless.
    :return: Output DMRS object
    """

    filterable_nodes = set()

    # Find general predicate nodes to filter
    for node in dmrs.iter_nodes():
        if node.is_gpred_node and node.pred.name in gpred_filter:
            filterable_nodes.add(node.nodeid)

    test_connectedness = not allow_disconnected_dmrs and is_dmrs_connected(dmrs, ignored_nodes=filterable_nodes)

    # If DMRS should remain connected, check that removing filterable nodes will not result in a disconnected DMRS
    if test_connectedness:
        filtered_node_ids = set()
        for node_id in filterable_nodes:
            if is_dmrs_connected(dmrs, removed_nodes=filtered_node_ids | {node_id}, ignored_nodes=filterable_nodes):
                filtered_node_ids.add(node_id)

    else:
        filtered_node_ids = filterable_nodes

    # Remove filtered nodes and their links from the DMRS
    for node_id in filtered_node_ids:
        dmrs.remove_node(node_id)

    return dmrs


def is_dmrs_connected(dmrs, removed_nodes=frozenset(), ignored_nodes=frozenset()):
    """
    Determine if a DMRS graph is connected.
    :param dmrs: DMRS object
    :param removed_nodes: Set of node ids that should be considered as already removed.
     This is to prevent the need for excessive copying of DMRS graphs for hypothetical node removals.
    :param ignored_nodes: Set of node ids that should not be considered as disconnected if found as such.
     This is to prevent nodes that are going to be filtered out later from affecting results of connectivity test.
    :return: True if DMRS is connected, otherwise False.
    """

    disconnected_nodes = disconnected_node_bfs(dmrs, removed_nodes=removed_nodes)

    return len(disconnected_nodes - ignored_nodes) == 0


def disconnected_node_bfs(dmrs, removed_nodes=frozenset(), num_max_iterations=100):
    """
    Breadth-first search of the DMRS for disconnected nodes.
    :param dmrs: DMRS object
    :param removed_nodes: Set of node ids that should be considered as already removed.
     This is to prevent the need for excessive copying of DMRS graphs for hypothetical node removals.
    :param num_max_iterations: Maximum number of iterations to run the BFS for. This is to prevent infinite loops.
    :return: Set of disconnected node id strings
    """

    # Initialize the set of node that have not been visited yet
    unvisited_nodes = {node.nodeid for node in dmrs.iter_nodes()} - removed_nodes

    if len(unvisited_nodes) == 0:
        return unvisited_nodes

    # Select a random starting node to visit
    start_node_id = unvisited_nodes.pop()

    # Start the explore set with nodes adjacent to the starting node
    explore_set = get_adjacent_node_ids(dmrs, start_node_id) - removed_nodes

    # Iteratively visit nodes in the explore set and grow new explore set from visited adjacent nodes
    # Exit the loop when no new adjacent nodes can be visited or num_max_iterations is reached
    current_iter = 0
    while explore_set:

        if current_iter >= num_max_iterations:
            break

        new_explore_set = set()

        # Visit all nodes on the explore list
        for node_id in explore_set:
            unvisited_nodes.remove(node_id)
            adjacent_node_ids = get_adjacent_node_ids(dmrs, node_id) - removed_nodes
            new_explore_set.update(adjacent_node_ids)

        # Explore set for the next iteration are the current explore set's adjacent nodes that have not been visited yet
        explore_set = new_explore_set & unvisited_nodes
        current_iter += 1

    return unvisited_nodes


def get_adjacent_node_ids(dmrs, node_id):
    """
    Retrieve adjacent node ids (regardless of link direction) from the dmrs for node_id
    :param dmrs: DMRS object
    :param node_id: Node id string
    :return: Set of adjacent node id strings
    """

    return {link.end for link in dmrs.get_out(node_id, itr=True)} | \
           {link.start for link in dmrs.get_in(node_id, itr=True)}
