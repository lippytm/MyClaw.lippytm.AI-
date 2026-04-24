from swarm.cluster_router import recommend_cluster, build_cluster_route, list_known_clusters


def test_recommend_cluster():
    assert recommend_cluster('repo_manufacturing') == 'repo_manufacturing_cluster'
    assert recommend_cluster('unknown_type') == 'general_cluster'


def test_build_cluster_route():
    route = build_cluster_route('revenue_optimization', 'offers')
    assert route['cluster'] == 'revenue_cluster'
    assert route['required_capability'] == 'offers'


def test_list_known_clusters():
    clusters = list_known_clusters()
    assert 'general_cluster' in clusters
    assert 'supervisor_cluster' in clusters
