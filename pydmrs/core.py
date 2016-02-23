from collections import namedtuple
from operator import attrgetter
from warnings import warn
import bisect


class Pred(object):
    """
    A superclass for all Pred classes
    """
    def __str__(self):
        raise NotImplementedError
    
    def __repr__(self):
        raise NotImplementedError
    
    @staticmethod
    def from_string(string):
        """
        Instantiates a suitable type of Pred, from a string
        """
        if string[0] != '_':
            return GPred.from_string(string)
        else:
            return RealPred.from_string(string)


class RealPred(Pred, namedtuple('RealPred',('lemma','pos','sense'))):
    """
    Real predicate, with a lemma, part of speech, and (optional) sense
    """
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
            return "RealPred({}, {}, {})".format(*self)
        else:
            return "RealPred({}, {})".format(*self)
    
    @staticmethod
    def from_string(string):
        """
        Create a new instance from a string,
        stripping a trailing _rel if it exists.
        """
        assert string[0] == '_'
        if string[-4:] == '_rel':
            string = string[:-4]
        parts = string[1:].rsplit('_', maxsplit=2)
        return RealPred(*parts)


class GPred(Pred, namedtuple('GPred',('name'))):
    """
    Grammar predicate, with a rel name
    """
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
        return "{}_rel".format(*self)
    
    def __repr__(self):
        """
        Return a string, as "GPred(name)"
        """
        return "GPred({})".format(*self)
    
    @staticmethod
    def from_string(string):
        """
        Create a new instance from a string,
        stripping a trailing '_rel' if it exists.
        """
        if string[-4:] == '_rel':
            return GPred(string[:-4])
        else:
            return GPred(string)



class LinkLabel(namedtuple('LinkLabel',('rargname','post'))):
    """
    A label for a link
    """
    def __str__(self):
        return "{}/{}".format(*self)
    
    def __repr__(self):
        return "LinkLabel({}, {})".format(*self)

class Link(namedtuple('Link',('start','end','rargname','post'))):
    """
    A link
    """
    def __str__(self):
        return "({} - {}/{} -> {})".format(self.start, self.rargname, self.post, self.end)
    
    def __repr__(self):
        return "Link({}, {}, {}, {})".format(*self)
    
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
    def __init__(self, nodeid, pred, sortinfo=None, cfrom=None, cto=None, surface=None, base=None, carg=None):
        self.nodeid = nodeid
        self.pred = pred
        self.cfrom = cfrom
        self.cto = cto
        self.surface = surface
        self.base = base
        self.carg = carg
        if sortinfo:
            if isinstance(sortinfo, dict):
                self.sortinfo = sortinfo
            else:  # Allow initialising sortinfo from (key,value) pairs
                self.sortinfo = {x:y for x,y in sortinfo}
        else:
            self.sortinfo = {}
    
    @property
    def span(self):
        return (self.cfrom, self.cto)
    
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



class Dmrs(object):
    """
    A superclass for all DMRS classes
    """
    Node = Node
    
    def __init__(self, nodes, links, cfrom=None, cto=None, surface=None, ident=None, index=None, top=None):
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
        if index:
            self.index = self[index]
        else:
            self.index = None
        if top:
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
    
    def get_label(self, rargname=None, post=None, itr=False):
        """
        Get links, filtered according to the label
        If itr is set to True, return an iterator rather than a set.
        """
        linkset = filter_links(self.iter_links(), rargname=rargname, post=post)
        if not itr:
            linkset = set(linkset)
        return linkset
    
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
            node_list = self.nodes
        else:
            node_list = [n.convert_to(cls.Node) for n in self.nodes]
        return cls(node_list, self.links, self.cfrom, self.cto, self.surface, self.ident, self.index.nodeid, self.top.nodeid)


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
        assert type(node) == self.Node
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
        else: # if nodeid never found
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
        assert not new_id in self
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
        assert not link in self.outgoing.get(link.start)
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
        assert not node.nodeid in self
        assert type(node) == self.Node
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
        assert not new_id in self
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
        if (j == i or j == i+1):
            self._nodeids[i] = new_id
        else:
            self._nodeids.pop(i)
            if i < j: j-=1
            self._nodeids.insert(j, new_id)
            self.nodes.insert(j, self.nodes.pop(i))
            self.links.sort()
