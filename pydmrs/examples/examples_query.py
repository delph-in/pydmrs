from pydmrs.pydelphin_interface import parse
from pydmrs.matching.query import dmrs_query


if __name__ == '__main__':

    # basic functionality
    dmrs_list = [parse('A mouse ate the whole cheese.')[0],
                 parse('Lions eat around 15 zebras per year.')[0],
                 parse('Their children eat so many sweets.')[0],
                 parse('Potatoes are mostly eaten by humans.')[0]]
    search_dmrs_str = '_?1_?_?_rel i <-1- _eat_v_1_rel e? -2-> _?2_?_?_rel i'

    # not dict, not per dmrs
    results = list(dmrs_query(dmrs_list, search_dmrs_str, results_as_dict=False, results_per_dmrs=False))
    assert len(results) == 4
    assert ('mouse', 'cheese') in results
    assert ('lion', 'zebra') in results
    assert ('child', 'sweet') in results
    assert ('human', 'potato') in results
    # dict, not per dmrs
    results = list(dmrs_query(dmrs_list, search_dmrs_str, results_as_dict=True, results_per_dmrs=False))
    assert len(results) == 4
    assert {'1': 'mouse', '2': 'cheese'} in results
    assert {'1': 'lion', '2': 'zebra'} in results
    assert {'1': 'child', '2': 'sweet'} in results
    assert {'1': 'human', '2': 'potato'} in results
    # not dict, per dmrs
    results = list(dmrs_query(dmrs_list, search_dmrs_str, results_as_dict=False, results_per_dmrs=True))
    assert len(results) == 4 and all(isinstance(result, list) for result in results)
    assert ('mouse', 'cheese') in results[0]
    assert ('lion', 'zebra') in results[1]
    assert ('child', 'sweet') in results[2]
    assert ('human', 'potato') in results[3]
    # dict, per dmrs
    results = list(dmrs_query(dmrs_list, search_dmrs_str, results_as_dict=True, results_per_dmrs=True))
    assert len(results) == 4 and all(isinstance(result, list) for result in results)
    assert {'1': 'mouse', '2': 'cheese'} in results[0]
    assert {'1': 'lion', '2': 'zebra'} in results[1]
    assert {'1': 'child', '2': 'sweet'} in results[2]
    assert {'1': 'human', '2': 'potato'} in results[3]
