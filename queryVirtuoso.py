from SPARQLWrapper import SPARQLWrapper, JSON
import numpy as np
from tqdm import tqdm
import json
# In virtuoso.txt in database/
# MaxQueryCostEstimationTime 	= 400	; in seconds


def load_queries(query_location):
    return np.load(query_location)


def wrapper(url, default_graph):
    sparql = SPARQLWrapper(
        url
    )
    sparql.setReturnFormat(JSON)
    sparql.addDefaultGraph(default_graph)
    return sparql


def execute_query(query, wrapped_sparql_endpoint):
    wrapped_sparql_endpoint.setTimeout(60)
    wrapped_sparql_endpoint.setQuery(query)
    return wrapped_sparql_endpoint.queryAndConvert()


def count_results(result):
    count = 0
    bindings_found = []
    for r in result["results"]["bindings"]:
        count += 1
    return count


def execute_queries(queries, endpoint):
    """Expects nested array of queries [[q1,q2],[q3,q4]]"""
    results = []
    for query_subset in tqdm(queries):
        subset_results = []
        for query in query_subset:
            ret = execute_query(query, endpoint)
            subset_results.append(ret)
        results.append(subset_results)
    return results

def execute_array_of_queries(queries, endpoint, ckp=None):
    query_strings = []
    query_cardinalities = []

    for i, query in enumerate(tqdm(queries)):
        ret = execute_query(query[0], endpoint)
        query_cardinalities.append(count_results(ret))
        query_strings.append(query[0])
        if ckp and i % 5 == 0 and i > 0:
            with open(ckp + "/query_strings.json", "w") as f:
                json.dump(query_strings, f)
            with open(ckp + "/query_cardinalities.json", "w") as f:
                json.dump(query_cardinalities, f)

    return query_strings, query_cardinalities


def main(endpoint, graph_uri, queries_location, dataset_save_location, ckp_location=None):
    queries = load_queries(queries_location)
    wrapped_endpoint = wrapper(endpoint, graph_uri)
    full_query_string, full_cardinalities = execute_array_of_queries(queries, wrapped_endpoint, ckp_location)

    with open(dataset_save_location + "/query_strings.json", "w") as f:
        json.dump(full_query_string, f)
    with open(dataset_save_location + "/query_cardinalities.json", "w") as f:
        json.dump(full_cardinalities, f)


if __name__ == "__main__":
    pass
    # main("http://localhost:8890/sparql",
    #      "http://localhost:8890/watdiv",
    #      "output/queries/queries_star_path.npy",
    #      "output/pretrain_dataset",
    #      "output/pretrain_dataset/chkp"
    #      )
    #
    # main("http://localhost:8890/sparql",
    #      "http://localhost:8890/watdiv",
    #      "output/queries/queries_star_path.npy",
    #      "output/pretrain_dataset",
    #      "output/pretrain_dataset/chkp"
    #      )
