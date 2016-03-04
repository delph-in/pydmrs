import bisect
from collections import namedtuple
from collections.abc import Mapping
from operator import attrgetter
from warnings import warn

from pydmrs._exceptions import *


class Pred(object):
    """
    A superclass for all Pred classes
    """

    __slots__ = ()  # Suppress __dict__

    def __str__(self):
        """
        Returns 'rel'
        """
        return 'rel'

    def __repr__(self):
        """
        Returns a string representation
        """
        return 'Pred()'

    @staticmethod
    def from_string(string):
        """
        Instantiates a suitable type of Pred, from a string
        """
        if string == 'rel':
            return Pred()
        elif string[0] == '_':
            return RealPred.from_string(string)
        else:
            return GPred.from_string(string)


class RealPred(Pred, namedtuple('RealPredNamedTuple', ('lemma', 'pos', 'sense'))):
    """
    Real predicate, with a lemma, part of speech, and (optional) sense
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, lemma, pos, sense=None):
        """
        Create a new instance, allowing the sense to be optional,
        and requiring non-empty lemma and pos
        """
        assert lemma
        assert pos
        return super(RealPred, cls).__new__(cls, lemma, pos, sense)

    def __str__(self):
        """
        Return a string, with leading underscore, and trailing '_rel'
        """
        if self.sense:
            return "_{}_{}_{}_rel".format(*self)
        else:
            return "_{}_{}_rel".format(*self)

    def __repr__(self):
        """
        Return a string, as "RealPred(lemma, pos, sense)"
        """
        if self.sense:
            return "RealPred({}, {}, {})".format(*(repr(x) for x in self))
        else:
            return "RealPred({}, {})".format(*(repr(x) for x in self))

    @staticmethod
    def from_string(string):
        """
        Create a new instance from a string,
        stripping a trailing _rel if it exists.
        :param string: Input string
        :return: RealPred object
        """
        if string[0] != '_':
            raise PydmrsValueError("RealPred strings must begin with an underscore")

        if string[-4:] == '_rel':
            string = string[:-4]

        parts = string[1:].rsplit('_', maxsplit=2)
        if len(parts) < 2:
            raise PydmrsValueError("RealPreds require both lemma and pos")

        return RealPred(*parts)


class GPred(Pred, namedtuple('GPredNamedTuple', ('name'))):
    """
    Grammar predicate, with a rel name
    """

    __slots__ = ()  # Suppress __dict__

    def __new__(cls, name):
        """
        Create a new instance, requiring non-empty name
        """
        assert name
        return super(GPred, cls).__new__(cls, name)

    def __str__(self):
        """
        Return a string, with trailing '_rel'
        """
        return "{}_rel".format(self.name)

    def __repr__(self):
        """
        Return a string, as "GPred(name)"
        """
        return "GPred({})".format(repr(self.name))

    @staticmethod
    def from_string(string):
        """
        Create a new instance from a string,
        stripping a trailing '_rel' if it exists.
        """
        if string[0] == '_':
            raise PydmrsValueError("GPred strings must not begin with an underscore")

        if string[-4:] == '_rel':
            return GPred(string[:-4])
        else:
            return GPred(string)


class Sortinfo(Mapping):
    """
    A superclass for all Sortinfo classes
    """
    __slots__ = ()

    def __str__(self):
        """
        Returns 'i'
        """
        return 'i'

    def __repr__(self):
        """
        Returns a string representation
        """
        return 'Sortinfo()'

    def __iter__(self):
        """
        Returns an iterator over the properties
        """
        yield 'cvarsort'

    def __len__(self):
        """
        Returns the size
        """
        return sum(1 for _ in self)

    def __getitem__(self, key):
        """
        Returns the value of a property
        """
        key = key.lower()
        if key == 'cvarsort':
            return 'i'
        else:
            raise KeyError

    def __setitem__(self, key, value):
        """
        Sets the value of a property
        """
        raise KeyError

    @property
    def cvarsort(self):
        return 'i'

    @staticmethod
    def from_dict(dictionary):
        """
        Instantiates a suitable type of Sortinfo from a dictionary
        """
        dictionary = {key.lower(): value.lower() for key, value in dictionary.items()}
        assert dictionary['cvarsort'] in 'eix?'
        if dictionary['cvarsort'] in 'i?':
            return Sortinfo()
        elif dictionary['cvarsort'] == 'e':
            return EventSortinfo(dictionary.get('sf', None), dictionary.get('tense', None), dictionary.get('mood', None), dictionary.get('perf', None), dictionary.get('prog', None))
        else:
            return InstanceSortinfo(dictionary.get('pers', None), dictionary.get('num', None), dictionary.get('gend', None), dictionary.get('ind', None), dictionary.get('pt', None))

    @staticmethod
    def from_string(string):
        """
        Instantiates a suitable type of Sortinfo from a string
        """
        if string in 'i?':
            return Sortinfo()
        assert string[0] in 'ex' and string[1] == '[' and string[-1] == ']'
        values = [tuple(value.strip().split('=')) for value in string[2:-1].split(',')]
        dictionary = {key.lower(): value.lower() for key, value in values}
        if string[0] == 'e':
            return EventSortinfo(dictionary.get('sf', None), dictionary.get('tense', None), dictionary.get('mood', None), dictionary.get('perf', None), dictionary.get('prog', None))
        else:
            return InstanceSortinfo(dictionary.get('pers', None), dictionary.get('num', None), dictionary.get('gend', None), dictionary.get('ind', None), dictionary.get('pt', None))


class EventSortinfo(Sortinfo):
    """
    Event sortinfo
    """
    __slots__ = ('sf', 'tense', 'mood', 'perf', 'prog')

    def __init__(self, sf, tense, mood, perf, prog):
        """
        Create a new instance
        """
        self.sf = sf
        self.tense = tense
        self.mood = mood
        self.perf = perf
        self.prog = prog

    def __str__(self):
        """
        Returns '?'
        """
        return 'e[{}]'.format(', '.join('{}={}'.format(key, self[key]) for key in self if key != 'cvarsort'))

    def __repr__(self):
        """
        Return a string representation
        """
        return "EventSortinfo({}, {}, {}, {}, {})".format(*self)

    def __iter__(self):
        """
        Returns an iterator over the properties
        """
        return (attr for attr in ('cvarsort', 'sf', 'tense', 'mood', 'perf', 'prog') if self[attr])

    def __getitem__(self, key):
        """
        Returns the value of a property
        """
        key = key.lower()
        if key == 'cvarsort':
            return 'e'
        elif key == 'sf':
            return self.sf
        elif key == 'tense':
            return self.tense
        elif key == 'mood':
            return self.mood
        elif key == 'perf':
            return self.perf
        elif key == 'prog':
            return self.prog
        else:
            raise KeyError

    def __setitem__(self, key, value):
        """
        Sets the value of a property
        """
        key = key.lower()
        if key == 'sf':
            self.sf = value
        elif key == 'tense':
            self.tense = value
        elif key == 'mood':
            self.mood = value
        elif key == 'perf':
            self.perf = value
        elif key == 'prog':
            self.prog = value
        else:
            raise KeyError

    @property
    def cvarsort(self):
        return 'e'


class InstanceSortinfo(Sortinfo):
    """
    Instance sortinfo
    """
    __slots__ = ('pers', 'num', 'gend', 'ind', 'pt')

    def __init__(self, pers, num, gend, ind, pt):
        """
        Create a new instance
        """
        self.pers = pers
        self.num = num
        self.gend = gend
        self.ind = ind
        self.pt = pt

    def __str__(self):
        """
        Returns '?'
        """
        return 'x[{}]'.format(', '.join('{}={}'.format(key, self[key]) for key in self if key != 'cvarsort'))

    def __repr__(self):
        """
        Return a string representation
        """
        return "InstanceSortinfo({}, {}, {}, {}, {})".format(*self)

    def __iter__(self):
        """
        Returns an iterator over the properties
        """
        return (attr for attr in ('cvarsort', 'pers', 'num', 'gend', 'ind', 'pt') if self[attr])

    def __getitem__(self, key):
        """
        Returns the value of a property
        """
        key = key.lower()
        if key == 'cvarsort':
            return 'x'
        elif key == 'pers':
            return self.pers
        elif key == 'num':
            return self.num
        elif key == 'gend':
            return self.gend
        elif key == 'ind':
            return self.ind
        elif key == 'pt':
            return self.pt
        else:
            raise KeyError

    def __setitem__(self, key, value):
        """
        Sets the value of a property
        """
        key = key.lower()
        if key == 'pers':
            self.pers = value
        elif key == 'num':
            self.num = value
        elif key == 'gend':
            self.gend = value
        elif key == 'ind':
            self.ind = value
        elif key == 'pt':
            self.pt = value
        else:
            raise KeyError

    @property
    def cvarsort(self):
        return 'x'


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


class Node(object):
    """
    A DMRS node
    """
    def __init__(self, nodeid=None, pred=None, sortinfo=None, cfrom=None, cto=None, surface=None, base=None, carg=None):
        self.nodeid = nodeid
        self.pred = pred
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.base = base
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
        disconnected = disconnected_nodeids(dmrs, removed_nodeids=removed_nodeids)
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
        unvisited_nodeids = set(dmrs) - removed_nodeids
        if not unvisited_nodeids:
            return unvisited_nodeids

        # Select top/index or a random starting node, if others are None
        if start_id is None:
            if dmrs.top is not None and dmrs.top.nodeid in unvisited_nodeids:
                start_id = dmrs.top.nodeid
            elif dmrs.index is not None and dmrs.index.nodeid in unvisited_nodeids:
                start_id = dmrs.index.nodeid
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
            queue.update(self.iter_neighbour_nodeids(nodeid) & unvisited_nodeids)
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
