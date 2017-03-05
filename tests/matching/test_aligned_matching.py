import unittest

from examples import examples_dmrs
from pydmrs.core import span_pred_key, abstractSortDictDmrs, ListDmrs, Node, RealPred, \
    InstanceSortinfo, Link
from pydmrs.matching import aligned_matching


class TestAlignedMatching(unittest.TestCase):
    def setUp(self):
        self.the_cat = examples_dmrs.the_cat().convert_to(
            abstractSortDictDmrs(node_key=span_pred_key))
        # Checks if the matching code converts to SortDictDmrs with span_pred_key
        self.the_cat_chases_the_dog = examples_dmrs.the_cat_chases_the_dog().convert_to(
            abstractSortDictDmrs(node_key=span_pred_key))
        self.the_dog_chases_the_cat = examples_dmrs.the_dog_chases_the_cat().convert_to(
            abstractSortDictDmrs(node_key=span_pred_key))
        self.the_mouse = examples_dmrs.the_mouse() \
            .convert_to(abstractSortDictDmrs(node_key=span_pred_key))
        self.dog_cat = examples_dmrs.dog_cat() \
            .convert_to(abstractSortDictDmrs(node_key=span_pred_key))
        # All other DMRS used here should udnergo conversion as well.

    def test_match_nodes(self):
        nodes1 = self.the_dog_chases_the_cat.nodes
        nodes2 = self.the_cat_chases_the_dog.nodes
        matches = aligned_matching.match_nodes(nodes1, nodes2)
        self.assertEqual(len(matches), 1)
        self.assertListEqual(matches[0], [(4, 4), (3, 3), (1, 1)])

        # Return [] if either of the nodes list empty.
        self.assertListEqual(aligned_matching.match_nodes([], nodes1), [])
        self.assertListEqual(aligned_matching.match_nodes(nodes1, []), [])

        nodes3 = self.the_cat.nodes
        matches = aligned_matching.match_nodes(nodes3, nodes1)
        self.assertEqual(len(matches), 2)
        self.assertListEqual(matches[0], [(2, 5), (1, 1)])
        self.assertListEqual(matches[1], [(2, 5), (1, 4)])

    def test_find_extra_surface_nodeids(self):
        nodeids = [1, 5]
        extras = aligned_matching.find_extra_surface_nodeids(nodeids, self.the_dog_chases_the_cat)
        self.assertListEqual(extras, [2, 3, 4])

        # No extras.
        nodeids1 = [1, 2]
        extras1 = aligned_matching.find_extra_surface_nodeids(nodeids1, self.the_cat)
        self.assertListEqual(extras1, [])

    def test_get_matching_nodeids(self):
        # Match "the cat" onto "the dog chases the cat" (exact fit, only one match)
        matches1 = aligned_matching.get_matching_nodeids(self.the_cat, self.the_dog_chases_the_cat)
        self.assertEqual(len(matches1), 1)
        self.assertCountEqual(matches1[0], [(2, 5), (1, 4)])

        # all_surface = True
        all_matches1 = aligned_matching.get_matching_nodeids(self.the_cat,
                                                             self.the_dog_chases_the_cat,
                                                             all_surface=True)
        # The same as earlier
        self.assertListEqual(matches1[0], all_matches1[0])
        # Extra surface nodes: between dog and cat

        all_matches1 = aligned_matching.get_matching_nodeids(self.dog_cat,
                                                             self.the_dog_chases_the_cat,
                                                             all_surface=True)
        self.assertCountEqual(all_matches1[0], [(2, 5), (1, 2), (None, 3), (None, 4)])

        # Match "the dog chases the cat" onto "the cat chases the dog" (inexact fit)
        matches2 = aligned_matching.get_matching_nodeids(self.the_dog_chases_the_cat,
                                                         self.the_cat_chases_the_dog)
        # Two options: "the dog" matches or "the cat" matches, 'chases' doesn't because it's not part of the longest match
        self.assertEqual(len(matches2), 2)
        self.assertCountEqual(matches2, [[(5, 2), (4, 1)], [(2, 5), (1, 4)]])

        # No match found
        matches = aligned_matching.get_matching_nodeids(self.the_mouse, self.dog_cat)
        self.assertListEqual(matches, [])

        # Should be the same as 'the cat'.
        mixed_cat = ListDmrs(surface='the cat')
        mixed_cat.add_node(Node(nodeid=2, pred=RealPred('cat', 'n', '1'), cfrom=4, cto=7,
                                sortinfo=InstanceSortinfo(pers='3', num='sg', ind='+')))
        mixed_cat.add_node(Node(nodeid=1, pred=RealPred('the', 'q'), cfrom=0, cto=3))
        mixed_cat.add_link(Link(start=1, end=2, rargname='RSTR', post='H'))
        mixed = aligned_matching.get_matching_nodeids(mixed_cat, self.the_dog_chases_the_cat)
        self.assertListEqual(mixed, matches1)

    def test_get_score(self):
        matches = aligned_matching.get_matching_nodeids(self.the_cat, self.the_dog_chases_the_cat)
        subgraph1 = aligned_matching.get_matched_subgraph(matches[0], self.the_dog_chases_the_cat)
        score1 = aligned_matching.get_score(self.the_cat, subgraph1, matches[0])
        self.assertEqual(score1, (3, 3, 3))  # 'the', 'cat' and the link

        # all_surface = True
        all_surface_matches = aligned_matching.get_matching_nodeids(self.dog_cat,
                                                                    self.the_dog_chases_the_cat,
                                                                    all_surface=True)
        subgraph1a = aligned_matching.get_matched_subgraph(all_surface_matches[0],
                                                           self.the_dog_chases_the_cat)
        score1a = aligned_matching.get_score(self.the_cat, subgraph1a, all_surface_matches[0])
        self.assertEqual(score1a, (2, 7, 3))
