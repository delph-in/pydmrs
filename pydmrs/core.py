import bisect
from collections import namedtuple
import copy
from functools import total_ordering
from operator import attrgetter
from itertools import chain
from pydmrs.components import *
from pydmrs._exceptions import *


class LinkLabel(namedtuple('LinkLabelNamedTuple', ('rargname', 'post'))):
    """
    A label for a link
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, rargname, post):
        """
        Create new instance, forcing strings to be uppercase
        """
        if isinstance(rargname, str):
            rargname = rargname.upper()
        if isinstance(post, str):
            post = post.upper()
        return super().__new__(cls, rargname, post)

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
        Create a new instance, forcing strings to be uppercase
        """
        if isinstance(rargname, str):
            rargname = rargname.upper()
        if isinstance(post, str):
            post = post.upper()
        return super().__new__(cls, start, end, rargname, post)

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

        if isinstance(pred, str):
            self.pred = Pred.from_string(pred)
        else:
            self.pred = pred

        if carg and carg[0] == '"' and carg[-1] == '"':
            carg = carg[1:-1]
        if carg and '"' in carg:
            raise PydmrsValueError('Cargs must not contain quotes.')
        self.carg = carg

        if isinstance(sortinfo, Sortinfo):
            self.sortinfo = sortinfo
        elif isinstance(sortinfo, dict):
            self.sortinfo = Sortinfo.from_dict(sortinfo)
        elif isinstance(sortinfo, list):  # Allow initialising sortinfo from (key,value) pairs
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
        return isinstance(other, Node) \
            and self.pred == other.pred \
            and self.carg == other.carg \
            and self.sortinfo == other.sortinfo

    def __le__(self, other):
        """
        Checks whether this node underspecifies or equals the other node (predicate, carg, sortinfo)
        """
        return isinstance(other, Node) \
            and ((self.pred is None and other.pred is None) \
                 or (self.pred <= other.pred)) \
            and (not self.carg or self.carg == other.carg) \
            and ((self.sortinfo is None and other.sortinfo is None) \
                 or (self.sortinfo <= other.sortinfo))

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
        return cls(self.nodeid,
                   self.pred,
                   self.sortinfo,
                   self.cfrom,
                   self.cto,
                   self.surface,
                   self.base,
                   self.carg)


class PointerNode(Node):
    """
    A DMRS node with a pointer to the whole graph,
    to allow access to links
    """

    def __init__(self, *args, graph=None, **kwargs):
        super().__init__(*args, **kwargs)
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
    def renumber_node(self, old_id, new_id): raise NotImplementedError
    def __getitem__(self, nodeid): raise NotImplementedError
    def __iter__(self): raise NotImplementedError
    def __len__(self): raise NotImplementedError
    def count_links(self): raise NotImplementedError

    def __contains__(self, nodeid):
        """
        Checks whether a node id is in the DMRS graph
        """
        return any(n == nodeid for n in self)

    def iter_outgoing(self, nodeid):
        """
        Iterate through links going from a given node
        """
        if nodeid not in self:
            raise PydmrsValueError('{} not a valid nodeid'.format(nodeid))
        for link in self.iter_links():
            if link.start == nodeid:
                yield link

    def iter_incoming(self, nodeid):
        """
        Iterate through links coming to a given node
        """
        if nodeid not in self:
            raise PydmrsValueError('{} not a valid nodeid'.format(nodeid))
        for link in self.iter_links():
            if link.end == nodeid:
                yield link

    def free_nodeid(self):
        """Returns a free nodeid"""
        if len(self):
            return max(self) + 1
        else:
            return 1

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

    def get_out(self, nodeid, rargname=None, post=None, itr=False):
        """
        Get links going from a node.
        If rargname or post are specified, filter according to the label.
        If itr is set to True, return an iterator rather than a set.
        """
        linkset = self.iter_outgoing(nodeid)

        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)

        if not itr:
            linkset = set(linkset)

        return linkset

    def get_in(self, nodeid, rargname=None, post=None, itr=False):
        """
        Get links coming to a node.
        If rargname or post are specified, filter according to the label.
        If itr is set to True, return an iterator rather than a set.
        """
        linkset = self.iter_incoming(nodeid)

        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)

        if not itr:
            linkset = set(linkset)

        return linkset
    
    def get_links(self, nodeid, rargname=None, post=None, itr=False):
        """
        Get links going from or coming to a node.
        If rargname or post are specified, filter according to the label.
        If itr is set to True, return an iterator rather than a set.
        """
        in_links = self.get_in(nodeid, rargname, post, itr)
        out_links = self.get_out(nodeid, rargname, post, itr)
        if itr:
            return chain(in_links, out_links)
        else:
            return in_links | out_links

    def get_out_nodes(self, nodeid, rargname=None, post=None, nodeids=False, itr=False):
        """
        Get end nodes of links going from a node.
        If rargname or post are specified, filter according to the label.
        If nodeids is set to True, return nodeids rather than nodes.
        If itr is set to True, return an iterator rather than a list (of nodes) or set (of nodeids).
        """
        links = self.get_out(nodeid, rargname=rargname, post=post, itr=True)
        # Get nodeids:
        nodes = (link.end for link in links)
        # Get nodes, if requested:
        if not nodeids:
            nodes = (self[nid] for nid in nodes)
        # Convert to a list/set if requested:
        if not itr:
            if nodeids:
                nodes = set(nodes)
            else:
                nodes = list(nodes)
        return nodes

    def get_in_nodes(self, nodeid, rargname=None, post=None, nodeids=False, itr=False):
        """
        Get start nodes of links coming to a node.
        If rargname or post are specified, filter according to the label.
        If nodeids is set to True, return nodeids rather than nodes.
        If itr is set to True, return an iterator rather than a list (of nodes) or set (of nodeids).
        """
        links = self.get_in(nodeid, rargname=rargname, post=post, itr=True)
        # Get nodeids:
        nodes = (link.start for link in links)
        # Get nodes, if requested:
        if not nodeids:
            nodes = (self[nid] for nid in nodes)
        # Convert to a list/set if requested:
        if not itr:
            if nodeids:
                nodes = set(nodes)
            else:
                nodes = list(nodes)
        return nodes

    def get_neighbours(self, nodeid, rargname=None, post=None, nodeids=False, itr=False):
        """
        Get adjacent nodes (regardless of link direction)
        If rargname or post are specified, filter according to the label.
        If nodeids is set to True, return nodeids rather than nodes.
        If itr is set to True, return an iterator rather than a list (of nodes) or set (of nodeids).
        """
        in_nodes = self.get_in_nodes(nodeid, rargname, post, nodeids, itr)
        out_nodes = self.get_out_nodes(nodeid, rargname, post, nodeids, itr)
        if itr:
            return chain(in_nodes, out_nodes)
        elif nodeids:
            return in_nodes | out_nodes
        else:
            return in_nodes + out_nodes

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
        disconnected = self.disconnected_nodeids(removed_nodeids=removed_nodeids)
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
                start_id = next(iter(unvisited_nodeids))
        else:
            assert start_id in unvisited_nodeids, 'Start nodeid not a valid node id.'

        # Start the explore set with nodes adjacent to the starting node
        explore_set = self.get_neighbours(start_id, nodeids=True) & unvisited_nodeids
        unvisited_nodeids.remove(start_id)

        # Iteratively visit a node and update the explore set with neighbouring nodes until explore set empty
        while explore_set:
            nodeid = explore_set.pop()
            unvisited_nodeids.remove(nodeid)
            explore_set.update(self.get_neighbours(nodeid, nodeids=True) & unvisited_nodeids)
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

    def convert_to(self, cls, copy_nodes=False):
        """
        Convert to a different DMRS format, optionally copying the nodes
        instead of keeping the same instances.
        """
        if copy_nodes:
            nodes = (copy.deepcopy(node) for node in self.iter_nodes())
        elif self.Node == cls.Node:
            nodes = self.iter_nodes()
        else:
            nodes = (node.convert_to(cls.Node) for node in self.iter_nodes())
        return cls(nodes,
                   self.iter_links(),
                   self.cfrom,
                   self.cto,
                   self.surface,
                   self.ident,
                   self.index.nodeid if self.index else None,
                   self.top.nodeid if self.top else None)

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
        super().__init__(*args, **kwargs)

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

    def count_links(self):
        """
        Return the number of links in the graph
        """
        return self.links.__len__()

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
        assert node.nodeid not in self
        assert isinstance(node, self.Node)
        if node.nodeid is None:
            node.nodeid = self.free_nodeid()
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
        return super().get(key, set())


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
        super().__init__(*args, **kwargs)

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

    def count_links(self):
        """
        Return the number of links in the graph
        """
        return sum(len(links) for links in self.outgoing.values())

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
        for outset in sorted(self.outgoing.values()):
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
        if node.nodeid is None:
            node.nodeid = self.free_nodeid()
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
        if nodeid not in self:
            raise PydmrsValueError('{} not a valid nodeid'.format(nodeid))
        return self.outgoing.get(nodeid).__iter__()

    def iter_incoming(self, nodeid):
        if nodeid not in self:
            raise PydmrsValueError('{} not a valid nodeid'.format(nodeid))
        return self.incoming.get(nodeid).__iter__()

    def renumber_node(self, old_id, new_id):
        """
        Change a node's ID from old_id to new_id
        """
        assert new_id not in self

        node = self._nodes.pop(old_id)
        node.nodeid = new_id
        self._nodes[new_id] = node

        for link in self.outgoing.pop(old_id, ()):
            _, end, rargname, post = link
            self.incoming[end].remove(link)
            newlink = Link(new_id, end, rargname, post)
            self.outgoing.add(new_id, newlink)
            self.incoming.add(end, newlink)

        for link in self.incoming.pop(old_id, ()):
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
        super().add_node(node)
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


def span_pred_key(node):
    return (node.cfrom, -node.cto, str(node.pred))

class SortDictDmrs(DictDmrs):
    """
    A DMRS graph implemented with both dicts and lists for nodes and links,
    with lists sorted according to some key.
    By default, nodes and links are sorted by nodeid.
    """
    # To override @property binding from DictDmrs
    nodes = None
    links = None

    def __init__(self, *args, node_key=None, link_key=None, **kwargs):
        # Sorted lists
        self.nodes = []
        self.links = []
        # Sorted lists of keys
        self._node_keys = []
        self._link_keys = []

        if node_key is not None:
            self.node_key = node_key
        # If node_key not specified, sort by nodeid
        else:
            self.node_key = attrgetter('nodeid')

        if link_key is not None:
            self.link_key = link_key
        # If link_key not specified but node_key specified,
        # sort according to start and end keys
        elif node_key is not None:
            self.link_key = lambda x : (node_key(self[x.start]),
                                        node_key(self[x.end]),
                                        x.rargname,
                                        x.post)
        # If link_key not specified and node_key not specified,
        # we don't need to look up the node to find the nodeid
        else:
            self.link_key = lambda x:x

        super().__init__(*args, **kwargs)

    def __iter__(self):
        return (n.nodeid for n in self.nodes)

    def iter_nodes(self):
        return self.nodes.__iter__()

    def iter_links(self):
        return self.links.__iter__()

    def add_link(self, link):
        # Add link to dictionaries
        super().add_link(link)
        # Find where the link should be placed in order
        key = self.link_key(link)
        i = bisect.bisect_right(self._link_keys, key)
        # Insert the link accordingly
        self._link_keys.insert(i, key)
        self.links.insert(i, link)

    def remove_link(self, link):
        # Remove the link from dictionaries
        super().remove_link(link)
        # Remove the link from the sorted lists
        i = bisect.bisect_left(self._link_keys, self.link_key(link))
        self.links.pop(i)
        self._link_keys.pop(i)

    def add_node(self, node):
        # Add node to dictionary
        super().add_node(node)
        # Find where the node should be placed in order
        key = self.node_key(node)
        i = bisect.bisect_right(self._node_keys, key)
        # Insert the node accordingly
        self._node_keys.insert(i, key)
        self.nodes.insert(i, node)

    def remove_node(self, nodeid):
        node = self[nodeid]
        
        # Remove the node and associated links from dictionaries
        super().remove_node(nodeid)
        
        # Remove the node and key from the sorted lists
        i = bisect.bisect_left(self._node_keys, self.node_key(node))
        self._node_keys.pop(i)
        self.nodes.pop(i)

        # Remove all associated links from the sorted lists
        remove = []
        for i, link in enumerate(self.links):
            if link.start == nodeid or link.end == nodeid:
                remove.append(i)
        for i in reversed(remove):
            self.links.pop(i)
            self._link_keys.pop(i)

    def renumber_node(self, old_id, new_id):
        # As we potentially have a lot of things to change,
        # the easiest option is to remove everything and add it again
        # (We could first check whether changing the nodeid changes the keys...)
        # (If link keys don't change, we could just replace them in place...)
        node = self[old_id]
        new_out = (Link(new_id, link.end, link.rargname, link.post) \
                   for link in self.get_out(old_id, itr=True))
        new_in = (Link(link.start, new_id, link.rargname, link.post) \
                  for link in self.get_in(old_id, itr=True))
        
        # Remove the node and all associated links
        self.remove_node(old_id)
        
        # Change the id of the node and add it
        node.nodeid = new_id
        self.add_node(node)
        
        # Add all the links
        for link in new_out:
            self.add_link(link)
        for link in new_in:
            self.add_link(link)
