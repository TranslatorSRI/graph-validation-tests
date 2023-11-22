"""
Ontology KP interface
"""
from typing import Optional
from reasoner_validator.biolink import get_biolink_model_toolkit
from one_hop_tests.trapi import post_query

ONTOLOGY_KP_TRAPI_SERVER = "https://ontology-kp.apps.renci.org/query"
NODE_NORMALIZER_SERVER = "https://nodenormalization-sri.renci.org/get_normalized_nodes"


def convert_to_preferred(curie, allowed_list):
    """
    :param curie
    :param allowed_list
    """
    j = {'curies': [curie]}
    result = post_query(NODE_NORMALIZER_SERVER, j)
    if not result:
        return None
    new_ids = [v['identifier'] for v in result[curie]['equivalent_identifiers']]
    for nid in new_ids:
        if nid.split(':')[0] in allowed_list:
            return nid
    return None


def get_ontology_ancestors(curie, btype):
    """
    :param curie:
    :param btype:
    """
    m = {
        "message": {
            "query_graph": {
                "nodes": {
                    "a": {
                        "ids": [curie]
                    },
                    "b": {
                        "categories": [btype]
                    }
                },
                "edges": {
                    "ab": {
                        "subject": "a",
                        "object": "b",
                        "predicates": ["biolink:subclass_of"]
                    }
                }
            }
        }
    }
    response = post_query(ONTOLOGY_KP_TRAPI_SERVER, m, server="Ontology KP")
    original_prefix = curie.split(':')[0]
    ancestors = []
    if response:
        for result in response['message']['results']:
            parent_id = result['node_bindings']['b'][0]['id']
            if parent_id == curie:
                # everything is a subclass of itself
                continue
            if not parent_id.startswith(original_prefix):
                # Don't give me UPHENO:000001 if I asked for a parent of HP:000012312
                continue
            # good enough
            ancestors.append(parent_id)
    else:
        print("### No response from the Ontology server: it may be offline?")

    return ancestors


def get_ontology_parent(curie, btype):
    """
    :param btype
    :param curie
    """
    # Here's a bunch of ancestors
    ancestors = get_ontology_ancestors(curie, btype)

    if not ancestors:
        return None

    # Now, to get the one closest to the input, we see
    # how many ancestors each ancestor has.  Largest number == lowest down
    ancestor_count = []
    for anc in ancestors:
        second_ancestors = get_ontology_ancestors(anc, btype)
        if not second_ancestors:
            continue
        ancestor_count.append((len(second_ancestors), anc))
    if ancestor_count:
        ancestor_count.sort()
        return ancestor_count[-1][1]
    else:
        return None


def get_parent_concept(curie, category, biolink_version) -> Optional[str]:
    """
    :param curie: CURIE of a concept instance
    :param category: Biolink Category of the concept instance
    :param biolink_version: Biolink Model version to use in validation (SemVer string specification)
    """
    tk = get_biolink_model_toolkit(biolink_version=biolink_version)
    if not tk.is_category(category):
        assert False, f"{category} is not a Biolink Model Category!"

    # Not every Biolink Category has a prefix namespace with ontological hierarchy.
    # We replace the previous hard coded namespace list with retrieval of id_prefixes
    # registered for the given concept category within the Biolink Model.
    # preferred_prefixes = {'CHEBI', 'HP', 'MONDO', 'UBERON', 'CL', 'EFO', 'NCIT'}
    preferred_prefixes = tk.get_element(category).id_prefixes

    input_prefix = curie.split(':')[0]
    if input_prefix in preferred_prefixes:
        query_entity = curie
    else:
        query_entity = convert_to_preferred(curie, preferred_prefixes)
    if query_entity is None:
        return None
    preferred_parent = get_ontology_parent(query_entity, category)
    if preferred_parent is None:
        return None
    original_parent_prefix = preferred_parent.split(':')[0]
    if original_parent_prefix == input_prefix:
        return preferred_parent
    return convert_to_preferred(preferred_parent, [input_prefix])
