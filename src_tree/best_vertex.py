import numpy as np
import pickle as pk
from operator import is_not
from functools import partial

from wiki_pubmed_fuzzy.ontology import get_ontology


#need to be sure that the doid has a parent
def check_parent(doid,ontology):
    flag = 0
    term = ontology.get_term(doid)
    if len(term.relationships) > 0:
        flag = 1
    return flag

def find_number_ancestors(doid, index,ontology):
    if check_parent(doid,ontology) > 0:
        term = ontology.get_term(doid)
        dict = {term.name: term.id for term in ontology.get_terms()}
        father = dict[term.relationships[0][2]]
        index = find_number_ancestors(father, index+1,ontology)   
    return index

def numerate(doid,ontology):
    #take integer number of a doid
    n = ontology.terms.keys().index(doid)
    res[n] += 1
    term = ontology.get_term(doid)
    if len(term.name) > 0 and check_parent(doid,ontology) > 0:
        dict = {term.name: term.id for term in ontology.get_terms()}
        print(term.relationships)
        father = dict[term.relationships[0][2].lower()]
        numerate(father,ontology)
    
def numerate_tree(list_of_doids,ontology):
    for v in list_of_doids:
        numerate(v,ontology)
        
def find_best_vertex(list_of_doids,ontology):
    if len(list_of_doids) > 0:
        N = len(ontology.terms.keys())
        global res
        res = np.zeros(N)
        numerate_tree(list_of_doids,ontology)
        index = np.where(res>0.5*len(list_of_doids))
        doids = [None] * len(index[0])
        ancestors = [None] * len(index[0])
        for i in range(len(index[0])):
            doids[i] = ontology.terms.keys()[index[0][i]]
            ancestors[i] = find_number_ancestors(doids[i],0,ontology)
        best_ancestor_index = ancestors.index(max(ancestors))
        best_vertex = doids[best_ancestor_index]
        return best_vertex
    else:
        return None