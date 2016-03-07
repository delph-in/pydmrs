from pydmrs.core import DictDmrs
from pydmrs.matching.common import are_equal_nodes, are_equal_links

def sort_nodes(nodes):
    """ Returns a list of nodes sorted by:
        1) cfrom,
        2) cto (decreasing),
        3) pred __str__()."""
    return sorted(sorted(sorted(nodes, key=lambda node: node.pred.__str__()), key = lambda node: node.cto, reverse=True), key = lambda node: node.cfrom)

# Finding the longest node overlap subsequence.
#------------------------------------------------------------------------
class TreeNode(object):
    def __init__(self, id1, id2):
        self.id1 = id1
        self.id2 = id2
        self.depth = 1
        self.children = []

    def __repr__(self):
        return "TreeNode({0}, {1})".format(self.id1, self.id2)

    def add_child(self, child_node):
        self.depth += child_node.depth
        self.children.append(child_node)

    def to_tuple(self):
        return (self.id1, self.id2)

def fill_tree(root, sorted_nodes1, sorted_nodes2):
    """ Builds a tree, starting at root, of matching subsequences between
        sorted_nodes1 and sorted_nodes2. The subsequences match if the order
        of the nodes is preserved and they satisfy are_equal_nodes.

        :param root A TreeNode root of the constructed tree.
        :param sorted_nodes1 A list of nodes (from the smaller DMRS) sorted by sort_nodes.
        :param sorted_nodes2 A list of nodes (from the larger DMRS) sorted by sort_nodes.
    """
    for id1 in range(root.id1+1, len(sorted_nodes1)):
        for id2 in range(root.id2+1, len(sorted_nodes2)):
            if are_equal_nodes(sorted_nodes1[id1], sorted_nodes2[id2]):
                child_node = TreeNode(id1, id2)
                fill_tree(child_node, sorted_nodes1, sorted_nodes2)
                root.add_child(child_node)

def find_treepaths(root, treepaths):
    """ Returns the longest paths through the tree starting at root.
        :param root A TreeNode root of a tree.
        :param treepaths A list of lists of TreeNodes partcipating in the longest path
                         through the root tree. A list of lists, in case more than one longest path found.
        :return Updated treepaths.
    """
    treepaths.append(root)# possible that more than one match of the same length
    if root.children:
        path_children = max(root.children, key = lambda node: node.depth) # pick the deepest child tree(s)
        if isinstance(path_children, TreeNode):
            find_treepaths(path_children, treepaths)
        else: # more than one child tree with the max depth
            num_paths = len(path_children)
            treepaths = [treepaths[:]]*num_paths # copies, not references
            for i in range(0, num_paths):
                find_treepaths(path_children[i], treepaths[i])
    return treepaths

def find_longest_matches(sorted_nodes1, sorted_nodes2):
    """ Returns the longest common subsequences between sorted_nodes1 and
        sorted_nodes2.
        :param sorted_nodes1 A list of nodes (from the smaller DMRS) sorted by sort_nodes.
        :param sorted_nodes2 A list of nodes (from the larger DMRS) sorted by sort_nodes.

        :return A list of lists of tuples (index in sorted_nodes1, index in sorted_nodes2).
                Each list is a longest matching subsequence between sorted_ndoes1
                and sorted_nodes2."""
    root = TreeNode(-1,-1)
    fill_tree(root, sorted_nodes1, sorted_nodes2)
    match = find_treepaths(root, [])

    # Remove (-1, -1) superroot.
    if isinstance(match[0], list): # More than one match of the same length.
        res = []
        for m in match:
            res.append([node.to_tuple() for node in m[1:]])
        return res
    else:
        return [[node.to_tuple() for node in match[1:]]]

def get_matched_nodeids_from_orderids(sorted_small_nodes, sorted_large_nodes, matched_orderids):
    """ Converts matched pairs of indices in sorted_small_nodes and sorted_large_nodes
        into matched pairs of nodeids."""
    orderid2nodeid_func = lambda order_pair: (sorted_small_nodes[order_pair[0]].nodeid, sorted_large_nodes[order_pair[1]].nodeid)
    return list(map(orderid2nodeid_func, matched_orderids))

def find_extra_surface_nodeids(orderids, sorted_large_nodes):
    """ Finds nodeids present in the aligned matched region of the large DMRS,
        but which have no equivalents in the small DMRS.

        :param orderids Indices of sorted_large_nodes corresponding to matched nodes.
        :param sorted_large_nodes A list of nodes of the large dmrs sorted by sort_nodes.

        :return A list of nodeids.
    """
    extra_nodeids = []
    first_overlap_orderid = orderids[0]
    min_cfrom = sorted_nodes[first_overlap_orderid].cfrom

    # Check if any earlier nodes also in the region.
    while True:
        prev_cfrom = sorted_nodes[first_overlap_orderid-1].cfrom
        if prev_cfrom == min_cfrom:
            first_overlap_orderid -= 1
            extra_nodeids.append(sorted_nodes[first_overlap_orderid].nodeid)
        else:
            break

    # Find the last node in the region.
    last_overlap_orderid = matched_orderids[-1]
    max_cto = sorted_nodes[last_overlap_orderid].cto
    for i in range(first_overlap_orderid, len(sorted_nodes)):
        if sorted_nodes[i].cfrom > max_cto:
            break
        else:
            if i not in orderids:
                extra_nodeids.append(sorted_nodes[i].nodeid)
            cto = sorted_nodes[i].cto
            if cto >= max_cto:
                max_cto = cto
                if i > last_overlap_orderid:
                    last_overlap_orderid = i

    return extra_nodeids

def get_subgraph(dmrs, subgraph_nodeids):
    """ Returns a subgraph of dmrs containing only nodes with subgraph_nodeids
        and all the links between them.
    """
    links = []
    for nodeid in subgraph_nodeids:
        node_links = dmrs.get_out(nodeid)
        for link in node_links:
            if link.end in subgraph_nodeids:
                links.append(link)
    nodes = [dmrs[nodeid] for nodeid in subgraph_nodeids]
    return DictDmrs(nodes, links)

#-------------------------------------------------------------------------------

def get_link_diff(small_dmrs, matched_subgraph, matching_nodeids):
    """ Returns three list of links:
        1) links present only in the small dmrs
        2) links present only in the matched subgraph
        3) common links.
    """
    both = []
    small_only = []
    subgraph_only= []
    for small_nodeid, subgraph_nodeid in matching_nodeids:
        if small_nodeid:
            small_links = small_dmrs.get_out(small_nodeid)
            subgraph_links = list(matched_subgraph.get_out(subgraph_nodeid))
            links_flag = [False]*len(subgraph_links)
            for link1 in small_links:
                match_found = False
                for link2 in subgraph_links:
                    if are_equal_links(link1, link2, small_dmrs, matched_subgraph):
                        both.append(link1)
                        match_found = True
                        links_flag[subgraph_links.index(link2)] = True
                        break
                if not match_found:
                    small_only.append(link1)
            for i in range(0, len(subgraph_links)):
                if not links_flag[i]:
                    subgraph_only.append(links[i])
        else:
            subgraph_only.extend(matched_subgraph.get_out(subgraph_nodeid))

    for nodeid in small_dmrs:
        if nodeid not in list(zip(*matching_nodeids))[0]:
            small_only.extend(small_dmrs.get_out(nodeid))

    return small_only, subgraph_only, both

def get_node_diff(small_dmrs, matched_subgraph, matching_nodeids):
    """ Returns three list of nodeids:
        1) nodes present only in the small_dmrs
        2) nodes present only in the matched_subgraph
        3) nodes from small_dmrs which have a matched_subgraph euivalent.
    """

    small_only = []
    subgraph_only = []
    both = []

    # Find missing sub_nodes
    for pair in matching_nodeids:
        if pair[0] is None:
            subgraph_only.append(matched_subgraph[pair[1]])
        else:
            both.append(small_dmrs[pair[0]])

    for nodeid in small_dmrs:
        if nodeid not in both:
            small_only.append(small_dmrs[nodeid])

    return small_only, subgraph_only, both

#------------------------------------------------------------------------------
## IMPORTANT ##
def get_matching_nodeids(small_dmrs, large_dmrs, all_surface=False):
    """ Finds matching pairs of nodeids between small_dmrs and large_dmrs.
        :param small_dmrs A DMRS object used as a match query,
        :param large_dmrs A DMRS object to be searched for a match.
        :param all_surface If true, include all nodes from the aligned surface region.
                           If false, find only the nodes with equivalents in small_dmrs.

        :return A list of lists of matched nodeid pairs (small_dmrs nodeid, large_dmrs nodeid).
                A list of lists, in case more than one best match found.
    """
    sorted_small_nodes = sort_nodes(small_dmrs.nodes)
    sorted_large_nodes = sort_nodes(large_dmrs.nodes)

    longest_matches = find_longest_matches(sorted_small_nodes, sorted_large_nodes) # list (of lists) of tuples (id_from_sub, id)

    all_matched_nodeids = []
    for match in longest_matches:
        matched_large_orderids = list(zip(*match))[1] # [(order ids from small dmrs), (order ids from the
        paired_nodeids = get_matched_nodeids_from_orderids(sorted_small_nodes, sorted_large_nodes, match)
        if all_surface:
            extra_overlap_nodeids = find_extra_surface_overlap(matched_large_nodeids, sorted_large_nodes)
            paired_nodeids.extend([(None, nodeid) for nodeid in extra_overlap_nodeids])
        all_matched_nodeids.append(paired_nodeids)

    return all_matched_nodeids

def get_matched_subgraph(matching_nodeids, large_dmrs):
    present_large_nodeids = list(zip(*matching_nodeids))[1]
    return get_subgraph(large_dmrs, present_large_nodeids)

def get_fscore(small_dmrs, matched_subgraph, matching_nodeids):
    num_extra_nodes = len([pair for pair in matching_nodeids if pair[0] is None])
    num_matched_nodes = len(matching_nodeids)-num_extra_nodes
    num_missing_nodes = len([nodeid for nodeid in small_dmrs if nodeid not in list(zip(*matching_nodeids))[0]])

    only_small_links, only_subgraph_links, shared_links = get_link_diff(small_dmrs, matched_subgraph, matching_nodeids)
    num_extra_links = len(only_subgraph_links)
    num_missing_links = len(only_small_links)
    num_shared_links = len(shared_links)

    num_matched = num_matched_nodes + num_shared_links
    num_selected = num_matched + num_extra_links + num_extra_nodes
    num_relevant = num_matched + num_missing_links + num_missing_nodes

    precision = num_matched/num_selected
    recall = num_matched/num_relevant

    return 2*precision*recall/(precision+recall) # f_score
