from swarm.replay_loop import summarize_replay, recommend_replay_actions, build_replay_summary


def test_summarize_replay_records():
    summary = summarize_replay([
        {'replayable': True},
        {'replayable': False},
        {'replayable': True},
    ])
    assert summary['total_records'] == 3
    assert summary['replayable_records'] == 2


def test_build_replay_summary_has_actions():
    result = build_replay_summary([{'replayable': False}])
    assert result['next_step'] == 'governed replay review'
    assert len(result['recommended_actions']) >= 1
