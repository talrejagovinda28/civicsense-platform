from app.services.adapters.fake import FakeAdapter


def test_fake_adapter_scenarios():
    adapter = FakeAdapter()
    intent = {"payload_hash": "hash", "destination": "test@example.test"}

    for scenario, expected in {
        "accept_registered": "officially_registered",
        "transport_only": "provider_accepted",
        "reject": "rejected",
        "timeout_unknown": "unknown_outcome",
    }.items():
        intent_with_scenario = {**intent, "scenario": scenario}
        outcome = adapter.submit(intent_with_scenario, idempotency_key=f"key-{scenario}")
        assert outcome.state.value == expected


def test_fake_adapter_deterministic_without_scenario():
    adapter = FakeAdapter()
    intent = {"payload_hash": "deterministic-hash", "destination": "test@example.test"}
    first = adapter.submit(intent, idempotency_key="same-key")
    second = adapter.submit(intent, idempotency_key="other-key")
    assert first.state == second.state
