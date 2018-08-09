from itertools import product, chain

from pydmrs.components import RealPred
from pydmrs.core import DictDmrs
from pydmrs.matching.common import are_equal_nodes, are_equal_links
from pydmrs.matching.match_evaluation import get_fscore


class Match(object):
    """ A mapping between two DMRS objects.
        The nodeid_pairs is a list of nodeid tuples (nodeid1, nodeid2), where
        nodeid1 and nodeid2 come from different DMRS.
        The link_pairs is the link equivalent of the nodeid_pairs.
    """

    def __init__(self, nodeid_pairs=[], link_pairs=[]):
        self.nodeid_pairs = nodeid_pairs
        self.link_pairs = link_pairs

    def __str__(self):
        return "Nodes:{}; Links:{}".format(self.nodeid_pairs, self.link_pairs)

    def __len__(self):
        return len(self.nodeid_pairs) + len(self.link_pairs)

    def add(self, match):
        """Combines self with match, resolving any conflicts in favour of self."""
        if self.is_compatible(match):
            self.nodeid_pairs.extend(match.nodeid_pairs)
            self.link_pairs.extend(match.link_pairs)
        else:
            nodesA, nodesB = map(list, zip(*self.nodeid_pairs))
            for node_pair in match.nodeid_pairs:
                if node_pair[0] not in nodesA and node_pair[1] not in nodesB:
                    self.nodeid_pairs.append(node_pair)
                    nodesA.append(node_pair[0])
                    nodesB.append(node_pair[1])

            linksA, linksB = map(set, zip(*self.link_pairs))
            for link1, link2 in match.link_pairs:
                if link1 not in linksA and link2 not in linksB:
                    if link1.start in nodesA and link1.end in nodesA:
                        if link2.start in nodesB and link2.end in nodesB:
                            self.link_pairs.append((link1, link2))

    def is_compatible(self, match2):
        """ Checks if two matches are possible simultaneously. Two matches are conflicting
            if they pair nodes differently, e.g. (10001, 10003) in self and
            (10001, 10005) in match2.
            :param match2 Another Match object.
            :return True/False
        """
        if len(self) == 0 or len(match2) == 0:
            return True
        nodeA_set1, nodeA_set2 = map(set, zip(*self.nodeid_pairs))
        nodeB_set1, nodeB_set2 = map(set, zip(*match2.nodeid_pairs))
        if nodeA_set1.isdisjoint(nodeB_set1) and nodeA_set2.isdisjoint(nodeB_set2):
            return True
        else:
            return False


# ------------------------------------------------------------------------------
def group_same_nodes(nodes):
    """ Groups nodeids of equivalent nodes into sublists, using are_equal_nodes
        as the equivalency criterion.

        :param nodes A list of nodes.
        :return A list of tuples (pred, id list) sorted by pred. The pred is
                the shared predicate of the group; the id_list is a list of
                nodeids of equivalent nodes.
    """
    grouped_nodes = []
    group_node_type = None
    current_group = []
    sorted_nodes = sorted(nodes, key=lambda n: str(n.pred))
    for node in sorted_nodes:
        if not group_node_type:
            group_node_type = node
            current_group.append(node.nodeid)
        elif are_equal_nodes(node, group_node_type):
            current_group.append(node.nodeid)
        else:
            grouped_nodes.append((group_node_type.pred, current_group))
            current_group = [node.nodeid]
            group_node_type = node
    grouped_nodes.append((group_node_type.pred, current_group))
    return grouped_nodes


def pair_same_node_groups(dmrs1, dmrs2):
    """ Finds which nodes in dmrs1 are equivalent to which nodes in dmrs2.
        :param dmrs1 A DMRS object. For matching, the small dmrs.
        :param dmrs2 A DMRS object. For matching, the large dmrs.
        :return A list of tuples (pred, nodes from dmrs1, nodes from dmrs2). All
                nodes in nodes from dmrs1 and nodes form dmrs2 are quivalent.
                The pred is their common predicate. The list of tuples is sorted
                 by pred.
    """
    grouped_nodes1 = group_same_nodes(dmrs1.nodes)
    grouped_nodes2 = group_same_nodes(dmrs2.nodes)
    grouped_nodes = []
    i = 0
    j = 0
    while i < len(grouped_nodes1) and j < len(grouped_nodes2):
        pred1, group1 = grouped_nodes1[i]
        pred2, group2 = grouped_nodes2[j]
        if pred1 == pred2 and are_equal_nodes(dmrs1[group1[0]], dmrs2[group2[0]]):
            grouped_nodes.append((pred1, group1, group2))
            i += 1
            j += 1
        else:
            if str(pred1) > str(pred2):
                j += 1
            else:
                i += 1
    return grouped_nodes


def find_match(start_id1, start_id2, dmrs1, dmrs2, matched_nodes, matched_links):
    """ Finds a match between dmrs1 and dmrs2.
        :param dmrs1 A DMRS object. For matching, the small dmrs.
        :param dmrs2 A DMRS object. For matching, the large dmrs.
        :param start_id1 A nodeid of a node from dmrs1 from which the graph traversal should be started.
        :param start_id2 A nodeid of a node from dmrs2 from which the graph traversal should be started.
        :param matched_nodes Nodes matched so far during the graph traversal
                             Gets updated during recursion. Use an empty list for the top call.
        :param matched_links Link matched so far during the graph traversal.
                            Gets updated during recursion. Use an empty list for the top call.

        The two start nodes should be equivalent by are_equal_nodes criterion.

        The function finds any links shared by the two start nodes (equivalent
        according to are"equal_links) and follows them. The pairs of nodes at
        other end of the links are added to a queue. Then the function calls
        itself recursively with the queued pairs of nodes as the start nodes.
        The recursion stops when no shared links are found and the queue is empty.

        :return A Match composed of updated matched_nodes, matched_links.
    """
    assert (are_equal_nodes(dmrs1[start_id1], dmrs2[start_id2]))
    matched_nodes.append((start_id1, start_id2))

    node_queue = []

    links1 = dmrs1.get_out(start_id1)
    links1.update(dmrs1.get_in(start_id1))
    links1.update(dmrs1.get_eq(start_id1))
    links2 = dmrs2.get_out(start_id2)
    links2.update(dmrs2.get_in(start_id2))
    links2.update(dmrs2.get_eq(start_id2))
    for link1 in links1:
        if link1 not in [pair[0] for pair in matched_links]:
            for link2 in links2:
                if link2 not in [pair[1] for pair in matched_links]:
                    if are_equal_links(link1, link2, dmrs1, dmrs2):
                        matched_links.append((link1, link2))
                        paired1 = link1.start if link1.end == start_id1 else link1.end
                        paired2 = link2.start if link2.end == start_id2 else link2.end
                        node_queue.append((paired1, paired2))
                        break

    for nodeid1, nodeid2 in node_queue:
        if (nodeid1, nodeid2) not in matched_nodes:
            find_match(nodeid1, nodeid2, dmrs1, dmrs2, matched_nodes, matched_links)
    return Match(matched_nodes, matched_links)


def find_all_matches(dmrs1, dmrs2):
    """ Finds all regions with potential matches between two DMRS graphs.
        :param dmrs1 A DMRS object. For matching, the small dmrs.
        :param dmrs2 A DMRS object. For matching, the large dmrs.

        The function initiates a find_match top call and repeats it until all
        possible pairings are explored. GPreds and quantifiers 'a' and 'the'
        are not allowed as the start ndoes of find_match to narrow down the search
        space.

        :return A list of Match objects.
        """
    node_pairings = pair_same_node_groups(dmrs1, dmrs2)
    matches = []
    checked_node_pairs = []

    # Sort pairs so that the ones with fewer matching combination are considered first.
    # Exclude GPreds and some quantifiers from the pool of start nodes.
    filter_func = lambda pairing: isinstance(pairing[0], RealPred) and pairing[0].lemma not in ['a',
                                                                                                'the']
    filtered_pairings = filter(filter_func, node_pairings)
    sorted_pairings = sorted(filtered_pairings,
                             key=lambda pairing: len(pairing[1]) * len(pairing[2]))

    for pred, group1, group2 in sorted_pairings:
        all_pairs = product(group1, group2)
        for pair in all_pairs:
            if pair not in checked_node_pairs:
                match = find_match(pair[0], pair[1], dmrs1, dmrs2, [], [])
                checked_node_pairs.extend(match.nodeid_pairs)
                matches.append(match)
    return matches  # (matched_nodes, matched_links)


def group_compatible_matches(matches):
    """ Groups matches into compatible sets of indices of non-conflicting matches.
        Indices are given by the positions in the matches list.
        :param matches A list of Matches.

        :return A list of sets of integers. Each set is unique and contains matches indices
                of compatible Matches.
    """
    are_all_clashes = True
    clash_pairs = []
    for i in range(len(matches)):
        for j in range(i + 1, len(matches)):
            if i != j:
                if matches[i].is_compatible(matches[j]):
                    are_all_clashes = False
                else:
                    clash_pairs.append((i, j))
                    clash_pairs.append((j, i))

    combinations = [{i} for i in range(len(matches))]
    if are_all_clashes:
        return combinations

    for i in range(len(matches)):
        for comb in combinations:
            if i not in comb:
                if comb.union({i}) in combinations:
                    combinations.remove(comb)
                    break
                clash = False
                for match_id in comb:
                    if (i, match_id) in clash_pairs:
                        clash = True
                        break
                if not clash:
                    comb.add(i)
    return combinations  # list of sets


def find_biggest_disjoint_matches(matches):
    """ Finds collections of compatible matches which maximize the number of
        elements matches. Returns a list in case more than one combination scores
        the highest.
        :param matches A list of Matches.
        :return A list of tuples (group, Match, where group is a set of matches
                indices (see group_compatible_matches) and the Match combines
                all the Matches in the group.
    """
    compatible_groups = group_compatible_matches(matches)
    best_score = 0
    best_groups = None
    for group in compatible_groups:
        group_score = sum(len(matches[i]) for i in group)
        if group_score > best_score:
            best_score = group_score
            best_groups = [group]
        elif group_score == best_score:
            best_groups.append(group)

    full_matches = []
    for group in best_groups:
        nodes = list(chain(*[matches[i].nodeid_pairs for i in group]))
        links = list(chain(*[matches[i].link_pairs for i in group]))
        full_matches.append((group, Match(nodes, links)))
    return full_matches


# -------------------------------------------------------------------------------\
# IMPORTANT
def find_best_matches(small_dmrs, large_dmrs):
    """ Finds the best matches between two DMRS (in case more the one reached
        the same score).
        :param small_dmrs A DMRS object.
        :param large_dmrs A DMRS object.

        :return A list of Matches.
    """
    matches = find_all_matches(small_dmrs, large_dmrs)
    if not matches:
        return None
    else:
        if len(matches) == 1:
            return matches

        best_combinations = []
        indexed_best_combined_matches = find_biggest_disjoint_matches(matches)
        for index, match in indexed_best_combined_matches:
            leftovers = [matches[i] for i in range(len(matches)) if i not in index]
            for extra_match in leftovers:
                match.add(extra_match)
            best_combinations.append(match)
        return best_combinations


def get_matched_subgraph(large_dmrs, match):
    """ Returns the subgraph of large_dmrs described by match.
        :param large_dmrs A DMRS object in which the match was found.
        :param match A Match object.

        :return A DMRS object containing only the matched elements from large_dmrs.
                The graph can be disconnected.
    """
    links = list(zip(*match.link_pairs))[1]
    nodeids = list(zip(*match.nodeid_pairs))[1]
    nodes = [large_dmrs[nodeid] for nodeid in nodeids]
    return DictDmrs(nodes, links)
