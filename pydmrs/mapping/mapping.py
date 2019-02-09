import copy
from pydmrs._exceptions import PydmrsError
from pydmrs.components import Pred, RealPred, GPred, Sortinfo, EventSortinfo, InstanceSortinfo
from pydmrs.core import Link, Node
from pydmrs.matching.exact_matching import dmrs_exact_matching


class AnchorNode(Node):
    """
    A DMRS graph node with an additional anchor id to identify anchor nodes for DMRS mapping.
    """

    def __init__(self, anchors, *args, **kwargs):
        """
        Create a new anchor node instance.
        """
        super(AnchorNode, self).__init__(*args, **kwargs)
        self.anchors = anchors
        self.required = True
        self.requires_target = True

    def before_map(self, dmrs, nodeid):
        """
        Is applied before the target node is mapped.
        :param dmrs Target DMRS graph.
        :param nodeid Target node id.
        """
        pass

    def after_map(self, dmrs, nodeid):
        """
        Is applied after the target node is mapped.
        :param dmrs Target DMRS graph.
        :param nodeid Target node id.
        """
        pass

    def map(self, dmrs, nodeid, hierarchy=None):
        """
        Overrides the values of the target node if they are not underspecified in this anchor node.
        :param dmrs Target DMRS graph.
        :param nodeid Target node id.
        :param hierarchy: An optional predicate hierarchy.
        """
        node = dmrs[nodeid]

        if self == node or self.is_less_specific(node, hierarchy=hierarchy):
            return

        if self.pred == node.pred or self.pred.is_less_specific(node.pred, hierarchy=hierarchy):
            pass
        elif isinstance(self.pred, RealPred):
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

        if self.sortinfo == node.sortinfo or self.sortinfo.is_less_specific(node.sortinfo):
            pass
        elif isinstance(node.sortinfo, self.sortinfo.__class__):
            node.sortinfo = self.sortinfo.__class__(**{feature: node.sortinfo[feature] if self.sortinfo[feature] in ('u', '?') else self.sortinfo[feature] for feature in self.sortinfo.features})
        else:
            node.sortinfo = copy.deepcopy(self.sortinfo)
        # elif isinstance(self.sortinfo, EventSortinfo):
        #     if isinstance(node.sortinfo, EventSortinfo):
        #         node.sortinfo = EventSortinfo(node.sortinfo.sf if self.sortinfo.sf in ('u', '?') else self.sortinfo.sf, node.sortinfo.tense if self.sortinfo.tense in ('u', '?') else self.sortinfo.tense, node.sortinfo.mood if self.sortinfo.mood in ('u', '?') else self.sortinfo.mood, node.sortinfo.perf if self.sortinfo.perf in ('u', '?') else self.sortinfo.perf, node.sortinfo.prog if self.sortinfo.prog in ('u', '?') else self.sortinfo.prog)
        #     else:
        #         node.sortinfo = copy.deepcopy(self.sortinfo)
        # elif isinstance(self.sortinfo, InstanceSortinfo):
        #     if isinstance(node.sortinfo, InstanceSortinfo):
        #         node.sortinfo = InstanceSortinfo(node.sortinfo.pers if self.sortinfo.pers in ('u', '?') else self.sortinfo.pers, node.sortinfo.num if self.sortinfo.num in ('u', '?') else self.sortinfo.num, node.sortinfo.gend if self.sortinfo.gend in ('u', '?') else self.sortinfo.gend, node.sortinfo.ind if self.sortinfo.ind in ('u', '?') else self.sortinfo.ind, node.sortinfo.pt if self.sortinfo.pt in ('u', '?') else self.sortinfo.pt)
        #     else:
        # elif not isinstance(self.sortinfo, Sortinfo):
        #     node.sortinfo = None

        if self.carg != '?':
            node.carg = self.carg

    def unify(self, other, hierarchy=None):
        """
        Unify nodes.
        :param other: The node to unify with.
        :param hierarchy: An optional predicate hierarchy.
        """
        hierarchy = hierarchy or dict()
        if (
            type(self.pred) is RealPred and
            type(other.pred) is RealPred and
            (self.pred.lemma == other.pred.lemma or self.pred.lemma == '?' or other.pred.lemma == '?') and
            (self.pred.pos == other.pred.pos or self.pred.pos in ('u', '?') or other.pred.pos in ('u', '?')) and
            (self.pred.sense == other.pred.sense or self.pred.sense in ('unknown', '?') or other.pred.sense in ('unknown', '?'))
        ):
            # RealPred and predicate values are either equal or underspecified
            lemma = other.pred.lemma if self.pred.lemma == '?' else self.pred.lemma
            pos = other.pred.pos if self.pred.pos in ('u', '?') else self.pred.pos
            sense = other.pred.sense if self.pred.sense in ('unknown', '?') else self.pred.sense
            self.pred = RealPred(lemma, pos, sense)
        elif (
            type(self.pred) is GPred and
            type(other.pred) is GPred and
            (self.pred.name == other.pred.name or self.pred.name == '?' or other.pred.name == '?')
        ):
            # GPred and predicate values are either equal or underspecified
            name = other.pred.name if self.pred.name == '?' else self.pred.name
            self.pred = GPred(name)
        elif type(self.pred) is Pred or str(other.pred) in hierarchy.get(str(self.pred), ()):
            # predicate is underspecified, or predicate is more general according to the hierarchy
            self.pred = other.pred
        elif type(other.pred) is Pred or str(self.pred) in hierarchy.get(str(other.pred), ()):
            # other is underspecified, or predicate is more specific according to the hierarchy
            pass
        else:
            raise PydmrsError("Node predicates cannot be unified: {}, {}".format(self.pred, other.pred))

        if self.sortinfo is not None and type(self.sortinfo) is not Sortinfo and isinstance(other.sortinfo, type(self.sortinfo)) and all((self.sortinfo[key] == other.sortinfo[key]) or (self.sortinfo[key] in ('u', '?')) or (other.sortinfo[key] in ('u', '?')) for key in self.sortinfo.features):
            # same sortinfo type and values are either equal or underspecified
            self.sortinfo = type(self.sortinfo)(*(other.sortinfo[key] if self.sortinfo[key] in ('u', '?') else self.sortinfo[key] for key in self.sortinfo.features))
        elif type(self.sortinfo) is Sortinfo and isinstance(other.sortinfo, Sortinfo):
            # sortinfo is underspecified
            self.sortinfo = other.sortinfo
        elif type(other.sortinfo) is Sortinfo and isinstance(self.sortinfo, Sortinfo):
            # other is underspecified
            pass
        elif self.sortinfo is None and other.sortinfo is None:
            pass
        else:
            raise PydmrsError("Node sortinfos cannot be unified: {}, {}".format(self.sortinfo, other.sortinfo))

        if self.carg == other.carg or other.carg == '?':
            # same carg, or other is underspecified
            pass
        elif self.carg == '?':
            # carg is underspecified
            self.carg = other.carg
        else:
            raise PydmrsError("Node cargs cannot be unified: {}, {}".format(self.carg, other.carg))


class SubgraphNode(AnchorNode):
    """
    A DMRS anchor node which comprises the subgraph attached to it.
    The attached subgraph consists of the nodes which are connected only via this node to the top node of the graph, and would be disconnected if the subgraph node was removed.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new subgraph node instance.
        """
        super(SubgraphNode, self).__init__(*args, **kwargs)
        self.requires_target = False

    def before_map(self, dmrs, nodeid):
        """
        Removes the subgraph attached to the target node.
        :param dmrs Target DMRS graph (requires the top node specified).
        :param nodeid Target node id.
        """
        assert dmrs.top is not None, 'Top node has to be specified for subgraph node to map.'
        node = dmrs[nodeid]
        dmrs.remove_node(nodeid)
        dmrs.remove_nodes(dmrs.disconnected_nodeids())
        dmrs.add_node(node)


class OptionalNode(AnchorNode):
    """
    A DMRS anchor node which is not required.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new optional node instance.
        """
        super(OptionalNode, self).__init__(*args, **kwargs)
        self.required = False
        self.requires_target = False


def dmrs_mapping(dmrs, search_dmrs, replace_dmrs, equalities=(), hierarchy=None, copy_dmrs=True, iterative=True, all_matches=True, match_top_index=True, require_connected=True, max_matches=100):
    """
    Performs an exact DMRS (sub)graph matching of a (sub)graph against a containing graph.
    :param dmrs DMRS graph to map.
    :param search_dmrs DMRS subgraph to replace.
    :param replace_dmrs DMRS subgraph to replace with.
    :param equalities
    :param hierarchy An optional predicate hierarchy.
    :param copy_dmrs True if DMRS graph argument should be copied before being mapped.
    :param iterative True if all possible mappings should be performed iteratively to the same DMRS graph, instead of a separate copy per mapping (iterative=False requires copy_dmrs=True).
    :param all_matches True if all possible matches should be returned, instead of only the first (or None).
    :param match_top_index True if top and index should be distinguished.
    :param require_connected True if mappings resulting in a disconnected DMRS graph should be ignored.
    :param max_matches: Maximum number of matches.
    :return Mapped DMRS graph (resp. a list of graphs in case of iterative=False and all_matches=True)
    """
    assert copy_dmrs or iterative, 'Invalid argument combination.'

    # extract anchor node mapping between search_dmrs and replace_dmrs
    sub_mapping = {}
    optional_nodeids = []
    for search_node in search_dmrs.iter_nodes():
        if not isinstance(search_node, AnchorNode):
            continue
        if not search_node.required:
            optional_nodeids.append(search_node.nodeid)
        for replace_node in replace_dmrs.iter_nodes():
            if not isinstance(replace_node, AnchorNode) or all(anchor not in replace_node.anchors for anchor in search_node.anchors):
                continue
            assert search_node.nodeid not in sub_mapping, 'Node matches multiple nodes.' + str(search_node)
            sub_mapping[search_node.nodeid] = replace_node.nodeid
        if search_node.nodeid not in sub_mapping:
            assert not search_node.requires_target, 'Un-matched anchor node.'

    # set up variables according to settings
    if iterative:
        result_dmrs = copy.deepcopy(dmrs) if copy_dmrs else dmrs
        # matchings = dmrs_exact_matching(search_dmrs, dmrs, optional_nodeids=optional_nodeids, equalities=equalities, hierarchy=hierarchy, match_top_index=match_top_index)
    else:
        matchings = dmrs_exact_matching(search_dmrs, dmrs, optional_nodeids=optional_nodeids, equalities=equalities, hierarchy=hierarchy, match_top_index=match_top_index)
    if not iterative and all_matches:
        result = []

    # continue while there is a match for search_dmrs
    count = 0
    last_matching = None
    for _ in range(max_matches):
        if iterative:
            matchings = dmrs_exact_matching(search_dmrs, result_dmrs, optional_nodeids=optional_nodeids, equalities=equalities, hierarchy=hierarchy, match_top_index=match_top_index)
        else:
            result_dmrs = copy.deepcopy(dmrs) if copy_dmrs else dmrs

        # return mapping(s) if there are no more matches left
        try:
            search_matching = next(matchings)
            while last_matching is not None and search_matching == last_matching:
                search_matching = next(matchings)
            count += 1
            last_matching = search_matching
        except StopIteration:
            if not all_matches:
                if copy_dmrs:
                    return None
                else:
                    return False
            elif iterative:
                if not require_connected or result_dmrs.is_connected():
                    if copy_dmrs:
                        return result_dmrs
                    else:
                        return count > 0
                else:
                    if copy_dmrs:
                        return None
                    else:
                        return False
            else:
                return result

        # remove nodes in the matched search_dmrs if they are no anchor nodes, otherwise perform mapping()
        # mapping() performs the mapping process (with whatever it involves) specific to this node type (e.g. fill underspecified values)
        for nodeid in search_dmrs:
            search_node = search_dmrs[nodeid]
            if isinstance(search_node, AnchorNode):
                search_node.before_map(result_dmrs, search_matching[nodeid])
        replace_matching = {}
        for nodeid in search_matching:
            if nodeid in sub_mapping:
                if search_dmrs[nodeid].pred.is_more_specific(replace_dmrs[sub_mapping[nodeid]].pred, hierarchy=hierarchy):
                    replace_dmrs[sub_mapping[nodeid]].map(result_dmrs, search_matching[nodeid])
                else:
                    replace_dmrs[sub_mapping[nodeid]].map(result_dmrs, search_matching[nodeid], hierarchy=hierarchy)
                replace_dmrs[sub_mapping[nodeid]].after_map(result_dmrs, search_matching[nodeid])
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
                if copy_dmrs:
                    return result_dmrs
                else:
                    return True

    raise Exception('More than {} matches!'.format(max_matches))
