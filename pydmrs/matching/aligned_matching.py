from pydmrs.core import SortDictDmrs, span_pred_key, abstractSortDictDmrs
from pydmrs.matching.common import are_equal_links


# ------------------------------------------------------------------------
def match_nodes(nodes1, nodes2, excluded=[]):
    """
    :param nodes1: A list of Nodes from the DMRS to be matched, sorted by span_pred_key.
    :param nodes2: A list of Nodes from the DMRS against which we match, sorted by span_pred_key.
    :param excluded: A list of nodeids which should not be used for matching.

    :return: A list of lists of nodeid pairs. The first element in the pair is from small DMRS, the second from the
    larger one. The pairs are listed in reverse span_pred_key order of the corresponding nodes.  Returns [] if no
    match found.
    """
    if not nodes1 or not nodes2:
        return []
    matches = []
    earliest = len(nodes1)
    longest = 0
    for i, node2 in enumerate(nodes2):
        if len(nodes2) - i < longest:  # Not enough nodes left to beat the current longest match.
            break
        if excluded and node2.nodeid in excluded:
            continue
        for j, node1 in enumerate(nodes1):
            if j > earliest:  # To avoid repetition.
                break
            if node1 == node2:
                best_matches = match_nodes(nodes1[j + 1:], nodes2[i + 1:], excluded=excluded)
                if best_matches:
                    for match in best_matches:
                        match.append((node1.nodeid, node2.nodeid))
                else:
                    best_matches = [[(node1.nodeid, node2.nodeid)]]
                earliest = j
                longest = max(longest, len(best_matches[0]))
                matches.extend(best_matches)
    if matches:
        max_len = len(max(matches, key=len))
        return [m for m in matches if len(m) == max_len]
    else:
        return []


def add_quantifier_matches(dmrs1, dmrs2, longest_matches):
    for m in longest_matches:
        q_pairs = []
        for nodeid1, nodeid2 in m:
            try:
                q_link1 = dmrs1.get_in(nodeid1, rargname='RSTR', post='H').pop()
                q_link2 = dmrs2.get_in(nodeid2, rargname='RSTR', post='H').pop()
            except KeyError:
                continue
            if dmrs1[q_link1.start] == dmrs2[q_link2.start]:
                q_pairs.append((q_link1.start, q_link2.start))
        m.extend(q_pairs)


def get_compounds(dmrs, compound_preds):
    compounds = []
    for node in dmrs.iter_nodes():
        if str(node.pred) in compound_preds:
            arg1 = dmrs.get_out_nodes(node.nodeid, rargname='ARG1').pop().nodeid
            arg2 = dmrs.get_out_nodes(node.nodeid, rargname='ARG2').pop().nodeid
            compounds.append({"node": node, "args" : (arg1, arg2)})
    return compounds


def add_compound_matches(small_dmrs, large_dmrs, longest_matches, compound_preds):
    small_compounds = get_compounds(small_dmrs, compound_preds)
    large_compounds = get_compounds(large_dmrs, compound_preds)

    for m in longest_matches:
        cmpd_pairs = []
        for small_cmpd in small_compounds:
            query_arg1 = None
            query_arg2 = None
            for small, large in m:
                if small == small_cmpd['args'][0]:
                    query_arg1 = large
                elif small == small_cmpd['args'][1]:
                    query_arg2 = large
                if query_arg1 and query_arg2:
                    break
            else:
                continue
            for large_cmpd in large_compounds:
                if (query_arg1, query_arg2) == large_cmpd['args']:
                    if small_cmpd['node'] == large_cmpd['node']:
                        cmpd_pairs.append((small_cmpd['node'].nodeid, large_cmpd['node'].nodeid))
        m.extend(cmpd_pairs)



def find_extra_surface_nodeids(nodeids, large_dmrs):
    """ Finds nodeids present in the aligned matched region of the large DMRS,
        but which have no equivalents in the small DMRS.

        :param nodeids Nodeids from the large DMRS which have equivalents in the small one, sorted by span_pred_key of
        their nodes.
        :param large_dmrs The large DMRS.

        :return A list of additional nodeids sharing the span with nodeids but without equivalents in the small DMRS.
    """
    max_cto = large_dmrs[nodeids[-1]].cto
    extra_nodeids = []
    reached_start = False
    reached_end = False
    for i, node in enumerate(large_dmrs.nodes):
        if node.nodeid == nodeids[0]:
            first_overlap_orderid = i
            min_cfrom = node.cfrom
            max_cto = max(max_cto, node.cto)
            while True and first_overlap_orderid > 0:
                prev_node = large_dmrs.nodes[first_overlap_orderid - 1]
                prev_cfrom = prev_node.cfrom
                if prev_cfrom == min_cfrom and prev_node.cto <= max_cto:
                    first_overlap_orderid -= 1
                    extra_nodeids.append(prev_node.nodeid)
                    max_cto = max(max_cto, prev_node.cto)
                else:
                    break
            reached_start = True
        elif not reached_start:
            continue
        elif reached_end and node.cfrom >= max_cto:
            break
        else:
            max_cto = max(max_cto, node.cto)
            if node.nodeid not in nodeids and node.nodeid not in extra_nodeids:
                extra_nodeids.append(node.nodeid)
        if node.nodeid == nodeids[-1]:
            reached_end = True

    return extra_nodeids


def get_links(dmrs, nodeids):
    """
    :param dmrs: A Dmrs object.
    :param nodeids: A list of nodeids.
    :return: A list of all links starting and ending on a node from nodeids.
    """
    links = []
    for nodeid in nodeids:
        node_links = dmrs.get_out(nodeid)
        for link in node_links:
            if link.end in nodeids:
                links.append(link)
    return links


def get_subgraph(dmrs, subgraph_nodeids):
    """ Returns a subgraph of dmrs containing only nodes with subgraph_nodeids and all the links between them.
    :param dmrs: A Dmrs object.
    :param subgraph_nodeids: A list of nodeids.
    :return A SortDictDmrs containing only nodes with subgraph_nodeids and links between them.
    """
    nodes = [dmrs[nodeid] for nodeid in subgraph_nodeids]
    return SortDictDmrs(nodes, links=get_links(dmrs, subgraph_nodeids), node_key=span_pred_key)


# -------------------------------------------------------------------------------

def get_link_diff(small_dmrs, matched_subgraph, matching_nodeids):
    """
    :param small_dmrs A Dmrs which we're matching.
    :param matched_subgraph A Dmrs. A subgraph of the larger DMRS returned as a match for small_dmrs.
    :param matching_nodeids A list of pairs of nodeids. The first nodeid in each pair comes from small_dmrs, the second
    comes from the large dmrs.
    :return three list of links:
        1) links present only in the small dmrs
        2) links present only in the matched subgraph
        3) common links.
    """
    both = []
    small_only = []
    subgraph_only = []
    for small_nodeid, subgraph_nodeid in matching_nodeids:
        if small_nodeid:
            small_links = small_dmrs.get_out(small_nodeid)
            subgraph_links = list(matched_subgraph.get_out(subgraph_nodeid))
            links_flag = [False] * len(subgraph_links)
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
                    subgraph_only.append(subgraph_links[i])
        else:
            subgraph_only.extend(matched_subgraph.get_out(subgraph_nodeid))

    for nodeid in small_dmrs:
        if nodeid not in list(zip(*matching_nodeids))[0]:
            small_only.extend(small_dmrs.get_out(nodeid))

    return small_only, subgraph_only, both


# ------------------------------------------------------------------------------
## IMPORTANT ##
def get_matching_nodeids(small_dmrs, large_dmrs, all_surface=False, large_excluded=None):
    """ Finds matching pairs of nodeids between small_dmrs and large_dmrs. Starts by matching all
        nodes but quantifiers, then matches quantifiers for nouns with matches.
        :param small_dmrs A DMRS object used as a match query,
        :param large_dmrs A DMRS object to be searched for a match.
        :param all_surface If true, include all nodes from the aligned surface region.
                           If false, find only the nodes with equivalents in small_dmrs.
        :param large_excluded The nodeids from the large DMRS to be ignored during matching.

        :return A list of lists of matched nodeid pairs (small_dmrs nodeid, large_dmrs nodeid).
                A list of lists, in case more than one best match found.
    """
    # Convert DMRSs to SortDictDmrs with span_pred_key node if needed.
    if not isinstance(small_dmrs, SortDictDmrs) or (small_dmrs.node_key != span_pred_key):
        small_dmrs = small_dmrs.convert_to(abstractSortDictDmrs(node_key=span_pred_key))
    if not isinstance(large_dmrs, SortDictDmrs) or (large_dmrs.node_key != span_pred_key):
        large_dmrs = large_dmrs.convert_to(abstractSortDictDmrs(node_key=span_pred_key))

    # Filter quantifiers.
    small_no_qs = [n for n in small_dmrs.nodes if not small_dmrs.is_quantifier(n.nodeid)]
    large_no_qs = [n for n in large_dmrs.nodes if not large_dmrs.is_quantifier(n.nodeid)]
    # Filter compound_name and compund predicates.
    filtered_pred = ['compound', 'compound_name']
    filtered_small = [n for n in small_no_qs if str(n.pred) not in filtered_pred]
    filtered_large = [n for n in large_no_qs if str(n.pred) not in filtered_pred]

    longest_matches = match_nodes(filtered_small, filtered_large,
                                  excluded=large_excluded)  # list of lists of nodeid pairs
    add_quantifier_matches(small_dmrs, large_dmrs, longest_matches)
    add_compound_matches(small_dmrs, large_dmrs, longest_matches, filtered_pred)
    max_len = len(max(longest_matches, key=len)) if longest_matches else 0
    longest_matches = [m for m in longest_matches if len(m) == max_len]
    # Returned in reverse span_pred_key order.
    all_matched_nodeids = []
    for match in longest_matches:
        matched_large_nodeids = list(reversed((list(zip(*match))[1])))  # span_pred_key order

        if all_surface:
            extra_overlap_nodeids = find_extra_surface_nodeids(matched_large_nodeids,
                                                               large_dmrs)
            match.extend([(None, nodeid) for nodeid in extra_overlap_nodeids])
        all_matched_nodeids.append(match)

    return all_matched_nodeids


def get_matched_subgraph(matching_nodeids, large_dmrs):
    """
    :param matching_nodeids: A list of pairs of matches nodeids from the small and large dmrs.
    :param large_dmrs: A Dmrs.
    :return: A Dmrs. A subgraph of large_dmrs containing only nodes with nodeids in matching_nodeids.
    """
    present_large_nodeids = list(zip(*matching_nodeids))[1]
    return get_subgraph(large_dmrs, present_large_nodeids)


def get_best_subgraph(nodeid_matches, small_dmrs, large_dmrs):
    best_fscore = 0
    best_score = 0, 0, 0
    best_graphs = []
    for match in nodeid_matches:
        subgraph = get_matched_subgraph(match, large_dmrs)
        score = get_score(small_dmrs, subgraph, match)
        fscore = get_fscore(*score)
        if fscore > best_fscore:
            best_graphs = [subgraph]
            best_fscore = fscore
            best_score = score
        elif fscore == best_fscore:
            best_graphs.append(subgraph)
    return best_graphs, best_score


def get_score(small_dmrs, matched_subgraph, matching_nodeids):
    num_extra_nodes = len([pair for pair in matching_nodeids if pair[0] is None])
    num_matched_nodes = len(matching_nodeids) - num_extra_nodes
    num_missing_nodes = len(
        [nodeid for nodeid in small_dmrs if nodeid not in list(zip(*matching_nodeids))[0]])

    only_small_links, only_subgraph_links, shared_links = get_link_diff(small_dmrs,
                                                                        matched_subgraph,
                                                                        matching_nodeids)
    num_extra_links = len(only_subgraph_links)
    num_missing_links = len(only_small_links)
    num_shared_links = len(shared_links)

    num_correct = num_matched_nodes + num_shared_links
    num_matched = num_correct + num_extra_links + num_extra_nodes
    num_expected = num_correct + num_missing_links + num_missing_nodes

    return num_correct, num_matched, num_expected


def get_fscore(num_correct, num_matched, num_expected):
    precision = num_correct / num_matched if num_matched > 0 else 0
    recall = num_correct / num_expected if num_expected > 0 else 0
    return 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0  # fscore
