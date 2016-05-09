import copy
from pydmrs.components import Pred, RealPred, GPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import Link, Node
from pydmrs.matching.exact_matching import dmrs_exact_matching


class AnchorNode(Node):
    """
    A DMRS graph node with an additional anchor id to identify anchor nodes for DMRS mapping.
    """

    def __init__(self, anchor, nodeid, pred, sortinfo=None, carg=None):
        """
        Create a new anchor node instance.
        """
        super().__init__(nodeid=nodeid, pred=pred, sortinfo=sortinfo, carg=carg)
        self.anchor = anchor

    def map(self, dmrs, nodeid):
        """
        Overrides the values of the target node if they are not underspecified in this anchor node.
        :param dmrs Target DMRS graph.
        :param nodeid Target node id.
        """
        node = dmrs[nodeid]
        if self == node or self.is_less_specific(node):
            return
        if isinstance(self.pred, RealPred):
            if isinstance(node.pred, RealPred):
                node.pred = RealPred(node.pred.lemma if self.pred.lemma == '?' else self.pred.lemma, node.pred.pos if self.pred.pos in ('u', '?') else self.pred.pos, node.pred.sense if self.pred.sense in ('unknown', '?') else self.pred.sense)
            else:
                node.pred = copy.deepcopy(self.pred)
        elif isinstance(self.pred, GPred):
            if isinstance(node.pred, GPred):
                node.pred = GPred(node.pred.name if self.pred.name == '?' else self.pred.name)
            else:
                node.pred = copy.deepcopy(self.pred)
        elif not isinstance(self.pred, Pred):
            node.pred = None
        if isinstance(self.sortinfo, EventSortinfo):
            if isinstance(node.sortinfo, EventSortinfo):
                node.sortinfo = EventSortinfo(node.sortinfo.sf if self.sortinfo.sf in ('u', '?') else self.sortinfo.sf, node.sortinfo.tense if self.sortinfo.tense in ('u', '?') else self.sortinfo.tense, node.sortinfo.mood if self.sortinfo.mood in ('u', '?') else self.sortinfo.mood, node.sortinfo.perf if self.sortinfo.perf in ('u', '?') else self.sortinfo.perf, node.sortinfo.prog if self.sortinfo.prog in ('u', '?') else self.sortinfo.prog)
            else:
                node.sortinfo = copy.deepcopy(self.sortinfo)
        elif isinstance(self.sortinfo, InstanceSortinfo):
            if isinstance(node.sortinfo, InstanceSortinfo):
                node.sortinfo = InstanceSortinfo(node.sortinfo.pers if self.sortinfo.pers in ('u', '?') else self.sortinfo.pers, node.sortinfo.num if self.sortinfo.num in ('u', '?') else self.sortinfo.num, node.sortinfo.gend if self.sortinfo.gend in ('u', '?') else self.sortinfo.gend, node.sortinfo.ind if self.sortinfo.ind in ('u', '?') else self.sortinfo.ind, node.sortinfo.pt if self.sortinfo.pt in ('u', '?') else self.sortinfo.pt)
            else:
                node.sortinfo = copy.deepcopy(self.sortinfo)
        elif not isinstance(self.sortinfo, Sortinfo):
            node.sortinfo = None
        if self.carg != '?':
            node.carg = self.carg


class SubgraphNode(AnchorNode):
    """
    A DMRS anchor node which comprises the subgraph attached to it.
    The attached subgraph consists of the nodes which are connected only via this node to the top node of the graph, and would be disconnected if the subgraph node was removed.
    """

    def __init__(self, anchor, nodeid, pred, sortinfo=None, carg=None):
        """
        Create a new subgraph node instance.
        """
        super().__init__(anchor, nodeid, pred, sortinfo=sortinfo, carg=carg)

    def map(self, dmrs, nodeid):
        """
        Overrides the values of the target node if they are not underspecified in this subgraph node, and removes the subgraph attached to it.
        :param dmrs Target DMRS graph (requires the top node specified).
        :param nodeid Target node id.
        """
        assert dmrs.top is not None, 'Top node has to be specified for subgraph node to map.'
        super().map(dmrs, nodeid)
        node = dmrs[nodeid]
        dmrs.remove_node(nodeid)
        dmrs.remove_nodes(dmrs.disconnected_nodeids(start_id=dmrs.top.nodeid))
        dmrs.add_node(node)


def dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=True, iterative=True, all_matches=True, require_connected=True):
    """
    Performs an exact DMRS (sub)graph matching of a (sub)graph against a containing graph.
    :param dmrs DMRS graph to map.
    :param search_dmrs DMRS subgraph to replace.
    :param replace_dmrs DMRS subgraph to replace with.
    :param copy_dmrs True if DMRS graph argument should be copied before being mapped.
    :param iterative True if all possible mappings should be performed iteratively to the same DMRS graph, instead of a separate copy per mapping (iterative=False requires copy_dmrs=True).
    :param all_matches True if all possible matches should be returned, instead of only the first (or None).
    :param require_connected True if mappings resulting in a disconnected DMRS graph should be ignored.
    :return Mapped DMRS graph (resp. a list of graphs in case of iterative=False and all_matches=True)
    """
    assert copy_dmrs or iterative, 'Invalid argument combination.'

    # extract anchor node mapping between search_dmrs and replace_dmrs
    sub_mapping = {}
    for search_node in search_dmrs.iter_nodes():
        if not isinstance(search_node, AnchorNode):
            continue
        for replace_node in replace_dmrs.iter_nodes():
            if not isinstance(replace_node, AnchorNode) or replace_node.anchor != search_node.anchor:
                continue
            sub_mapping[search_node.nodeid] = replace_node.nodeid
            break
        else:
            assert False, 'Un-matched anchor node.'

    # set up variables according to settings
    if iterative:
        result_dmrs = copy.deepcopy(dmrs) if copy_dmrs else dmrs
    else:
        matchings = dmrs_exact_matching(search_dmrs, dmrs)
    if not iterative and all_matches:
        result = []

    # continue while there is a match for search_dmrs
    while True:
        if iterative:
            matchings = dmrs_exact_matching(search_dmrs, result_dmrs)
        else:
            result_dmrs = copy.deepcopy(dmrs) if copy_dmrs else dmrs

        # return mapping(s) if there are no more matches left
        try:
            search_matching = next(matchings)
        except StopIteration:
            if not all_matches:
                return None
            elif iterative:
                return result_dmrs
            else:
                return result

        # remove nodes in the matched search_dmrs if they are no anchor nodes, otherwise perform mapping()
        # mapping() performs the mapping process (with whatever it involves) specific to this node type (e.g. fill underspecified values)
        replace_matching = {}
        for nodeid in search_matching:
            if isinstance(search_dmrs[nodeid], AnchorNode):
                replace_dmrs[sub_mapping[nodeid]].map(result_dmrs, search_matching[nodeid])
                replace_matching[sub_mapping[nodeid]] = search_matching[nodeid]
            elif search_matching[nodeid] is not None:
                result_dmrs.remove_node(search_matching[nodeid])

        # add copies of the non-anchor nodes for the matched replace_dmrs
        for nodeid in replace_dmrs:
            if nodeid in replace_matching:
                continue
            node = copy.deepcopy(replace_dmrs[nodeid])
            node.nodeid = result_dmrs.free_nodeid()
            result_dmrs.add_node(node)
            replace_matching[nodeid] = node.nodeid

        # set top/index if specified in replace_dmrs
        if replace_dmrs.top is not None:
            result_dmrs.top = result_dmrs[replace_matching[replace_dmrs.top.nodeid]]
        if replace_dmrs.index is not None:
            result_dmrs.index = result_dmrs[replace_matching[replace_dmrs.index.nodeid]]

        # remove all links in the matched search_dmrs
        links = []
        matching_values = set(search_matching.values())
        for link in result_dmrs.iter_links():
            if link.start in matching_values and link.end in matching_values:
                links.append(link)
        result_dmrs.remove_links(links)

        # add all links for the matched replace_dmrs
        for link in replace_dmrs.iter_links():
            link = Link(replace_matching[link.start], replace_matching[link.end], link.rargname, link.post)
            result_dmrs.add_link(link)

        # add/return result
        if not require_connected or result_dmrs.is_connected():
            if all_matches and not iterative:
                result.append(result_dmrs)
            elif not all_matches:
                return result_dmrs
