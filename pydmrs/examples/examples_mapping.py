from pydmrs.pydelphin_interface import parse, generate
from pydmrs.mapping.mapping import dmrs_mapping
from pydmrs.graphlang.graphlang import parse_graphlang
import pydmrs.examples.examples_dmrs as examples


if __name__ == '__main__':

    # basic functionality
    dmrs = examples.the_dog_chases_the_cat()
    search_dmrs = parse_graphlang('[1]:_the_q')
    replace_dmrs = parse_graphlang('[1]:_a_q')

    # iterative, all
    assert 'A dog chases a cat.' in generate(dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=True, iterative=True, all_matches=True))
    # not iterative, all
    assert all(sent in sents for sent, sents in zip(['A dog chases the cat.', 'The dog chases a cat.'], [generate(dmrs) for dmrs in dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=True, iterative=False, all_matches=True)]))
    # iterative, not all
    assert 'A dog chases the cat.' in generate(dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=True, iterative=True, all_matches=False))
    # not iterative, not all
    assert 'A dog chases the cat.' in generate(dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=True, iterative=False, all_matches=False))
    # original dmrs did not change so far
    assert 'The dog chases the cat.' in generate(dmrs)
    # iterative, not all
    dmrs = examples.the_dog_chases_the_cat()
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False, iterative=True, all_matches=False)
    assert 'A dog chases the cat.' in generate(dmrs)
    # iterative, all
    dmrs = examples.the_dog_chases_the_cat()
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False, iterative=True, all_matches=True)
    assert 'A dog chases a cat.' in generate(dmrs)


    # some examples inspired by examples from the AMR specification

    dmrs = parse('He described the mission as a failure.')[0]
    search_dmrs = parse_graphlang('[2]:node <-2- *[1]:_describe_v_as e? -3-> [3]:node')
    replace_dmrs = parse_graphlang('pronoun_q --> pron x[3sn_s] <-2- [1]:_describe_v_to e? <-2h- *_as_x_subord e[pui--] -1h-> _be_v_id e[ppi--] -1-> [2]:node; :_be_v_id -2-> [3]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'As he described it, the mission is a failure.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'He described the mission as a failure.' in generate(dmrs)

    dmrs = parse('The boy can go.')[0]
    search_dmrs = parse_graphlang('[1]:_can_v_modal e[p????] -1h-> [2]:_v e[pui--]')
    replace_dmrs = parse_graphlang('[1]:_possible_a_for e[o????] -1h-> [2]:_v e[ppi--]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'It is possible that the boy goes.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The boy can go.' in generate(dmrs)

    dmrs = parse('The boy can\'t go.')[0]
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'It is not possible that the boy goes.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The boy can\'t go.' in generate(dmrs)

    dmrs = parse('The boy must go.')[0]
    search_dmrs = parse_graphlang('[1]:_must_v_modal e? -1h-> [2]:_v e[pui--]')
    replace_dmrs = parse_graphlang('[1]:_necessary_a_for e? -1h-> [2]:_v e[ppi--]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'It is necessary that the boy goes.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The boy must go.' in generate(dmrs)

    dmrs = parse('The boy should go.')[0]
    search_dmrs = parse_graphlang('[1]:_should_v_modal e? -1h-> [2]:_v e[pui--]')
    replace_dmrs = parse_graphlang('[1]:_recommend_v_to e? -2h-> [2]:_v e[ppi--]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'That the boy goes, is recommended.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The boy should go.' in generate(dmrs)

    dmrs = parse('The boy is likely to go.')[0]
    search_dmrs = parse_graphlang('[1]:_likely_a_1 e? -1h-> [2]:_v e[oui--]')
    replace_dmrs = parse_graphlang('[1]:_likely_a_1 e? -1h-> [2]:_v e[ppi--]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'It is likely that the boy goes.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The boy is likely to go.' in generate(dmrs)

    dmrs = parse('The boy would rather go.')[0]
    search_dmrs = parse_graphlang('[1]:_would_v_modal e? -1h-> [2]:_v e? <=1= _rather_a_1 i; :2 -1-> [3]:node')
    replace_dmrs = parse_graphlang('[1]:_prefer_v_to e? -2h-> [2]:_v e? -1-> [3]:node <-1- :1')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'The boy prefers to go.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The boy would rather go.' in generate(dmrs)

    dmrs = parse('I don\'t have any money.')[0]
    search_dmrs = parse_graphlang('neg e[pui--] -1h-> [1]:_v e? -2-> [2]:node <-- _any_q')
    replace_dmrs = parse_graphlang('[1]:_v e? -2-> [2]:node <-- _no_q')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I have no money.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I don\'t have any money.' in generate(dmrs)

    dmrs = parse('Kim doesn\'t like any cake.')[0]
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Kim likes no cake.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Kim doesn\'t like any cake.' in generate(dmrs)

    dmrs = parse('The boy doesn\'t think his team will win.')[0]
    search_dmrs = parse_graphlang('neg e[pui--] -1h-> [1]:_v e? -2h-> [2]:_v e?')
    replace_dmrs = parse_graphlang('[1]:_v e? -2h-> neg e[pui--] -1h-> [2]:_v e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'The boy thinks his team won\'t win.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The boy doesn\'t think his team will win.' in generate(dmrs)

    dmrs = parse('I don\'t believe that Kim likes cake.')[0]
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I believe that Kim doesn\'t like cake.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I don\'t believe that Kim likes cake.' in generate(dmrs)

    dmrs = parse('I don\'t think that Kim doesn\'t like cake.')[0]
    search_dmrs = parse_graphlang('neg e[pui--] -1h-> [1]:_v e? -2h-> neg e[pui--] -1h-> [2]:_v e?')
    replace_dmrs = parse_graphlang('[1]:_v e? -2h-> [2]:_v e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I think that Kim likes cake.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I don\'t think that Kim doesn\'t like cake.' in generate(dmrs)


    # Verb particle examples

    dmrs = parse('I look you up.')[0]
    search_dmrs = parse_graphlang('[1]:_look_v_up e?')
    replace_dmrs = parse_graphlang('[1]:_find_v_1 e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I find you.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I look you up.' in generate(dmrs)

    dmrs = parse('Kim carries on eating cake.')[0]
    search_dmrs = parse_graphlang('[1]:_carry_v_on e?')
    replace_dmrs = parse_graphlang('[1]:_continue_v_2 e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Kim continues eating cake.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Kim carries on eating cake.' in generate(dmrs)

    dmrs = parse('Alice passed a message on to Bob.')[0]
    search_dmrs = parse_graphlang('[1]:_pass_v_on e?')
    replace_dmrs = parse_graphlang('[1]:_give_v_1 e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Alice gave a message to Bob.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Alice passed a message on to Bob.' in generate(dmrs)

    dmrs = parse('Bob then gave Alice back the message.')[0]
    search_dmrs = parse_graphlang('[1]:node <-2- [2]:_give_v_back e? -3-> [3]:node')
    replace_dmrs = parse_graphlang('[3]:node <-2- [2]:_return_v_to e? -3-> [1]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Bob then returned the message to Alice.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Bob then gave Alice back the message.' in generate(dmrs)

    dmrs = parse('He keeps on complaining.')[0]
    search_dmrs = parse_graphlang('[2]:node <-1- [1]:_keep_v_on e? -2h-> [3]:_v e[pui-+] -1-> :2')
    replace_dmrs = parse_graphlang('[1]:_continue_v_2 e? -1h-> [3]:_v e[oui--] -1-> [2]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'He continues to complain.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'He keeps on complaining.' in generate(dmrs)

    dmrs = parse('He takes on great responsibility.')[0]
    search_dmrs = parse_graphlang('[1]:_take_v_on e?')
    replace_dmrs = parse_graphlang('[1]:_accept_v_1 e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'He accepts great responsibility.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'He takes on great responsibility.' in generate(dmrs)


    # determinerless PPs

    dmrs = parse('I found you at last.')[0]
    search_dmrs = parse_graphlang('[1]:_at_p e[pui--] -2-> _last_n_1 x[3s_+_] <-- idiom_q_i')
    replace_dmrs = parse_graphlang('[1]:_final_a_1 e[pui--]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I found you finally.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I found you at last.' in generate(dmrs)

    dmrs = parse('I am on edge.')[0]
    search_dmrs = parse_graphlang('[1]:_on_p e? -2-> _edge_n_of x[3s_+_] <-- idiom_q_i')
    replace_dmrs = parse_graphlang('[1]:_nervous_a_about e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I am nervous.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I am on edge.' in generate(dmrs)

    dmrs = parse('You can see the insects at close range.')[0]
    search_dmrs = parse_graphlang('[1]:_at_p e[pui--] -2-> _range_n_of x[3s___] <-- udef_q; :_range_n_of <=1= _close_a_to e[p____]')
    replace_dmrs = parse_graphlang('[1]:_from_p_state e[pui--] -2-> _distance_n_1 x[3s_+_] <-- _a_q; :_distance_n_1 <=1= _small_a_1 e[p____]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'You can see the insects from a small distance.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'You can see the insects at close range.' in generate(dmrs)


    # idioms

    dmrs = parse('Kim often took advantage of Sandy.')[0]
    search_dmrs = parse_graphlang('[2]:node <-3- [1]:_take_v_of-i e? -2-> _advantage_n_i x[3s_+_] <-- idiom_q_i')
    replace_dmrs = parse_graphlang('[1]:_benefit_v_from e? -2-> [2]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Kim often benefitted from Sandy.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Kim often took advantage of Sandy.' in generate(dmrs)

    dmrs = parse('The government keeps tabs on everyone.')[0]
    search_dmrs = parse_graphlang('[2]:node <-3- [1]:_keep_v_on-i e? -2-> _tabs_n_i x[3p_+_] <-- udef_q')
    replace_dmrs = parse_graphlang('[1]:_watch_v_1 e? -2-> [2]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'The government watches everyone.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The government keeps tabs on everyone.' in generate(dmrs)

    dmrs = parse('I can give you a hand with your work.')[0]
    search_dmrs = parse_graphlang('[2]:node <-3- [1]:_give_v_1 e? -2-> _hand_n_1 x[3s_+_] <-- _a_q')
    replace_dmrs = parse_graphlang('[1]:_help_v_1 e? -2-> [2]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I can help you with your work.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I can give you a hand with your work.' in generate(dmrs)

    dmrs = parse('The old senator kicked the bucket.')[0]
    search_dmrs = parse_graphlang('[1]:_kick_v_i e? -2-> _bucket_n_1 x[3s_+_] <-- _the_q')
    replace_dmrs = parse_graphlang('[1]:_die_v_1 e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'The old senator died.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'The old senator kicked the bucket.' in generate(dmrs)


    # light verbs

    dmrs = parse('I give a talk on linguistics.')[0]
    search_dmrs = parse_graphlang('[1]:_give_v_1 e? -2-> _talk_n_of-on x[3s_+_] <-- _a_q; :_talk_n_of-on -1-> [2]:node')
    replace_dmrs = parse_graphlang('[1]:_talk_v_about e? <=1= _about_p e -2-> [2]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I talk about linguistics.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I give a talk on linguistics.' in generate(dmrs)


    # synonyms

    dmrs = parse('Kim loves cake.')[0]
    search_dmrs = parse_graphlang('[1]:_love_v_1 e?')
    replace_dmrs = parse_graphlang('[1]:_adore_v_1 e?')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Kim adores cake.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Kim loves cake.' in generate(dmrs)

    dmrs = parse('I like to play tennis.')[0]
    search_dmrs = parse_graphlang('[1]:_like_v_1 e? -2h-> [2]:_v e[pui--]')
    replace_dmrs = parse_graphlang('[1]:_enjoy_v_1 e? -2h-> [2]:_v e[pui-+]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I enjoy playing tennis.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I like to play tennis.' in generate(dmrs)


    # synonyms with re-ordering

    dmrs = parse('Kim gave a book to Sandy.')[0]
    search_dmrs = parse_graphlang('[2]:node <-1- [1]:_give_v_1 e? -3-> [3]:node')
    replace_dmrs = parse_graphlang('[3]:node <-1- [1]:_get_v_1 e? <=1= _from_p e -2-> [2]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Sandy got a book from Kim.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Kim gave a book to Sandy.' in generate(dmrs)

    dmrs = parse('Kim hates spinach.')[0]
    search_dmrs = parse_graphlang('[2]:node <-1- [1]:_hate_v_1 e? -2-> [3]:node')
    replace_dmrs = parse_graphlang('[3]:node <-1- [1]:_disgust_v_1 e? -2-> [2]:node')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Spinach disgusts Kim.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'Kim hates spinach.' in generate(dmrs)

    dmrs = parse('I like to play tennis.')[0]
    search_dmrs = parse_graphlang('[1]:node <-1- [2]:_like_v_1 e? -2h-> [3]:_v e[pui--] -1-> :1')
    replace_dmrs = parse_graphlang('udef_q --> nominalization x <-1- [2]:_make_v_cause e? -2h-> _happy_a_with e[pui__] -1-> [1]:node; :nominalization =1h=> [3]:_v e[pui-+]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Playing tennis makes me happy.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I like to play tennis.' in generate(dmrs)


    # think + subclause examples

    dmrs = parse('I think I will go.')[0]
    search_dmrs = parse_graphlang('[1]:_think_v_1 e[????-] -2h-> [2]:_v e[pfi--]')
    replace_dmrs = parse_graphlang('[1]:_think_v_of e[????+] -2-> nominalization x <-- udef_q; :nominalization =1h=> [2]:_v e[pui-+]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I am thinking of me going.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I think I will go.' in generate(dmrs)

    dmrs = parse('I think he will go.')[0]
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'I am thinking of him going.' in generate(dmrs)
    dmrs_mapping(dmrs, replace_dmrs, search_dmrs, copy_dmrs=False)
    assert 'I think he will go.' in generate(dmrs)


    # question generation (with subgraph nodes)

    dmrs = parse('Kim gave Sandy a book.')[0]
    search_dmrs = parse_graphlang('*[1]:_v e[p????] -1-> {2}:node')
    replace_dmrs = parse_graphlang('*[1]:_v e[q????] -1-> {2}:person x[3s___] <-- which_q')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Who gave Sandy a book?' in generate(dmrs)

    dmrs = parse('Kim gave Sandy a book.')[0]
    search_dmrs = parse_graphlang('*[1]:_v e[p????] -2-> {2}:node')
    replace_dmrs = parse_graphlang('*[1]:_v e[q????] -2-> {2}:thing x <-- which_q')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'What did Kim give Sandy?' in generate(dmrs)

    dmrs = parse('Kim gave Sandy a book.')[0]
    search_dmrs = parse_graphlang('*[1]:_v e[p????] -3-> {2}:node')
    replace_dmrs = parse_graphlang('*[1]:_v e[q????] -3-> {2}:person x[3s___] <-- which_q')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, copy_dmrs=False)
    assert 'Who did Kim give a book?' in generate(dmrs)


    # think example (with equal constraints)

    dmrs = parse('I think I will go.')[0]
    equalities = {}
    search_dmrs = parse_graphlang('[1]:node=1 <-1- [2]:_think_v_1 e[????-] -2h-> [3]:_v e[pfi--] -1-> node=1 <-- pred', equalities=equalities)
    replace_dmrs = parse_graphlang('[1]:node <-1- [2]:_think_v_of e[????+] -2-> nominalization x <-- udef_q; :nominalization =1h=> [3]:_v e[pui-+]')
    dmrs_mapping(dmrs, search_dmrs, replace_dmrs, equalities=equalities, copy_dmrs=False)
    assert 'I am thinking of going.' in generate(dmrs)
