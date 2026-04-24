from swarm.event_bridge import event_to_routing_task


def test_event_to_routing_task_for_billing_event():
    event = {
        'event_id': 'evt_1',
        'event_type': 'billing.event',
        'payload': {
            'objective': 'Activate workflow',
            'task_id': 'task_1',
        },
        'source': {'repo': 'lippytm/Web3AI'},
        'target': {'repo': 'lippytm/MyClaw.lippytm.AI-'},
    }
    task = event_to_routing_task(event)
    assert task['required_capability'] == 'commerce'
    assert task['objective'] == 'Activate workflow'


def test_event_to_routing_task_defaults():
    task = event_to_routing_task({'event_id': 'evt_2'})
    assert task['required_capability'] == 'general'
    assert 'Handle event' in task['objective']
