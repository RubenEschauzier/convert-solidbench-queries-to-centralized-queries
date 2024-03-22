import re
import json
import os
from queryVirtuoso import wrapper, execute_query, count_results, execute_queries

from os.path import isfile, join


def load_queries(queryDir):
    loaded_queries = []
    query_names = []
    for file in os.listdir(queryDir):
        with open(queryDir + '/' + file) as f:
            query_subset = [x.strip() for x in f.read().split('\n\n')]
            loaded_queries.append(query_subset)
            query_names.append(file)
            pass
    return loaded_queries, query_names


def replace_prefixes(queries, conversion_dict):
    converted_queries = []
    for query in queries:
        for (key, value) in conversion_dict.items():
            conversion_regex = re.compile(r'(PREFIX\s+{}\s*:\s*)<[^>]+>'.format(key))
            query = conversion_regex.sub(r'\g<1>{}'.format(value), query)
        converted_queries.append(query)
    return converted_queries


def replace_all_pod_occurrences(queries):
    new_queries = []
    pattern = re.compile(r'<http://localhost:3000/pods/(\d+)/profile/card#me>')
    for i in range(len(queries)):
        new_queries.append(pattern.sub(r'sn:pers\g<1>', queries[i]))
    return new_queries


def replace_all_sn_occurences(result):
    pattern = re.compile(r'http://www.ldbc.eu/ldbc_socialnet/1.0/data/pers(\d+)')
    test = pattern.sub(r'<http://localhost:3000/pods/\g<1>/profile/card#me>', "hello")
    pass


def add_prefix_to_start_queries(queries):
    prefixes_to_add = [
        "PREFIX sn: <http://www.ldbc.eu/ldbc_socialnet/1.0/data/> \n"
    ]
    for prefix in prefixes_to_add:
        new_queries = [[prefix + query for query in query_subset] for query_subset in queries]
    return new_queries


def convert_all_queries(queries, conversion_dict):
    """Expects nested array of queries"""
    queries_replaced_prefixes = [replace_prefixes(query_subset, conversion_dict) for query_subset in queries]
    queries_replaced_pod_references = [replace_all_pod_occurrences(query_subset)
                                       for query_subset in queries_replaced_prefixes]
    queries_added_prefixes = add_prefix_to_start_queries(queries_replaced_pod_references)
    return queries_added_prefixes


def convert_query_output_to_bindings(queryResult):
    simplified_dict = {}
    for (var, binding) in queryResult.items():
        simplified_dict[var] = binding['value']
    return simplified_dict


def process_all_results(results):
    query_subset_results = []
    for result_subset in results:
        processed_subset = []
        for result in result_subset:
            processed_subset.append(convert_query_output_to_bindings(result))
        query_subset_results.append(processed_subset)
    return query_subset_results


def get_substitutions_in_query(query, variables):
    sub_dict = {}
    for variable in variables:
        print(variable)
        matched = re.search(r'\((\?[A-z0-9]+) AS \?{}'.format(variable), query)
        if matched:
            print(matched.group(1))
            sub_dict[variable] = matched.group(1)
    return sub_dict
    # pattern_sub = re.compile(r'\((.*?)\)')
    # pattern_alias = re.compile(r'\?(.+) AS \?(.+)')
    # print(re.findall(pattern_alias, query))
    # matches = re.findall(pattern_sub, query)
    # for match in matches:
    #     a = re.search(pattern_alias, match)
    #     print(a.group() if a is not None else 'Not found')
    #
    # print(matches)


def main():
    prefix_conversion_dict = {
        "xsd": "<http://www.w3.org/2001/XMLSchema#>",
        "snvoc": "<http://www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>",
        "sntag": "<http://www.ldbc.eu/ldbc_socialnet/1.0/tag/>",
        "sn": "<http://www.ldbc.eu/ldbc_socialnet/1.0/data/>",
        "rdf": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        "rdfs": "<http://www.w3.org/2000/01/rdf-schema#>",
        "foaf": "<http://xmlns.com/foaf/0.1/>",
        "dbpedia": "<http://dbpedia.org/resource/>",
        "dbpedia-owl": "<http://dbpedia.org/ontology/>",
    }
    prefix_conversion_dict_back_to_solidbench = {
        "PREFIX snvoc: <http://localhost:3000/www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>"
        "PREFIX dbpedia-owl: <http://localhost:3000/dbpedia.org/ontology/>"
    }
    graph_uri = "http://localhost:8890/solidbench"
    endpoint_uri = "http://localhost:8890/sparql"
    wrapped_endpoint = wrapper(endpoint_uri, graph_uri)

    queries, query_names = load_queries("queries")
    queries_replaced_pod_references = convert_all_queries(queries, prefix_conversion_dict)

    # query_results = execute_queries(queries_replaced_pod_references, wrapped_endpoint)
    results = execute_queries([[queries_replaced_pod_references[0][0]]], wrapped_endpoint)
    all_var = []
    for r in results[0][0]["head"]["vars"]:
        all_var.append(r)

    sub_dict = get_substitutions_in_query(queries_replaced_pod_references[0][0], all_var)
    bindings = []
    test_query = queries[0][0]
    for r in results[0][0]["results"]["bindings"]:
        print(r)
        bindings.append(convert_query_output_to_bindings((r)))
    for binding in bindings:
        for (var, value) in binding.items():
            if var in sub_dict:
                var_to_replace = sub_dict[var]
                print(var_to_replace)
                test_query = test_query.replace(var_to_replace, value)
                # print(var_to_replace)
                # print(var, value)
    print(test_query)
    # print(queries[0][0])
    # print(bindings)

    # results = execute_queries(queries_replaced_pod_references[0:1], wrapped_endpoint)
    # all_bindings_objects = []
    # for result_subset in results:
    #     subset_results = []
    #     for result in result_subset:
    #         bindings = []
    #         for r in result["results"]["bindings"]:
    #             bindings.append(convert_query_output_to_bindings(r))
    #         subset_results.append(bindings)
    #     all_bindings_objects.append(subset_results)
    # json.dump(all_bindings_objects, open("test.json", "w"))
    # print(count_results(test))

    # print(queries_replaced_pod_references[0][0])


if __name__ == "__main__":
    main()
    # query_test = '''
    # PREFIX snvoc : <https://solidbench.linkeddatafragments.org/www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>
    # SELECT DISTINCT ?creator ?messageContent WHERE {
    #   <https://solidbench.linkeddatafragments.org/pods/00000006597069767117/profile/card#me> snvoc:likes _:g_0.
    #   _:g_0 (snvoc:hasPost|snvoc:hasComment) ?message.
    #   ?message snvoc:hasCreator ?creator.
    #   ?otherMessage snvoc:hasCreator ?creator;
    #     snvoc:content ?messageContent.
    # }
    # LIMIT 10
    # '''

    # replace_prefixes(prefix_conversion_dict, query_test)
#     p = re.compile(r'<https://solidbench.linkeddatafragments.org/pods/(\d+)/profile/card#me>')
#     print(re.findall(p, query))
#     res = p.sub(r'sn:pers\g<1>', '''
#     PREFIX snvoc: <https://solidbench.linkeddatafragments.org/www.ldbc.eu/ldbc_socialnet/1.0/vocabulary/>
#             SELECT DISTINCT ?creator ?messageContent WHERE {
#   <https://solidbench.linkeddatafragments.org/pods/00000006597069767117/profile/card#me> snvoc:likes _:g_0.
#   _:g_0 (snvoc:hasPost|snvoc:hasComment) ?message.
#   ?message snvoc:hasCreator ?creator.
#   ?otherMessage snvoc:hasCreator ?creator;
#     snvoc:content ?messageContent.
# }
# LIMIT 10''')
#     print(res)
#     pass
