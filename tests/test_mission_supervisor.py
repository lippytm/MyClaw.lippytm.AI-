from swarm.mission_supervisor import MissionSupervisor


def test_mission_supervisor_start_and_summary():
    supervisor = MissionSupervisor()
    supervisor.start('mission_1')
    summary = supervisor.summarize('mission_1')
    assert summary['mission_id'] == 'mission_1'


def test_mission_supervisor_complete_and_fail():
    supervisor = MissionSupervisor()
    supervisor.start('mission_2')
    supervisor.complete_task('mission_2', 'task_a')
    supervisor.fail_task('mission_2', 'task_b', 'needs review')
    summary = supervisor.summarize('mission_2')
    assert summary['completed_count'] == 1
    assert summary['failed_count'] == 1
    assert 'needs review' in summary['notes']
