def are_equal_nodes(n1, n2):
    """Returns True if nodes n1 and n2 have the same predicate and sortinfo."""
    return n1.pred == n2.pred and n1.sortinfo == n2.sortinfo and n1.carg == n2.carg


def are_equal_links(l1, l2, dmrs1, dmrs2):
    """Returns True if links l1 and l2 have the same link label and their
       starting and ending nodes respectively satisfy are_equal_nodes."""
    if l1.label == l2.label:
        if l1.rargname is None:
            if (are_equal_nodes(dmrs1[l1.start], dmrs2[l2.start]) and
                    are_equal_nodes(dmrs1[l1.end], dmrs2[l2.end])) or (are_equal_nodes(dmrs1[l1.start], dmrs2[l2.end])
                                                                       and are_equal_nodes(dmrs1[l1.end],
                                                                                           dmrs2[l2.start])):
                return True
        else:
            if (are_equal_nodes(dmrs1[l1.start], dmrs2[l2.start]) and
                    are_equal_nodes(dmrs1[l1.end], dmrs2[l2.end])):
                return True
    else:
        return False
