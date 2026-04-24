from swarm.telemetry_loop import summarize_telemetry, recommend_telemetry_actions, build_telemetry_summary


def test_summarize_telemetry_counts_types():
    summary = summarize_telemetry([
        {'type': 'missing_event'},
        {'type': 'missing_event'},
        {'type': 'stale_state'},
    ])
    assert summary['total_events'] == 3
    assert summary['by_type']['missing_event'] == 2


def test_build_telemetry_summary_has_next_step():
    result = build_telemetry_summary([{'type': 'stale_state'}])
    assert result['next_step'] == 'governed telemetry review'
    assert len(result['recommended_actions']) >= 1
