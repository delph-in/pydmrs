import bisect
from collections import namedtuple
from functools import total_ordering
from operator import attrgetter
from pydmrs.components import Pred, Sortinfo
from pydmrs._exceptions import *


class LinkLabel(namedtuple('LinkLabelNamedTuple', ('rargname', 'post'))):
    """
    A label for a link
    """

    __slots__ = ()  # Suppress __dict__

    def __str__(self):
        return "{}/{}".format(*self)

    def __repr__(self):
        return "LinkLabel({}, {})".format(*(repr(x) for x in self))


class Link(namedtuple('LinkNamedTuple', ('start', 'end', 'rargname', 'post'))):
    """
    A link
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, start, end, rargname, post):
        """
        Create a new instance
        """
        return super().__new__(cls, start, end, None if rargname is None else rargname.upper(), None if post is None else post.upper())

    def __str__(self):
        return "({} - {}/{} -> {})".format(self.start, self.rargname, self.post, self.end)

    def __repr__(self):
        return "Link({}, {}, {}, {})".format(*(repr(x) for x in self))

    @property
    def label(self):
        return LinkLabel(self.rargname, self.post)

    @property
    def labelstring(self):
        return "{}/{}".format(self.rargname, self.post)


@total_ordering
class Node(object):
    """
    A DMRS node
    """
    def __init__(self, nodeid=None, pred=None, sortinfo=None, cfrom=None, cto=None, surface=None, base=None, carg=None):
        self.nodeid = nodeid
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.base = base

        if isinstance(pred, Pred):
            self.pred = pred
        else:
            self.pred = Pred.from_string(pred)

        if carg and carg[0] == '"' and carg[-1] == '"':
            carg = carg[1:-1]
        if carg and '"' in carg:
            raise PydmrsValueError('Cargs must not contain quotes.')
        self.carg = carg

        if sortinfo:
            if isinstance(sortinfo, Sortinfo):
                self.sortinfo = sortinfo
            elif isinstance(sortinfo, dict):
                self.sortinfo = Sortinfo.from_dict(sortinfo)
            else:  # Allow initialising sortinfo from (key,value) pairs
                self.sortinfo = Sortinfo.from_dict({x: y for x, y in sortinfo})
        else:
            self.sortinfo = None

    def __str__(self):
        if self.carg:
            if self.sortinfo:
                return '{}({}) {}'.format(self.pred, self.carg, self.sortinfo)
            else:
                return '{}({})'.format(self.pred, self.carg)
        elif self.sortinfo:
            return '{} {}'.format(self.pred, self.sortinfo)
        else:
            return str(self.pred)

    def __eq__(self, other):
        """
        Checks two nodes for equality (predicate, carg, sortinfo)
        """
        return isinstance(other, Node) and self.pred == other.pred and self.carg == other.carg and self.sortinfo == other.sortinfo

    def __le__(self, other):
        """
        Checks whether this node underspecifies or equals the other node (predicate, carg, sortinfo)
        """
        return isinstance(other, Node) and ((self.pred is None and other.pred is None) or (self.pred <= other.pred)) and (not self.carg or self.carg == other.carg) and ((self.sortinfo is None and other.sortinfo is None) or (self.sortinfo <= other.sortinfo))

    @property
    def span(self):
        return self.cfrom, self.cto

    @property
    def is_gpred_node(self):
        return isinstance(self.pred, GPred)

    @property
    def is_realpred_node(self):
        return isinstance(self.pred, RealPred)

    def convert_to(self, cls):
        return cls(self.nodeid, self.pred, self.sortinfo, self.cfrom, self.cto, self.surface, self.base, self.carg)


class PointerNode(Node):
    """
    A DMRS node with a pointer to the whole graph,
    to allow access to links
    """

    def __init__(self, *args, graph=None, **kwargs):
        super(PointerNode, self).__init__(*args, **kwargs)
        self.graph = graph

    @property
    def incoming(self):
        """
        Incoming links
        """
        if self.graph:
            return self.graph.get_in(self.nodeid)
        else:
            return set()

    @property
    def outgoing(self):
        """
        Outgoing links
        """
        if self.graph:
            return self.graph.get_out(self.nodeid)
        else:
            return set()

    def get_in(self, *args, **kwargs):
        """
        Incoming links, filtered by the label.
        If nodes is set to True, return nodes rather than links.
        If itr is set to True, return an iterator rather than a set.
        """
        if self.graph:
            return self.graph.get_in(self.nodeid, *args, **kwargs)
        else:
            return set()

    def get_out(self, *args, **kwargs):
        """
        Outgoing links, filtered by the label.
        If nodes is set to True, return nodes rather than links.
        If itr is set to True, return an iterator rather than a set.
        """
        if self.graph:
            return self.graph.get_out(self.nodeid, *args, **kwargs)
        else:
            return set()

    def renumber(self, new_id):
        """
        Change the node's id to new_id
        """
        if self.graph:
            self.graph.renumber_node(self.nodeid, new_id)
        else:
            self.nodeid = new_id

    @property
    def is_quantifier(self):
        """
        Check if the node is a quantifier
        by looking for an outgoing RSTR/H link
        """
        return self.graph.is_quantifier(self.nodeid)


class Dmrs(object):
    """
    A superclass for all DMRS classes
    """
    Node = Node

    def __init__(self, nodes=(), links=(), cfrom=None, cto=None, surface=None, ident=None, index=None, top=None):
        """
        Initialise simple attributes, index, and top.
        """
        # Initialise nodes and links
        self.add_nodes(nodes)
        self.add_links(links)

        # Initialise simple attributes
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.ident = ident

        # Initialise index and top
        if isinstance(index, Node):
            self.index = index
        elif isinstance(index, int):
            self.index = self[index]
        else:
            self.index = None
        if isinstance(top, Node):
            self.top = top
        elif isinstance(top, int):
            self.top = self[top]
        else:
            self.top = None

    def add_node(self, node): raise NotImplementedError
    def add_link(self, link): raise NotImplementedError
    def remove_node(self, nodeid): raise NotImplementedError
    def remove_link(self, link): raise NotImplementedError
    def iter_nodes(self): raise NotImplementedError
    def iter_links(self): raise NotImplementedError
    def iter_outgoing(self, nodeid): raise NotImplementedError
    def iter_incoming(self, nodeid): raise NotImplementedError
    def renumber_node(self, old_id, new_id): raise NotImplementedError
    def __getitem__(self, nodeid): raise NotImplementedError
    def __iter__(self): raise NotImplementedError
    def __len__(self): raise NotImplementedError

    def free_nodeid(self):
        """Returns a free nodeid"""
        return max(self) + 1

    def add_nodes(self, iterable):
        """Add a number of nodes"""
        for node in iterable:
            self.add_node(node)

    def add_links(self, iterable):
        """Add a number of links"""
        for link in iterable:
            self.add_link(link)

    def remove_links(self, iterable):
        """Remove a number of links"""
        for link in iterable:
            self.remove_link(link)

    def remove_nodes(self, iterable):
        """Remove a number of nodes and all associated links"""
        for nodeid in iterable:
            self.remove_node(nodeid)

    def get_out(self, nodeid, rargname=None, post=None, nodes=False, itr=False):
        """
        Get links going from a node.
        If rargname or post are specified, filter according to the label.
        If nodes is set to True, return nodes rather than links.
        If itr is set to True, return an iterator rather than a set.
        """
        linkset = self.iter_outgoing(nodeid)

        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)

        if nodes:
            linkset = (self[link.end] for link in linkset)

        if not itr:
            linkset = set(linkset)

        return linkset

    def get_in(self, nodeid, rargname=None, post=None, nodes=False, itr=False):
        """
        Get links coming to a node.
        If rargname or post are specified, filter according to the label.
        If nodes is set to True, return nodes rather than links.
        If itr is set to True, return an iterator rather than a set.
        """
        linkset = self.iter_incoming(nodeid)

        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)

        if nodes:
            linkset = (self[link.start] for link in linkset)

        if not itr:
            linkset = set(linkset)

        return linkset

    def iter_neighbour_nodeids(self, nodeid):
        """
        Retrieve adjacent node ids (regardless of link direction) from the dmrs for given node id
        """
        assert nodeid in self, 'Invalid node id.'
        return {link.end for link in self.get_out(nodeid, itr=True)} | {link.start for link in self.get_in(nodeid, itr=True)}

    def get_label(self, rargname=None, post=None, itr=False):
        """
        Get links, filtered according to the label
        If itr is set to True, return an iterator rather than a set.
        """
        linkset = filter_links(self.iter_links(), rargname=rargname, post=post)
        if not itr:
            linkset = set(linkset)

        return linkset

    def is_quantifier(self, nodeid):
        """
        Check if a given node is a quantifier
        by looking for an outgoing RSTR/H link
        """
        if self.get_out(nodeid, rargname='RSTR', post='H'):
            return True
        else:
            return False

    def is_connected(self, removed_nodeids=frozenset(), ignored_nodeids=frozenset()):
        """
        Determine if a DMRS graph is connected.
        :param dmrs: DMRS object
        :param removed_nodeids: Set of node ids that should be considered as already removed.
         This is to prevent the need for excessive copying of DMRS graphs for hypothetical node removals.
        :param ignored_nodeids: Set of node ids that should not be considered as disconnected if found as such.
         This is to prevent nodes that are going to be filtered out later from affecting results of connectivity test.
        :return: True if DMRS is connected, otherwise False.
        """
        disconnected = self. disconnected_nodeids(removed_nodeids=removed_nodeids)
        return len(disconnected - ignored_nodeids) == 0

    def disconnected_nodeids(self, start_id=None, removed_nodeids=frozenset()):
        """
        Search for disconnected nodes.
        :param start_id: Node id to start search. If None, top/index or random node id.
        :param removed_nodeids: Set of node ids that should be considered as already removed.
         This is to prevent the need for excessive copying of DMRS graphs for hypothetical node removals.
        :return: Set of disconnected node ids
        """

        # Initialize the set of node that have not been visited yet
        unvisited_nodeids = set(self) - removed_nodeids
        if not unvisited_nodeids:
            return unvisited_nodeids

        # Select top/index or a random starting node, if others are None
        if start_id is None:
            if self.top is not None and self.top.nodeid in unvisited_nodeids:
                start_id = self.top.nodeid
            elif self.index is not None and self.index.nodeid in unvisited_nodeids:
                start_id = self.index.nodeid
            else:
                start_id = unvisited_nodeids.pop()
        else:
            assert start_id in unvisited_nodeids, 'Start nodeid not a valid node id.'

        # Start the explore set with nodes adjacent to the starting node
        explore_set = self.iter_neighbour_nodeids(start_id) & unvisited_nodeids
        unvisited_nodeids.remove(start_id)

        # Iteratively visit a node and update the explore set with neighbouring nodes until explore set empty
        while explore_set:
            nodeid = explore_set.pop()
            unvisited_nodeids.remove(nodeid)
            explore_set.update(self.iter_neighbour_nodeids(nodeid) & unvisited_nodeids)
        return unvisited_nodeids

    @classmethod
    def loads_xml(cls, bytestring, encoding=None):
        """
        Currently processes "<dmrs>...</dmrs>"
        To be updated for "<dmrslist>...</dmrslist>"...
        Expects a bytestring; to load from a string instead, specify encoding
        """
        from pydmrs.serial import loads_xml
        return loads_xml(bytestring, encoding=encoding, cls=cls)

    @classmethod
    def load_xml(cls, filehandle):
        """
        Load a DMRS from a file
        NB: read file as bytes!
        """
        return cls.loads_xml(filehandle.read())

    def dumps_xml(self, encoding=None):
        """
        Currently creates "<dmrs>...</dmrs>"
        To be updated for "<dmrslist>...</dmrslist>"...
        Returns a bytestring; to return a string instead, specify encoding
        """
        from pydmrs.serial import dumps_xml
        return dumps_xml(self, encoding=encoding)

    def dump_xml(self, filehandle):
        """
        Dump a DMRS to a file
        NB: write as a bytestring!
        """
        filehandle.write(self.dumps_xml())

    def convert_to(self, cls):
        """
        Convert to a different DMRS format
        """
        if self.Node == cls.Node:
            nodes = self.iter_nodes()
        else:
            nodes = (n.convert_to(cls.Node) for n in self.iter_nodes())
        return cls(nodes, self.iter_links(), self.cfrom, self.cto, self.surface, self.ident, self.index.nodeid, self.top.nodeid)

    def visualise(self, format='dot', filehandle=None):
        """
        Returns the bytestring of the chosen visualisation representation
        format. If filehandle is set, writes the bytestream to the respective
        file (in binary mode!).
        Supported formats:
        - dot  (Cmd to convert to png: "dot -Tpng [file.dot] > [file.png]")
        """
        from pydmrs.serial import visualise
        bytestring = visualise(self, format)
        if filehandle:
            filehandle.write(bytestring)
        else:
            return bytestring


class ListDmrs(Dmrs):
    """
    A DMRS graph implemented with lists for nodes and links
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise the graph
        """
        self.nodes = []
        self.links = []
        super(ListDmrs, self).__init__(*args, **kwargs)

    def __getitem__(self, nodeid):
        """
        Allow accessing nodes as self[nodeid]
        """
        for n in self.nodes:
            if n.nodeid == nodeid:
                return n

    def __iter__(self):
        """
        Allow iterating over nodeids using 'in'
        """
        for n in self.nodes:
            yield n.nodeid

    def __len__(self):
        """
        Return the number of nodes in the graph
        """
        return self.nodes.__len__()

    def iter_nodes(self):
        return self.nodes.__iter__()

    def iter_links(self):
        return self.links.__iter__()

    def add_link(self, link):
        """Add a link"""
        self.links.append(link)

    def add_links(self, iterable):
        """Add a number of links"""
        self.links.extend(iterable)

    def remove_link(self, link):
        """Remove a link"""
        self.links.remove(link)

    def add_node(self, node):
        """Add a node"""
        assert isinstance(node, self.Node)
        self.nodes.append(node)

    def remove_node(self, nodeid):
        """
        Remove a node and all associated links
        """
        # Remove node:
        for i, node in enumerate(self.nodes):
            if node.nodeid == nodeid:
                self.nodes.pop(i)
                break

        else:  # if nodeid never found
            raise KeyError(nodeid)

        # Remove links:
        remove = []
        for i, link in enumerate(self.links):
            if link.start == nodeid or link.end == nodeid:
                remove.append(i)

        for i in reversed(remove):
            self.links.pop(i)

        # Check if the node was top or index
        if self.top and self.top.nodeid == nodeid:
            self.top = None

        if self.index and self.index.nodeid == nodeid:
            self.index = None

    def iter_outgoing(self, nodeid):
        """
        Iterate through links going from a given node
        """
        for link in self.links:
            if link.start == nodeid:
                yield link

    def iter_incoming(self, nodeid):
        """
        Iterate through links coming to a given node
        """
        for link in self.links:
            if link.end == nodeid:
                yield link

    def renumber_node(self, old_id, new_id):
        """
        Change a node's ID from old_id to new_id
        """
        assert new_id not in self
        self[old_id].nodeid = new_id

        for i, link in enumerate(self.links):
            start, end, rargname, post = link
            if start == old_id:
                self.links[i] = Link(new_id, end, rargname, post)
            elif end == old_id:
                self.links[i] = Link(start, new_id, rargname, post)

    def sort(self):
        """
        Sort the lists of nodes and links by nodeids
        """
        self.nodes.sort(key=attrgetter('nodeid'))
        self.links.sort()


class SetDict(dict):
    """
    A dict of sets.
    Used to store links in DictDmrs.
    """
    def remove(self, key, value):
        """
        Remove value from the set self[key],
        and remove the whole set if there's nothing left
        """
        self[key].remove(value)
        if not self[key]:
            self.pop(key)

    def add(self, key, value):
        """
        Add value to the set self[key],
        initialising a new set if it doesn't already exist
        """
        self.setdefault(key, set()).add(value)

    def get(self, key):
        """
        Get a set in the dictionary,
        defaulting to the empty set if not found
        """
        return super(SetDict, self).get(key, set())


class DictDmrs(Dmrs):
    """
    A DMRS graph implemented with dicts for nodes and links
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise dictionaries from lists
        """
        self._nodes = {}
        self.outgoing = SetDict()
        self.incoming = SetDict()
        super(DictDmrs, self).__init__(*args, **kwargs)

    def __getitem__(self, nodeid):
        """
        Allow accessing nodes as self[nodeid]
        """
        return self._nodes[nodeid]

    def __iter__(self):
        """
        Allow iterating over nodeids using 'in'
        """
        return self._nodes.__iter__()

    def __contains__(self, nodeid):
        """
        Allow checking if a node is in the graph
        """
        return self._nodes.__contains__(nodeid)

    def __len__(self):
        """
        Return the number of nodes in the graph
        """
        return self._nodes.__len__()

    def iter_links(self):
        """
        Iterate through all links
        """
        for outset in self.outgoing.values():
            for link in outset:
                yield link

    def iter_nodes(self):
        """
        Iterate through all nodes
        """
        return iter(self._nodes.values())

    @property
    def links(self):
        """
        Return a list of links
        """
        links = []
        for _, outset in sorted(self.outgoing.items()):
            links.extend(sorted(outset, key=attrgetter('end')))

        return links

    @property
    def nodes(self):
        """
        Return a list of nodes
        """
        return sorted(self._nodes.values(), key=attrgetter('nodeid'))

    def add_link(self, link):
        """
        Add a link.
        """
        if not (link.start in self and link.end in self):
            raise KeyError((link.start, link.end))

        assert link not in self.outgoing.get(link.start)
        self.outgoing.add(link.start, link)
        self.incoming.add(link.end, link)

    def remove_link(self, link):
        """
        Remove a link.
        """
        self.outgoing.remove(link.start, link)
        self.incoming.remove(link.end, link)

    def add_node(self, node):
        """
        Add a node
        """
        assert node.nodeid not in self
        assert isinstance(node, self.Node)
        self._nodes[node.nodeid] = node

    def remove_node(self, nodeid):
        """
        Remove a node and all associated links
        """
        # Remove links
        if nodeid in self.outgoing:
            for link in self.outgoing[nodeid]:
                self.incoming.remove(link.end, link)
            self.outgoing.pop(nodeid)

        if nodeid in self.incoming:
            for link in self.incoming[nodeid]:
                self.outgoing.remove(link.start, link)
            self.incoming.pop(nodeid)

        # Remove the node
        self._nodes.pop(nodeid)

        # Check if the node was top or index
        if self.top and self.top.nodeid == nodeid:
            self.top = None
        if self.index and self.index.nodeid == nodeid:
            self.index = None

    def iter_outgoing(self, nodeid):
        return self.outgoing.get(nodeid).__iter__()

    def iter_incoming(self, nodeid):
        return self.incoming.get(nodeid).__iter__()

    def renumber_node(self, old_id, new_id):
        """
        Change a node's ID from old_id to new_id
        """
        assert new_id not in self

        node = self._nodes.pop(old_id)
        node.nodeid = new_id
        self._nodes[new_id] = node

        for link in self.outgoing.pop(old_id, set()):
            _, end, rargname, post = link
            self.incoming[end].remove(link)
            newlink = Link(new_id, end, rargname, post)
            self.outgoing.add(new_id, newlink)
            self.incoming.add(end, newlink)

        for link in self.incoming.pop(old_id, set()):
            start, _, rargname, post = link
            self.outgoing[start].remove(link)
            newlink = Link(start, new_id, rargname, post)
            self.outgoing.add(start, newlink)
            self.incoming.add(new_id, newlink)


class PointerMixin(Dmrs):
    """
    Allow a DMRS class to use PointerNode
    """
    Node = PointerNode

    def add_node(self, node):
        """Add a node"""
        # Although add_node() is not defined in Dmrs,
        # in subclasses of PointerMixin, super() looks at the Method Resolution Order,
        # which can include other parent classes where add_node() is defined.
        super(PointerMixin, self).add_node(node)
        node.graph = self


class ListPointDmrs(PointerMixin, ListDmrs):
    """
    A DMRS graph implemented with lists for nodes and links,
    plus pointers from nodes to the graph
    """


class DictPointDmrs(PointerMixin, DictDmrs):
    """
    A DMRS graph implemented with dicts for nodes and links,
    plus pointers from nodes to the graph
    """


def filter_links(iterable, rargname, post):
    """
    Filter links according to the label.
    None specifies a wildcard.
    """
    if not (rargname or post):
        raise Exception("Specify either 'rargname' or 'post'")
    elif not rargname:
        return (x for x in iterable if x.post == post)
    elif not post:
        return (x for x in iterable if x.rargname == rargname)
    else:
        return (x for x in iterable if x.rargname == rargname and x.post == post)


class SortDictDmrs(DictDmrs):
    """
    A DMRS graph implemented with both dicts and lists for nodes and links,
    with lists sorted according to nodeid
    """
    # To override @property binding from DictDmrs
    nodes = None
    links = None

    def __init__(self, nodes, links, *args, **kwargs):
        self.links = []
        self.nodes = []
        self._nodeids = []
        super(SortDictDmrs, self).__init__(nodes, links, *args, **kwargs)

    def __iter__(self):
        return self._nodeids.__iter__()

    def iter_nodes(self):
        return self.nodes.__iter__()

    def iter_links(self):
        return self.links.__iter__()

    def add_link(self, link):
        super(SortDictDmrs, self).add_link(link)
        bisect.insort(self.links, link)

    def remove_link(self, link):
        super(SortDictDmrs, self).remove_link(link)
        i = bisect.bisect_left(self.links, link)
        self.links.pop(i)

    def add_node(self, node):
        super(SortDictDmrs, self).add_node(node)
        i = bisect.bisect(self._nodeids, node.nodeid)
        self._nodeids.insert(i, node.nodeid)
        self.nodes.insert(i, node)

    def remove_node(self, nodeid):
        super(SortDictDmrs, self).remove_node(nodeid)

        i = bisect.bisect_left(self._nodeids, nodeid)
        self._nodeids.pop(i)
        self.nodes.pop(i)

        remove = []
        for i, link in enumerate(self.links):
            if link.start == nodeid or link.end == nodeid:
                remove.append(i)

        for i in remove:
            self.links.pop(i)

    def renumber_node(self, old_id, new_id):
        super(SortDictDmrs, self).renumber_node(old_id, new_id)

        for i, link in enumerate(self.links):
            start, end, rargname, post = link
            if start == old_id:
                self.links[i] = Link(new_id, end, rargname, post)
            elif end == old_id:
                self.links[i] = Link(start, new_id, rargname, post)

        i = bisect.bisect_left(self._nodeids, old_id)
        j = bisect.bisect_left(self._nodeids, new_id)

        if j == i or j == i+1:
            self._nodeids[i] = new_id
        else:
            self._nodeids.pop(i)
            if i < j:
                j -= 1
            self._nodeids.insert(j, new_id)
            self.nodes.insert(j, self.nodes.pop(i))
            self.links.sort()
