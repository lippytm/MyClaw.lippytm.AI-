from swarm.improvement_loop import summarize_signals, recommend_actions, build_improvement_summary


def test_summarize_signals_counts_types():
    summary = summarize_signals([
        {'type': 'routing_failure'},
        {'type': 'routing_failure'},
        {'type': 'dead_letter_growth'},
    ])
    assert summary['total_signals'] == 3
    assert summary['by_type']['routing_failure'] == 2


def test_recommend_actions_returns_guidance():
    actions = recommend_actions([
        {'type': 'routing_failure'},
        {'type': 'confidence_drop'},
    ])
    assert 'review swarm routing rules' in actions
    assert 'raise supervisor review threshold' in actions


def test_build_improvement_summary_has_next_step():
    result = build_improvement_summary([{'type': 'dead_letter_growth'}])
    assert result['next_step'] == 'governed review'
