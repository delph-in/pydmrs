from collections import namedtuple
from xml.etree.ElementTree import XML
from operator import attrgetter


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
        assert string[-4:] == '_rel'
        if string[0] != '_':
            return GPred(string[:-4])
        else:
            parts = string[1:-4].split('_')
            return RealPred(*parts)


class RealPred(Pred, namedtuple('RealPred',('lemma','pos','sense'))):
    """
    Real predicate, with a lemma, part of speech, and (optional) sense
    """
    def __new__(cls, lemma, pos, sense=None):
        """
        Create a new instance, allowing the sense to be optional
        """
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


class GPred(Pred, namedtuple('GPred',('name'))):
    """
    Grammar predicate, with a rel name
    """
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
        return "({}:{}/{} -> {})".format(self.start, self.rargname, self.post, self.end)
    
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
        return self.graph.get_in(self.nodeid)
    
    @property
    def outgoing(self):
        """
        Outgoing links
        """
        return self.graph.get_out(self.nodeid)
    
    def get_in(self, rargname=None, post=None, nodes=False):
        """
        Incoming links, filtered by the label.
        If nodes is set to True, return nodes rather than links. 
        """
        return self.graph.get_in(self.nodeid, rargname=rargname, post=post, nodes=nodes)
    
    def get_out(self, rargname=None, post=None, nodes=False):
        """
        Outgoing links, filtered by the label.
        If nodes is set to True, return nodes rather than links.
        """
        return self.graph.get_out(self.nodeid, rargname=rargname, post=post, nodes=nodes)



class Dmrs(object):
    """
    A superclass for all DMRS classes
    """
    Node = Node
    
    def __init__(self, cfrom=None, cto=None, surface=None, ident=None, index=None, top=None):
        """
        Initialise simple attributes, index, and top.
        Does not initialise nodes and links!
        """
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
    
    @classmethod
    def loads_xml(cls, bytestring, encoding=None):
        """
        Currently processes "<dmrs>...</dmrs>"
        To be updated for "<dmrslist>...</dmrslist>"...
        Expects a bytestring; to load from a string instead, specify encoding
        """
        if encoding:
            bytestring = bytestring.encode(encoding)
        xml = XML(bytestring)
        
        dmrs_cfrom = int(xml.get('cfrom'))
        dmrs_cto = int(xml.get('cto'))
        dmrs_surface = xml.get('surface')
        ident = xml.get('ident')
        index = xml.get('index')
        if ident: ident = int(ident)
        if index: index = int(index)
        top = None
        
        nodes = []
        links = []
        
        for elem in xml:
            if elem.tag == 'node':
                nodeid = int(elem.get('nodeid'))
                cfrom = int(elem.get('cfrom'))
                cto = int(elem.get('cto'))
                surface = elem.get('surface')
                base = elem.get('base')
                carg = elem.get('carg')
                
                pred = None
                sortinfo = None
                for sub in elem:
                    if sub.tag == 'realpred':
                        pred = RealPred(sub.get('lemma'),sub.get('pos'),sub.get('sense'))
                    elif sub.tag == 'gpred':
                        pred = GPred(sub.text[:-4])
                    elif sub.tag == 'sortinfo':
                        sortinfo = sub.items()
                    else:
                        raise ValueError(sub.tag)
                
                nodes.append(cls.Node(nodeid, pred, sortinfo, cfrom, cto, surface, base, carg))
            
            elif elem.tag == 'link':
                start = int(elem.get('from'))
                end = int(elem.get('to'))
                
                if start == 0:
                    top = end
                
                else:
                    rargname = None
                    post = None
                    for sub in elem:
                        if sub.tag == 'rargname':
                            rargname = sub.text
                        elif sub.tag == 'post':
                            post = sub.text
                        else:
                            raise ValueError(sub.tag)
                    links.append(Link(start, end, rargname, post))
            else:
                raise ValueError(elem.tag)
        
        return cls(nodes, links, dmrs_cfrom, dmrs_cto, dmrs_surface, ident, index, top)
    
    @classmethod
    def load_xml(cls, filehandle):
        """
        Load a DMRS from a file
        NB: read file as bytes!
        """
        return cls.loads(filehandle.read())
    
    @classmethod
    def dumps_xml(cls, dmrs):
        pass
        # Get the nodes and links, then write them out...
    
    @classmethod
    def dump_xml(cls, filehandle, dmrs):
        """
        Dump a DMRS to a file
        NB: write as a bytestring!
        """
        filehandle.write(cls.dumps(dmrs))
    
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
    def __init__(self, nodes, links, *args, **kwargs):
        """
        Initialise the graph
        """
        self.nodes = []
        self.add_nodes(nodes)  # Allow subclasses to modify this
        self.links = links
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
    
    def add_link(self, link):
        """Add a link"""
        self.links.append(link)
    
    def add_links(self, iterable):
        """Add a number of links"""
        self.links.extend(iterable)
    
    def remove_link(self, link):
        """Remove a link"""
        self.links.remove(link)
    
    def remove_links(self, iterable):
        """Remove a number of links"""
        for link in iterable:
            self.remove_link(link)
    
    def add_node(self, node):
        """Add a node"""
        assert type(node) == self.Node
        self.nodes.append(node)
    
    def add_nodes(self, iterable):
        """Add a number of nodes"""
        for node in iterable:
            self.add_node(node)
        
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
        if self.top.nodeid == nodeid:
            self.top = None
        if self.index.nodeid == nodeid:
            self.index = None
    
    def remove_nodes(self, nodeids):
        """
        Remove a number of nodes and all associated links
        """
        # Remove nodes:
        remove = []
        for i, node in enumerate(self.nodes):
            if node.nodeid in nodeids:
                remove.append(node.nodeid)
        if len(remove) != len(nodeids):
            raise KeyError(nodeids)
        for i in reversed(remove):
            self.nodes.pop(i)
        # Remove links:
        remove = []
        for i, link in enumerate(self.links):
            if link.start in nodeids or link.end in nodeids:
                remove.append(i)
        for i in reversed(remove):
            self.links.pop(i)
        # Check if a node was top or index
        if self.top.nodeid in nodeids:
            self.top = None
        if self.index.nodeid in nodeids:
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
    
    def get_out(self, nodeid, rargname=None, post=None, nodes=False):
        """
        Get links going from a node.
        If rargname or post are specified, filter according to the label.
        If nodes is set to True, return nodes rather than links.
        """
        linkset = self.iter_outgoing(nodeid)
        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)
        if nodes:
            return {self[link.end] for link in linkset}
        else:
            return set(linkset)
    
    def get_in(self, nodeid, rargname=None, post=None, nodes=False):
        """
        Get links coming to a node.
        If rargname or post are specified, filter according to the label.
        If nodes is set to True, return nodes rather than links.
        """
        linkset = self.iter_incoming(nodeid)
        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)
        if nodes:
            return {self[link.start] for link in linkset}
        else:
            return set(linkset)
    
    def get_label(self, rargname=None, post=None):
        """
        Get links, filtered according to the label
        """
        return filter_links(self.links, rargname=rargname, post=post)



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
    def __init__(self, nodes, links, *args, **kwargs):
        """
        Initialise dictionaries from lists
        """
        # Initialise nodes:
        self._nodes = {}
        self.add_nodes(nodes)
        # Initialise links:
        self.outgoing = SetDict()
        self.incoming = SetDict()
        self.add_links(links)
        # Initialise rest:
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
    
    def iter_links(self, sort=True):
        """
        Iterate through all links, by default ordered by start and then end id.
        """
        if sort:
            for _, outset in sorted(self.outgoing.items()):
                for link in sorted(outset, key=attrgetter('end')):
                    yield link
        else:
            for outset in self.outgoing.values():
                for link in outset:
                    yield link
    
    def iter_nodes(self, sort=True):
        """
        Iterate through all nodes, by default ordered by nodeid.
        """
        if sort:
            return iter(self.nodes)
        else:
            return iter(self._nodes.values())
    
    @property
    def links(self):
        """
        Return a list of nodes, ordered by start and then end id.
        """
        return list(self.iter_links())
    
    @property
    def nodes(self):
        """
        Return a list of nodes, ordered by nodeid.
        """
        return sorted(self._nodes.values(), key=attrgetter('nodeid'))
    
    def add_link(self, link):
        """
        Safely add a link.
        """
        if not (link.start in self and link.end in self):
            raise KeyError((link.start, link.end))
        self.outgoing.add(link.start, link)
        self.incoming.add(link.end, link)
    
    def add_links(self, iterable):
        """
        Safely add a number of links
        """
        for link in iterable:
            self.add_link(link)
    
    def remove_link(self, link):
        """
        Safely remove a link.
        """
        self.outgoing.remove(link.start, link)
        self.incoming.remove(link.end, link)
    
    def remove_links(self, iterable):
        """
        Safely remove a number of links.
        """
        for link in iterable:
            self.remove_link(link)
    
    def add_node(self, node):
        """
        Add a node
        """
        assert not node.nodeid in self
        assert type(node) == self.Node
        self._nodes[node.nodeid] = node
    
    def add_nodes(self, iterable):
        """
        Add a number of nodes
        """
        for node in iterable:
            self.add_node(node)
    
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
        if self.top.nodeid == nodeid:
            self.top = None
        if self.index.nodeid == nodeid:
            self.index = None
    
    def remove_nodes(self, iterable):
        """
        Remove a number of nodes and all associated links
        """
        for nodeid in iterable:
            self.remove_node(nodeid)
    
    def get_out(self, nodeid, rargname=None, post=None, nodes=False):
        """
        Get links going from a node.
        If rargname or post are specified, filter according to the label.
        If nodes is set to True, return nodes rather than links.
        """
        linkset = self.outgoing.get(nodeid)
        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)
        if nodes:
            return {self[link.end] for link in linkset}
        else:
            return linkset
    
    def get_in(self, nodeid, rargname=None, post=None, nodes=False):
        """
        Get links coming to a node.
        If rargname or post are specified, filter according to the label.
        If nodes is set to True, return nodes rather than links.
        """
        linkset = self.incoming.get(nodeid)
        if rargname or post:
            linkset = filter_links(linkset, rargname=rargname, post=post)
        if nodes:
            return {self[link.start] for link in linkset}
        else:
            return linkset
    
    def get_label(self, rargname=None, post=None):
        """
        Get links, filtered according to the label
        """
        return filter_links(self.iter_links(), rargname=rargname, post=post)


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
        return {x for x in iterable if x.post == post}
    elif not post:
        return {x for x in iterable if x.rargname == rargname}
    else:
        return {x for x in iterable if x.rargname == rargname and x.post == post}
