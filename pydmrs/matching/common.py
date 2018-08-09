def are_equal_nodes(n1, n2, underspecified=True):
    """Returns True if nodes n1 and n2 have the same predicate and sortinfo. If underspecified,
    allow underspecification."""
    if underspecified:
        if n1.is_less_specific(n2) or n2.is_less_specific(n1):
            return True
    return n1.pred == n2.pred and n1.sortinfo == n2.sortinfo and n1.carg == n2.carg


def are_equal_links(l1, l2, dmrs1, dmrs2, underspecified=True):
    """Returns True if links l1 and l2 have the same link label and their
       starting and ending nodes respectively satisfy are_equal_nodes."""
    if l1.label == l2.label:
        if l1.rargname is None:
            if (are_equal_nodes(dmrs1[l1.start], dmrs2[l2.start], underspecified) and
                    are_equal_nodes(dmrs1[l1.end], dmrs2[l2.end], underspecified)) or (
                        are_equal_nodes(dmrs1[l1.start], dmrs2[l2.end], underspecified)
                    and are_equal_nodes(dmrs1[l1.end],
                                        dmrs2[l2.start], underspecified)):
                return True
        else:
            if (are_equal_nodes(dmrs1[l1.start], dmrs2[l2.start], underspecified) and
                    are_equal_nodes(dmrs1[l1.end], dmrs2[l2.end], underspecified)):
                return True
    else:
        return False
