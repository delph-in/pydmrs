from pydmrs.core import Link

def reverse_link(dmrs, link):
    """
    Reverse a Link in a Dmrs graph.
    The start and end nodeids are switched,
    and "_rev" is appended to the rargname (or removed if already present)
    """
    if link.rargname[-4:] == "_rev":
        new_rargname = link.rargname[:-4]
    else:
        new_rargname = link.rargname + "_rev"
    new_link = Link(link.end, link.start, new_rargname, link.post)
    dmrs.remove_link(link)
    dmrs.add_link(new_link)
    return new_link

def is_root(dmrs, nodeid):
    """
    Check if a node has no incoming links
    """
    for _ in dmrs.get_in(nodeid, itr=True):
        return False
    return True

def is_leaf(dmrs, nodeid):
    """
    Check if a node has no outgoing links
    """
    for _ in dmrs.get_out(nodeid, itr=True):
        return False
    return True

def is_singleton(dmrs, nodeid):
    """
    Check if a node has no links
    """
    for _ in dmrs.get_links(nodeid, itr=True):
        return False
    return True

def iter_roots(dmrs):
    """
    Find all nodes with no incoming links
    """
    for n in dmrs.iter_nodes():
        if is_root(dmrs, n):
            yield n

def iter_leaves(dmrs):
    """
    Find all nodes with no outgoing links
    """
    for n in dmrs.iter_nodes():
        if is_leaf(dmrs, n):
            yield n