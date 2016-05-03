from pydmrs.core import Dmrs
from pydmrs.matching.exact_matching import dmrs_exact_matching
from pydmrs.graphlang.graphlang import parse_graphlang


# not all_matches then None if no match
def dmrs_query(dmrs_iter, search_dmrs_str, results_as_dict=False, results_per_dmrs=False):
    """
    Queries DMRS graphs for an underspecified (sub)graph pattern and returns the values of named wildcards (of the form "?[Identifier]") as they are specified in the queried graph.
    :param dmrs_iter An iterator of DMRS graphs to query.
    :param search_dmrs_str The query DMRS (sub)graph, given as a GraphLang string.
    :param results_as_dict True if a query result should be a dictionary, mapping identifiers to values.
    :param results_per_dmrs True if a (possibly empty) list per DMRS should be returned.
    :return Iterator of dicts containing the matching node ids.
    """

    queries = {}
    search_dmrs = parse_graphlang(search_dmrs_str, queries=queries)
    queries = [(key, queries[key]) for key in sorted(queries)]
    for dmrs in dmrs_iter:
        assert isinstance(dmrs, Dmrs), 'Object in dmrs_iter is not a Dmrs.'
        # perform an exact matching of search_dmrs against dmrs
        matchings = dmrs_exact_matching(search_dmrs, dmrs)
        if results_per_dmrs:
            results = []
        for matching in matchings:
            # extract matched values
            if results_as_dict:
                result = {key: query(matching, dmrs) for key, query in queries}
            else:
                result = tuple(query(matching, dmrs) for _, query in queries)
            if results_per_dmrs:
                results.append(result)
            else:
                yield result
        if results_per_dmrs:
            yield results
