from copy import copy
from operator import attrgetter
from collections import deque
from pydmrs.core import Link
from pydmrs._exceptions import PydmrsError

def reverse_link(dmrs, link):
    """
    Reverse a Link in a Dmrs graph.
    The start and end nodeids are switched,
    and "_rev" is appended to the rargname (or removed if already present)
    """
    if link.rargname[-4:] == "_REV":
        new_rargname = link.rargname[:-4]
    else:
        new_rargname = link.rargname + "_REV"
    new_link = Link(link.end, link.start, new_rargname, link.post)
    dmrs.remove_link(link)
    dmrs.add_link(new_link)
    return new_link

def is_root(dmrs, nodeid):
    """
    Check if a node has no incoming links
    """
    return not any(dmrs.get_in(nodeid, itr=True))

def is_leaf(dmrs, nodeid):
    """
    Check if a node has no outgoing links
    """
    return not any(dmrs.get_out(nodeid, itr=True))

def is_singleton(dmrs, nodeid):
    """
    Check if a node has no links
    """
    return not any(dmrs.get_links(nodeid, itr=True))

def iter_roots(dmrs):
    """
    Find all nodes with no incoming links
    """
    for n in dmrs.iter_nodes():
        if is_root(dmrs, n.nodeid):
            yield n

def iter_leaves(dmrs):
    """
    Find all nodes with no outgoing links
    """
    for n in dmrs.iter_nodes():
        if is_leaf(dmrs, n.nodeid):
            yield n

def is_rooted(dmrs, check_connected=True):
    """
    Check if a dmrs has a single root
    """
    if check_connected and not dmrs.is_connected():
        return False
    return any(iter_roots(dmrs))

def is_acyclic(dmrs):
    """
    Check if the graph is acyclic
    """
    return not find_cycle(dmrs)

def find_cycle(dmrs):
    """
    If there is a cycle, return the nodeids in the largest subgraph with no roots or leaves.
    If there is no cycle, return False 
    """
    # There are no cycles iff iteratively removing all leaves leaves nothing
    trim_leaves = trimmable(dmrs, leaves=True)
    if len(trim_leaves) == len(dmrs):
        return False
    
    # If there is a cycle, do the same with roots
    trim_roots = trimmable(dmrs, leaves=False)
    return {n.nodeid for n in dmrs.iter_nodes()} - trim_leaves - trim_roots
     

def trimmable(dmrs, leaves=True):
    """
    Return the nodeids that can be removed by recursively trimming
    If leaves is True (by default), trim leaves; if False, trim roots
    """
    if leaves:
        initial = iter_leaves
        forward = dmrs.get_in_nodes
        back = dmrs.get_out_nodes
    else:
        initial = iter_roots
        forward = dmrs.get_out_nodes
        back = dmrs.get_in_nodes
    
    # Iteratively remove all leaves from the graph
    discard = {n.nodeid for n in initial(dmrs)}
    parents = {p for leaf in discard \
               for p in forward(leaf, nodeids=True, itr=True)}
    n = True
    while n:  # Keep removing leaves until we can't remove any more
        n = 0  # Count how many leaves we can remove in this pass
        next_parents = set()  # Parents for the next iteration
        for mother in parents:
            if back(mother, nodeids=True) - discard:  # Has non-leaf children
                next_parents.add(mother)
            else:
                n += 1
                discard.add(mother)
                next_parents.update(forward(mother, nodeids=True, itr=True))
        parents = next_parents
    
    return discard

def connected_pair(dmrs, first_id, second_id):
    """
    Check if a pair of nodes are connected to each other
    """
    cover = set()  # Nodes reachable from the first node
    queue = {first_id}  # Queue of nodes to explore
    while queue:
        new = queue.pop()
        cover.add(new)
        for adjacent in dmrs.get_neighbours(new, nodeids=True, itr=True):
            if adjacent == second_id:
                return True
            elif adjacent not in cover:
                queue.add(adjacent)
    return False

def components(dmrs):
    """
    Find out how many connected components are in the graph
    """
    comps = 0  # Number of connected components
    nodeids = {n.nodeid for n in dmrs.iter_nodes()}
    queue = copy(nodeids)  # Queue of nodes to explore
    while queue:
        comps += 1
        queue = dmrs.disconnected_nodeids(removed_nodeids=(nodeids - queue))
    return comps

def iter_bottom_up(dmrs, check_acyclic=True, node_key=None):
    """
    Iterate through the graph bottom up,
    i.e. nodes are only returned once all their children have been.
    By default, raises an error if the graph has cycles.
    By default, nodes are sorted by nodeid (or for SortDictDmrs, by node_key)
    """
    if check_acyclic and not is_acyclic(dmrs):
        raise PydmrsError
    if node_key is None:
        if hasattr(dmrs, 'node_key'):
            node_key = dmrs.node_key
        else:
            node_key = attrgetter('nodeid')

    returned = set()  # Nodeids that have already been yielded
    queue = deque(sorted(iter_leaves(dmrs), key=node_key))  # Nodes to be considered next
    while queue:
        new = queue.popleft()
        if dmrs.get_out_nodes(new.nodeid, nodeids=True) - returned:  # If the node has children yet to be returned
            queue.append(new)  # Put back on the queue
        else:
            returned.add(new.nodeid)
            for parent in sorted(dmrs.get_in_nodes(new.nodeid, itr=True), key=node_key):
                if parent.nodeid not in returned and parent not in queue:
                    queue.append(parent)
            yield new
