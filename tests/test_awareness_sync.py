from swarm.awareness_sync import summarize_awareness, recommend_sync_actions, build_awareness_sync_summary


def test_summarize_awareness_groups_by_lane():
    summary = summarize_awareness([
        {'repo': 'a', 'primary_lane': 'hub'},
        {'repo': 'b', 'primary_lane': 'hub'},
        {'repo': 'c', 'primary_lane': 'lab'},
    ])
    assert summary['total_items'] == 3
    assert summary['by_lane']['hub'] == 2


def test_build_awareness_sync_summary_has_next_step():
    result = build_awareness_sync_summary([
        {'repo': 'a', 'primary_lane': 'hub'},
        {'repo': '', 'primary_lane': 'lab'},
    ])
    assert result['next_step'] == 'governed awareness review'
    assert len(result['recommended_actions']) >= 1
