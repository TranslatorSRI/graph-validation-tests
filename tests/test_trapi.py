"""
Unit tests of the low level TRAPI (ARS, KP & ARA) calling subsystem.
"""

from one_hop_tests.trapi import post_query
from one_hop_tests.ontology_kp import ONTOLOGY_KP_TRAPI_SERVER, NODE_NORMALIZER_SERVER

import pytest

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.parametrize(
    "curie,category,result",
    [
        (
            "CHEMBL.COMPOUND:CHEMBL2333026",
            "biolink:SmallMolecule",
            ""
        )
    ]
)
@pytest.mark.asyncio
async def test_post_query_to_ontology_kp(curie: str, category: str, result):
    query = {
        "message": {
            "query_graph": {
                "nodes": {
                    "a": {
                        "ids": [curie]
                    },
                    "b": {
                        "categories": [category]
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
    response = post_query(url=ONTOLOGY_KP_TRAPI_SERVER, query=query, server="Post Ontology KP Query")
    assert response


@pytest.mark.asyncio
async def test_post_query_to_node_normalization():
    j = {'curies': ['HGNC:12791']}
    result = post_query(url=NODE_NORMALIZER_SERVER, query=j, server="Post Node Normalizer Query")
    assert result
    assert "HGNC:12791" in result
    assert "equivalent_identifiers" in result["HGNC:12791"]
    assert len(result["HGNC:12791"]["equivalent_identifiers"])
