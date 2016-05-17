import unittest

from pydmrs.core import span_pred_key, abstractSortDictDmrs, ListDmrs, Node, RealPred, \
    InstanceSortinfo, Link
from pydmrs.examples import examples_dmrs
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
        sorted_nodes = self.the_dog_chases_the_cat.nodes  # sorted because from SortDictDmrs
        nodeids = [1, 5]
        extras = aligned_matching.find_extra_surface_nodeids(nodeids, sorted_nodes)
        self.assertListEqual(extras, [2, 3, 4])

        # No extras.
        sorted_nodes1 = self.the_cat.nodes
        nodeids1 = [4, 5]
        extras1 = aligned_matching.find_extra_surface_nodeids(nodeids1, sorted_nodes1)
        self.assertListEqual(extras1, [])

    def test_get_matching_nodeids(self):
        # Match "the cat" onto "the dog chases the cat" (exact fit)
        matches1 = aligned_matching.get_matching_nodeids(self.the_cat, self.the_dog_chases_the_cat)
        self.assertEqual(len(matches1), 2)
        self.assertCountEqual(matches1[0], [(2, 5), (1, 1)])
        self.assertCountEqual(matches1[1], [(2, 5), (1, 4)])

        # all_surface = True
        all_matches1 = aligned_matching.get_matching_nodeids(self.the_cat,
                                                             self.the_dog_chases_the_cat,
                                                             all_surface=True)
        self.assertListEqual(matches1[1], all_matches1[1])
        # Extra surface nodes
        self.assertCountEqual(all_matches1[0], [(2, 5), (1, 1), (None, 2), (None, 3), (None, 4)])

        # Match "the dog chases the cat" onto "the cat chases the dog" (inexact fit)
        matches2 = aligned_matching.get_matching_nodeids(self.the_dog_chases_the_cat,
                                                         self.the_cat_chases_the_dog)
        self.assertEqual(len(matches2), 1)
        self.assertCountEqual(matches2[0], [(4, 4), (3, 3), (1, 1)])
        all_matches2 = aligned_matching.get_matching_nodeids(self.the_dog_chases_the_cat,
                                                             self.the_cat_chases_the_dog,
                                                             all_surface=True)
        self.assertEqual(len(all_matches2), 1)
        self.assertCountEqual(all_matches2[0], [(4, 4), (3, 3), (1, 1), (None, 2)])

        # No match found
        the_mouse = examples_dmrs.the_mouse() \
            .convert_to(abstractSortDictDmrs(node_key=span_pred_key))
        dog_cat = examples_dmrs.dog_cat() \
            .convert_to(abstractSortDictDmrs(node_key=span_pred_key))
        matches = aligned_matching.get_matching_nodeids(the_mouse, dog_cat)
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
        self.assertEqual(score1, (2, 2, 3))
        subgraph2 = aligned_matching.get_matched_subgraph(matches[1], self.the_dog_chases_the_cat)
        score2 = aligned_matching.get_score(self.the_cat, subgraph2, matches[1])
        self.assertEqual(score2, (3, 3, 3))

        # all_surface = True
        all_surface_matches = aligned_matching.get_matching_nodeids(self.the_cat,
                                                                    self.the_dog_chases_the_cat,
                                                                    all_surface=True)
        subgraph1a = aligned_matching.get_matched_subgraph(all_surface_matches[0],
                                                           self.the_dog_chases_the_cat)
        score1a = aligned_matching.get_score(self.the_cat, subgraph1a, all_surface_matches[0])
        self.assertEqual(score1a, (2, 9, 3))
        subgraph2a = aligned_matching.get_matched_subgraph(all_surface_matches[1],
                                                           self.the_dog_chases_the_cat)
        score2a = aligned_matching.get_score(self.the_cat, subgraph2a, all_surface_matches[1])
        self.assertEqual(score2a, (3, 3, 3))
