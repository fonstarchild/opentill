"""Tests for shared domain BaseEntity and AggregateRoot."""
import pytest
from backend.shared.domain.entity import BaseEntity
from backend.shared.domain.aggregate import AggregateRoot
from backend.shared.domain.domain_event import DomainEvent
from dataclasses import dataclass


@dataclass(frozen=True)
class SampleEvent(DomainEvent):
    data: str = ""


class SampleAggregate(AggregateRoot):
    def do_something(self):
        self._record_event(SampleEvent(aggregate_id=self.id, data="test"))


class TestBaseEntity:
    def test_equality_by_id(self):
        e1 = BaseEntity(1)
        e2 = BaseEntity(1)
        assert e1 == e2

    def test_inequality_different_id(self):
        assert BaseEntity(1) != BaseEntity(2)

    def test_inequality_different_class(self):
        class OtherEntity(BaseEntity):
            pass
        assert BaseEntity(1) != OtherEntity(1)

    def test_hash_by_id(self):
        e1 = BaseEntity(1)
        e2 = BaseEntity(1)
        assert hash(e1) == hash(e2)

    def test_id_property(self):
        e = BaseEntity(42)
        assert e.id == 42


class TestAggregateRoot:
    def test_starts_with_no_events(self):
        agg = SampleAggregate(1)
        assert agg.collect_events() == []

    def test_records_event(self):
        agg = SampleAggregate(1)
        agg.do_something()
        events = agg.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], SampleEvent)

    def test_clear_events(self):
        agg = SampleAggregate(1)
        agg.do_something()
        agg.clear_events()
        assert agg.collect_events() == []

    def test_collect_returns_copy(self):
        agg = SampleAggregate(1)
        agg.do_something()
        events = agg.collect_events()
        events.clear()
        assert len(agg.collect_events()) == 1

    def test_event_has_occurred_at(self):
        agg = SampleAggregate(1)
        agg.do_something()
        event = agg.collect_events()[0]
        assert event.occurred_at is not None

    def test_event_has_unique_id(self):
        agg = SampleAggregate(1)
        agg.do_something()
        agg.do_something()
        events = agg.collect_events()
        ids = {e.event_id for e in events}
        assert len(ids) == 2
