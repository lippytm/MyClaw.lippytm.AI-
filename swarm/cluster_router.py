from __future__ import annotations

from typing import Dict, List


CLUSTER_MAP = {
    'repo_manufacturing': 'repo_manufacturing_cluster',
    'revenue_optimization': 'revenue_cluster',
    'commerce_activation': 'commerce_cluster',
    'assistant_support': 'assistant_cluster',
    'knowledge_packaging': 'knowledge_cluster',
}


def recommend_cluster(mission_type: str) -> str:
    return CLUSTER_MAP.get(mission_type, 'general_cluster')


def build_cluster_route(mission_type: str, required_capability: str) -> Dict[str, object]:
    cluster = recommend_cluster(mission_type)
    return {
        'cluster': cluster,
        'mission_type': mission_type,
        'required_capability': required_capability,
        'fallback_clusters': ['general_cluster', 'supervisor_cluster'],
    }


def list_known_clusters() -> List[str]:
    return sorted(set(CLUSTER_MAP.values()) | {'general_cluster', 'supervisor_cluster'})
