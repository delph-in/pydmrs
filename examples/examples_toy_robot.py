from copy import copy

from pydmrs.core import Link, LinkLabel
from pydmrs.components import Pred, RealPred
from pydmrs.simplification.gpred_filtering import gpred_filtering
from pydmrs.simplification.simplification import DEFAULT_CONFIG_FILE, ConfigParser, get_config_option, parse_gpred_filter_config
#from pydmrs.mapping.mapping import dmrs_mapping
from pydmrs.graphlang.graphlang import parse_graphlang

config = ConfigParser()
assert DEFAULT_CONFIG_FILE[:3] == '../'
config.read(DEFAULT_CONFIG_FILE[3:])
gpred_filter_config = get_config_option(config, 'General Predicate Filtering', 'filter')
gpred_filter = parse_gpred_filter_config(gpred_filter_config)
# Also remove pronouns
gpred_filter.append('pron')

# Replace the first pred with the second:
rename = [(RealPred('forwards','p'), RealPred('forward','p','dir'))]

# Replace a pair of nodes with a single node
# (the first pred linked to the second pred, is replaced by the third pred)
shrink = [('_left_a_1', 'ARG1/EQ', 'place_n', '_left_n_1'),
          ('_right_a_1', 'ARG1/EQ', 'place_n', '_right_n_1'),
          ('loc_nonsp', 'ARG2/NEQ', '_left_n_1', '_left_p_dir'),
          ('loc_nonsp', 'ARG2/NEQ', '_right_n_1', '_right_p_dir'),
          ('_to_p', 'ARG2/NEQ', '_left_n_1', '_left_p_dir'),
          ('_to_p', 'ARG2/NEQ', '_right_n_1', '_right_p_dir')]

shrink = [(Pred.from_string(a),
           LinkLabel.from_string(b),
           Pred.from_string(c),
           Pred.from_string(d)) for a,b,c,d in shrink]

def simplify(dmrs):
    """
    Simplify an input DMRS to a form that can be converted to robot commands
    """
    # Remove unnecessary GPreds (defaults, plus pronouns)
    gpred_filtering(dmrs, gpred_filter)
    
    # Remove quantifiers
    for node in copy(dmrs.nodes):
        if dmrs.is_quantifier(node.nodeid):
            dmrs.remove_node(node.nodeid)
    
    # Apply mapping rules
    for before, after in rename:
        for node in dmrs.iter_nodes():
            if node.pred == before:
                node.pred = after
    
    for first, label, second, new in shrink:
        for node in copy(dmrs.nodes):
            if node.pred == first:
                nid = node.nodeid
                for link in dmrs.get_out(nid, rargname=label.rargname, post=label.post):
                    if dmrs[link.end].pred == second:
                        # We've found a match 
                        endid = link.end
                        dmrs.remove_link(link)
                        # Copy links from second node to first
                        for old_link in dmrs.get_out(endid):
                            dmrs.add_link(Link(nid, old_link.end, old_link.rargname, old_link.post))
                        for old_link in dmrs.get_in(endid):
                            dmrs.add_link(Link(old_link.start, nid, old_link.rargname, old_link.post))
                        # Remove the second node and update the first
                        dmrs.remove_node(link.end)
                        dmrs[nid].pred = new
    
    return dmrs


dmrsstring = '''
_then_c -L-HNDL/H-> _drive_v_1 <-L-INDEX/NEQ- :_then_c -R-HNDL/H-> _turn_v_1 <-R-INDEX/NEQ- :_then_c;
pronoun_q -RSTR/H-> pron <-1- :_drive_v_1 <=1= _forwards_p;
pronoun_q -RSTR/H-> pron <-1- :_turn_v_1 <=1= loc_nonsp -2-> place_n <-RSTR/H- def_implicit_q;
_left_a_1 =1=> :place_n
'''
dmrs = parse_graphlang(dmrsstring)
dmrs.surface = 'Drive forwards then turn left'

print([(n.nodeid, n.pred) for n in dmrs.nodes])
print(dmrs.links)

simplify(dmrs)

print()
print([(n.nodeid, n.pred) for n in dmrs.nodes])
print(dmrs.links)

'Go forward and then turn to the left'
'Turn left at a yellow line'
'On a yellow line, turn to the left'