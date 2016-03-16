from pydmrs.core import Dmrs
from pydmrs.matching.exact_matching import dmrs_exact_matching
from pydmrs.develop.graphlang import parse_graphlang


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


if __name__ == '__main__':
    from pydmrs.core import ListDmrs

    # Example sentences:
    # A mouse ate the whole cheese.
    # Lions eat around 15 zebras per year.
    # Their children eat so many sweets.
    # Potatoes are mostly eaten by humans.
    dmrs_iter = [ListDmrs.loads_xml('<dmrs cfrom="-1" cto="-1"><node cfrom="0" cto="1" nodeid="10000"><realpred lemma="a" pos="q" /><sortinfo /></node><node cfrom="2" cto="7" nodeid="10001"><realpred lemma="mouse" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="sg" pers="3" /></node><node cfrom="8" cto="11" nodeid="10002"><realpred lemma="eat" pos="v" sense="1" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="past" /></node><node cfrom="12" cto="15" nodeid="10003"><realpred lemma="the" pos="q" /><sortinfo /></node><node cfrom="16" cto="21" nodeid="10004"><realpred lemma="whole" pos="a" sense="1" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="bool" sf="prop" tense="untensed" /></node><node cfrom="22" cto="29" nodeid="10005"><realpred lemma="cheese" pos="n" sense="1" /><sortinfo cvarsort="x" num="sg" pers="3" /></node><link from="0" to="10002"><rargname /><post>H</post></link><link from="10000" to="10001"><rargname>RSTR</rargname><post>H</post></link><link from="10002" to="10001"><rargname>ARG1</rargname><post>NEQ</post></link><link from="10002" to="10005"><rargname>ARG2</rargname><post>NEQ</post></link><link from="10003" to="10005"><rargname>RSTR</rargname><post>H</post></link><link from="10004" to="10005"><rargname>ARG1</rargname><post>EQ</post></link></dmrs>'), ListDmrs.loads_xml('<dmrs cfrom="-1" cto="-1"><node cfrom="0" cto="5" nodeid="10000"><gpred>udef_q_rel</gpred><sortinfo /></node><node cfrom="0" cto="5" nodeid="10001"><realpred lemma="lion" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="pl" pers="3" /></node><node cfrom="6" cto="9" nodeid="10002"><realpred lemma="eat" pos="v" sense="1" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="pres" /></node><node cfrom="10" cto="16" nodeid="10003"><realpred lemma="around" pos="x" sense="deg" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="untensed" /></node><node cfrom="17" cto="19" nodeid="10004"><gpred>udef_q_rel</gpred><sortinfo /></node><node carg="&quot;15&quot;" cfrom="17" cto="19" nodeid="10005"><gpred>card_rel</gpred><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="untensed" /></node><node cfrom="20" cto="26" nodeid="10006"><realpred lemma="zebra" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="pl" pers="3" /></node><node cfrom="27" cto="30" nodeid="10007"><realpred lemma="per" pos="p" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="untensed" /></node><node cfrom="27" cto="30" nodeid="10008"><gpred>udef_q_rel</gpred><sortinfo /></node><node cfrom="31" cto="36" nodeid="10009"><realpred lemma="year" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="sg" pers="3" /></node><link from="0" to="10002"><rargname /><post>H</post></link><link from="10000" to="10001"><rargname>RSTR</rargname><post>H</post></link><link from="10002" to="10001"><rargname>ARG1</rargname><post>NEQ</post></link><link from="10002" to="10006"><rargname>ARG2</rargname><post>NEQ</post></link><link from="10003" to="10005"><rargname>ARG1</rargname><post>EQ</post></link><link from="10004" to="10006"><rargname>RSTR</rargname><post>H</post></link><link from="10005" to="10006"><rargname>ARG1</rargname><post>EQ</post></link><link from="10007" to="10006"><rargname>ARG1</rargname><post>EQ</post></link><link from="10007" to="10009"><rargname>ARG2</rargname><post>NEQ</post></link><link from="10008" to="10009"><rargname>RSTR</rargname><post>H</post></link></dmrs>'), ListDmrs.loads_xml('<dmrs cfrom="-1" cto="-1"><node cfrom="0" cto="5" nodeid="10000"><gpred>def_explicit_q_rel</gpred><sortinfo /></node><node cfrom="0" cto="5" nodeid="10001"><gpred>poss_rel</gpred><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="untensed" /></node><node cfrom="0" cto="5" nodeid="10002"><gpred>pronoun_q_rel</gpred><sortinfo /></node><node cfrom="0" cto="5" nodeid="10003"><gpred>pron_rel</gpred><sortinfo cvarsort="x" num="pl" pers="3" pt="std" /></node><node cfrom="6" cto="14" nodeid="10004"><realpred lemma="child" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="pl" pers="3" /></node><node cfrom="15" cto="18" nodeid="10005"><realpred lemma="eat" pos="v" sense="1" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="pres" /></node><node cfrom="19" cto="34" nodeid="10006"><gpred>udef_q_rel</gpred><sortinfo /></node><node cfrom="19" cto="21" nodeid="10007"><gpred>comp_so_rel</gpred><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="untensed" /></node><node cfrom="22" cto="26" nodeid="10008"><gpred>much-many_a_rel</gpred><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="untensed" /></node><node cfrom="27" cto="34" nodeid="10009"><realpred lemma="sweet" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="pl" pers="3" /></node><link from="0" to="10005"><rargname /><post>H</post></link><link from="10000" to="10004"><rargname>RSTR</rargname><post>H</post></link><link from="10001" to="10003"><rargname>ARG2</rargname><post>NEQ</post></link><link from="10001" to="10004"><rargname>ARG1</rargname><post>EQ</post></link><link from="10002" to="10003"><rargname>RSTR</rargname><post>H</post></link><link from="10005" to="10004"><rargname>ARG1</rargname><post>NEQ</post></link><link from="10005" to="10009"><rargname>ARG2</rargname><post>NEQ</post></link><link from="10006" to="10009"><rargname>RSTR</rargname><post>H</post></link><link from="10007" to="10008"><rargname>ARG1</rargname><post>EQ</post></link><link from="10008" to="10009"><rargname>ARG1</rargname><post>EQ</post></link></dmrs>'), ListDmrs.loads_xml('<dmrs cfrom="-1" cto="-1"><node cfrom="0" cto="8" nodeid="10000"><gpred>udef_q_rel</gpred><sortinfo /></node><node cfrom="0" cto="8" nodeid="10001"><realpred lemma="potato" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="pl" pers="3" /></node><node cfrom="13" cto="19" nodeid="10002"><realpred lemma="mostly" pos="a" sense="1" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="untensed" /></node><node cfrom="20" cto="25" nodeid="10003"><realpred lemma="eat" pos="v" sense="1" /><sortinfo cvarsort="e" mood="indicative" perf="-" prog="-" sf="prop" tense="pres" /></node><node cfrom="29" cto="36" nodeid="10004"><gpred>udef_q_rel</gpred><sortinfo /></node><node cfrom="29" cto="36" nodeid="10005"><realpred lemma="human" pos="n" sense="1" /><sortinfo cvarsort="x" ind="+" num="pl" pers="3" /></node><link from="0" to="10003"><rargname /><post>H</post></link><link from="10000" to="10001"><rargname>RSTR</rargname><post>H</post></link><link from="10002" to="10003"><rargname>ARG1</rargname><post>EQ</post></link><link from="10003" to="10001"><rargname>ARG2</rargname><post>NEQ</post></link><link from="10003" to="10005"><rargname>ARG1</rargname><post>NEQ</post></link><link from="10004" to="10005"><rargname>RSTR</rargname><post>H</post></link></dmrs>')]

    search_dmrs_str = '_?1_?_?_rel i <-1- _eat_v_1_rel e? -2-> _?2_?_?_rel i'
    print('- not dict, not per dmrs:', list(dmrs_query(dmrs_iter, search_dmrs_str, results_as_dict=False, results_per_dmrs=False)))
    print('- dict, not per dmrs:', list(dmrs_query(dmrs_iter, search_dmrs_str, results_as_dict=True, results_per_dmrs=False)))
    print('- not dict, per dmrs:', list(dmrs_query(dmrs_iter, search_dmrs_str, results_as_dict=False, results_per_dmrs=True)))
    print('- dict, per dmrs:', list(dmrs_query(dmrs_iter, search_dmrs_str, results_as_dict=True, results_per_dmrs=True)))
