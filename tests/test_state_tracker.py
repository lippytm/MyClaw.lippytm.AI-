from swarm.state_tracker import StateTracker


def test_state_tracker_update_and_get():
    tracker = StateTracker()
    snapshot = tracker.update('system_1', 'swarm', 'routing', confidence=0.8, mission_id='mission_1')
    assert snapshot['lane'] == 'swarm'
    assert tracker.get('system_1')['current_mission_id'] == 'mission_1'


def test_state_tracker_summary():
    tracker = StateTracker()
    tracker.update('system_1', 'swarm', 'routing')
    tracker.update('system_2', 'product', 'idle')
    summary = tracker.summary()
    assert summary['total_systems'] == 2
    assert summary['by_lane']['swarm'] == 1
    assert summary['by_lane']['product'] == 1
