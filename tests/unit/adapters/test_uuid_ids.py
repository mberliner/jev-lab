import uuid

from jevlab.adapters.uuid_ids import UuidIdGenerator


def test_request_ids_are_distinct_uuids() -> None:
    generator = UuidIdGenerator()
    ids = {generator.new_request_id() for _ in range(50)}

    assert len(ids) == 50
    for value in ids:
        assert str(uuid.UUID(value)) == value
