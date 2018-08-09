from pydmrs._exceptions import PydmrsTypeError


def get_recall(match, dmrs):
    from pydmrs.matching.general_matching import Match
    if isinstance(match, list) and isinstance(match[0], Match):
        raise PydmrsTypeError("More than one match passed in an argument.")
    return len(match) / (len(dmrs.nodes) + len(dmrs.links))


def get_fscore(match, dmrs):
    # Precision always 1.0. for this algorithm.
    recall = get_recall(match, dmrs)
    return 2 * recall / (1.0 + recall)


def get_missing_elements(match, dmrs):
    """ Returns a list of elements of dmrs for which no match was found.:
        :param match A Match object.
        :param dmrs A DMRS object for which the match was searched.
        :return A list of nodeids and links.
    """
    matched_nodeids = list(zip(*match.nodeid_pairs))[1]
    matched_links = list(zip(*match.link_pairs))[1]
    not_matched = []
    for nodeid in dmrs:
        if nodeid not in matched_nodeids:
            not_matched.append(nodeid)
    for link in dmrs.iter_links():
        if link not in matched_links:
            not_matched.append(link)
    return not_matched
