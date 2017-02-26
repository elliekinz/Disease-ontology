import multiprocessing
import requests
import json
from wiki_pubmed_fuzzy.ontology import get_ontology


# TREE = get_ontology("../data/doid.obo")


def request_synonyms(oid, iri):
    j = requests.get('http://www.ebi.ac.uk/ols/api/ontologies/' + oid + '/terms?iri=' + iri).json()
    return j["_embedded"]["terms"][0]["synonyms"] if "_embedded" in j else []


def search_others(query, doids):
    j = requests.get('http://www.ebi.ac.uk/ols/api/search?q=' + query + '&ontology=efo, hp, ogms, ordo').json()

    results = []
    syns = set()
    for item in j['response']['docs']:
        if 'iri' in item:
            ss = request_synonyms(item['ontology_name'], item['iri'])
            if ss:
                for s in ss:
                    syns.add(s.lower().strip())

    for syn in syns:
        r = search_doid(syn, True, doids)
        if len(r) > 0:
            results.append(r)

    return results


def search_doid(query, exact, doids):
    j = requests.get('http://www.ebi.ac.uk/ols/api/search?q=' + query + '&ontology=doid&exact=' + str(exact).lower()).json()

    matches = []
    for item in j['response']['docs']:
        if 'obo_id' in item and item['obo_id'] not in doids:
            matches.append({
                             'id':item['obo_id'],
                             'desc':next(iter(item['description'])) if 'description' in item else '',
                             'label':item['label'],
                            })
            doids.add(item['obo_id'])

    return matches


def search(query):
    doids = set()
    doid_exact_results = search_doid(query, True, doids)
    if (len(doid_exact_results) > 0):
        return {'query': query, 'exact_matches': doid_exact_results}
    else:
        return {}
        # doid_results = search_doid(query, False, doids)
        # other_results = search_others(query, doids)
        # return {'query': query, 'top_matches': doid_results, 'synonym_matches': other_results}


def parse(text):
    lines = list(l.strip() for l in text.split('\n') if len(l.strip()) > 0)

    if len(lines) == 4 and all(l.startswith('#') for l in lines):
        # test data format
        def getTerms(line):
            return list(map(lambda s: s.strip(), line.split(':')[1].split(',')))
        reason = getTerms(lines[0])
        additional = getTerms(lines[3])
    else:
        reason = [text]
        additional = []
    return {'reason': reason, 'additional': additional}


def format_response(r):
    s = r['query'] + "\n"

    if 'exact_matches' in r:
        s += ("Exact match\n"
               "Name: {0}\n"
               "# {1}").format(r['exact_matches'][0]['label'], r['exact_matches'][0]['id'])
    else:
        s += "Best fuzzy match\n"

    return s


def lookup(text):
    pool = multiprocessing.Pool(15)

    parsed = parse(text)
    strings = parsed['reason'] + parsed['additional']

    results = pool.map(search, strings)

    for i in range(len(results)):
        yield format_response(results[i])