from swarm.confidence_loop import summarize_confidence, recommend_confidence_actions, build_confidence_summary


def test_summarize_confidence_values():
    summary = summarize_confidence([0.9, 0.5, 0.7])
    assert summary['count'] == 3
    assert summary['lowest'] == 0.5


def test_build_confidence_summary_has_actions():
    result = build_confidence_summary([0.2, 0.4])
    assert result['next_step'] == 'governed confidence review'
    assert len(result['recommended_actions']) >= 1
