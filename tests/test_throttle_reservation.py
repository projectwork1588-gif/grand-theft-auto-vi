"""The throttle's reservation primitive (Phase 3A): reserve() checks every limit and records capacity in ONE locked step, all-or-nothing, and hands back a ticket;
settle() and release() act on that ticket's own events only. No web server and no database here. Concurrency is made deterministic with barriers (all threads
start together) and with invariants that must hold however the scheduler orders them; nothing asserts how long anything took."""
import random
import threading

import pytest

from app.security import Throttle, Ticket

WINDOW = 600


def make(max_keys=100):
    clock = {"now": 1000.0}
    throttle = Throttle(clock=lambda: clock["now"])
    throttle.MAX_KEYS = max_keys
    return throttle, clock


def together(count, work):
    """Run work(i) in `count` threads that all start at the same moment. Returns the results in thread order."""
    barrier, results, errors = threading.Barrier(count), [None] * count, []

    def run(i):
        try:
            barrier.wait(30)
            results[i] = work(i)
        except BaseException as error:                    # a failure inside a thread must fail the test, not vanish
            errors.append(error)
    threads = [threading.Thread(target=run, args=(i,), daemon=True) for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(60)
        assert not thread.is_alive(), "a thread did not finish"
    assert not errors, errors
    return results


def events(throttle, key):
    with throttle._lock:
        return [list(e) for e in throttle._failures.get(key, ())]


def pending(throttle, key):
    return [e for e in events(throttle, key) if not e[2]]


# ------------------------------------------------------------------ simultaneous reservations
@pytest.mark.parametrize("round_number", range(10))
def test_fifty_simultaneous_reservations_get_exactly_the_limit(round_number):
    throttle, _ = make()
    results = together(50, lambda i: throttle.reserve([("k", 5, WINDOW)]))
    granted = [ticket for wait, ticket in results if ticket is not None]
    refused = [wait for wait, ticket in results if ticket is None]
    assert len(granted) == 5 and len(refused) == 45 and all(wait > 0 for wait in refused)
    assert len({ticket.id for ticket in granted}) == 5                     # every ticket is unique
    assert len(events(throttle, "k")) == 5 and len(pending(throttle, "k")) == 5


def test_a_refused_reservation_records_nothing_on_any_key():
    throttle, _ = make()
    throttle.record_failure("full", WINDOW)
    throttle.record_failure("full", WINDOW)
    wait, ticket = throttle.reserve([("free-1", 5, WINDOW), ("full", 2, WINDOW), ("free-2", 5, WINDOW)])
    assert ticket is None and wait > 0
    assert events(throttle, "free-1") == [] and events(throttle, "free-2") == [] and len(events(throttle, "full")) == 2
    assert "free-1" not in throttle._failures and "free-2" not in throttle._windows


def test_all_or_nothing_holds_under_contention_when_only_one_of_two_keys_limits():
    throttle, _ = make()
    results = together(30, lambda i: throttle.reserve([("tight", 3, WINDOW), ("loose", 100, WINDOW)]))
    assert sum(ticket is not None for _wait, ticket in results) == 3
    assert len(events(throttle, "tight")) == 3 and len(events(throttle, "loose")) == 3      # the 27 refusals left nothing on the loose key


def test_all_or_nothing_holds_when_two_keys_both_limit():
    throttle, _ = make()
    results = together(40, lambda i: throttle.reserve([("a", 4, WINDOW), ("b", 3, WINDOW)]))
    assert sum(ticket is not None for _wait, ticket in results) == 3                         # the tighter key decides
    assert len(events(throttle, "a")) == 3 and len(events(throttle, "b")) == 3               # refusals that passed 'a' but failed 'b' left nothing on 'a'


def test_the_wait_is_the_longest_refusing_wait_and_shrinks_as_time_passes():
    throttle, clock = make()
    throttle.reserve([("old", 1, WINDOW)])
    clock["now"] += 400
    throttle.reserve([("new", 1, WINDOW)])
    wait, ticket = throttle.reserve([("old", 1, WINDOW), ("new", 1, WINDOW)])
    assert ticket is None and 590 <= wait <= 610                                             # 'old' has 200 s left, 'new' a full 600: the longest wins
    clock["now"] += 250                                                                      # 'old' has now expired, 'new' still has 350 s to go
    wait, ticket = throttle.reserve([("old", 1, WINDOW), ("new", 1, WINDOW)])
    assert ticket is None and 345 <= wait <= 355 and events(throttle, "old") == []
    clock["now"] += 400
    assert throttle.reserve([("old", 1, WINDOW), ("new", 1, WINDOW)])[1] is not None          # a cooldown, never a lock


# ------------------------------------------------------------------ tickets own their events
def test_release_removes_only_that_tickets_events():
    throttle, _ = make()
    throttle.record_failure("k", WINDOW)                                                      # someone else's settled failure
    tickets = [throttle.reserve([("k", 50, WINDOW), ("other", 50, WINDOW)])[1] for _ in range(3)]
    ids = [{event_id for _key, event_id in ticket.events} for ticket in tickets]
    assert len(set().union(*ids)) == 6                                                        # six distinct event ids
    throttle.release(tickets[1])
    left = {e[1] for e in events(throttle, "k")} | {e[1] for e in events(throttle, "other")}
    assert left >= ids[0] | ids[2] and not (left & ids[1])
    assert len(events(throttle, "k")) == 3 and len(events(throttle, "other")) == 2           # the settled failure and the other two tickets are untouched
    assert tickets[1].state == "released" and tickets[0].state == tickets[2].state == "open"


def test_releasing_one_ticket_frees_exactly_its_own_capacity():
    throttle, _ = make()
    first = throttle.reserve([("k", 2, WINDOW)])[1]
    second = throttle.reserve([("k", 2, WINDOW)])[1]
    assert throttle.reserve([("k", 2, WINDOW)])[1] is None
    throttle.release(first)
    third = throttle.reserve([("k", 2, WINDOW)])[1]
    assert third is not None and throttle.reserve([("k", 2, WINDOW)])[1] is None
    assert {e[1] for e in events(throttle, "k")} == {second.events[0][1], third.events[0][1]}


def test_a_ticket_leaves_the_open_state_once():
    throttle, _ = make()
    a, b, c = (throttle.reserve([("k", 50, WINDOW)])[1] for _ in range(3))
    throttle.settle(a)
    throttle.release(a)                                                                       # a settled failure cannot be released
    throttle.settle(a)
    assert a.state == "settled" and len(events(throttle, "k")) == 3
    throttle.release(b)
    throttle.release(b)                                                                       # twice: the second does nothing
    throttle.settle(b)                                                                        # and a released ticket cannot be settled
    assert b.state == "released" and len(events(throttle, "k")) == 2
    assert [e[2] for e in events(throttle, "k")] == [True, False] and c.state == "open"


def test_settle_marks_only_its_own_events():
    throttle, _ = make()
    a = throttle.reserve([("k", 50, WINDOW), ("j", 50, WINDOW)])[1]
    b = throttle.reserve([("k", 50, WINDOW), ("j", 50, WINDOW)])[1]
    throttle.settle(a)
    assert [e[2] for e in events(throttle, "k")] == [True, False] and [e[2] for e in events(throttle, "j")] == [True, False]
    assert b.state == "open"


def test_release_never_decrements_a_key_it_did_not_reserve():
    throttle, _ = make()
    for _ in range(4):
        throttle.record_failure("shared", WINDOW)
    ticket = throttle.reserve([("mine", 5, WINDOW)])[1]
    throttle.release(ticket)
    assert len(events(throttle, "shared")) == 4 and events(throttle, "mine") == [] and "mine" not in throttle._failures


def test_concurrent_releases_remove_exactly_the_released_tickets():
    throttle, _ = make()
    tickets = [throttle.reserve([("k", 100, WINDOW)])[1] for _ in range(40)]
    together(40, lambda i: throttle.release(tickets[i]) if i % 2 == 0 else None)
    left = {e[1] for e in events(throttle, "k")}
    assert left == {tickets[i].events[0][1] for i in range(1, 40, 2)}                          # the odd tickets, untouched


def test_the_same_ticket_released_by_many_threads_is_released_once():
    throttle, _ = make()
    keep = throttle.reserve([("k", 100, WINDOW)])[1]
    shared = throttle.reserve([("k", 100, WINDOW)])[1]
    together(30, lambda i: throttle.release(shared))
    assert [e[1] for e in events(throttle, "k")] == [keep.events[0][1]]


# ------------------------------------------------------------------ forgiving a success's typos
def test_forgive_drops_settled_failures_but_never_pending_attempts():
    throttle, _ = make()
    for _ in range(3):
        throttle.record_failure("user-key", WINDOW)                                           # three typos, settled
    in_flight = [throttle.reserve([("user-key", 50, WINDOW)])[1] for _ in range(2)]            # two attempts still running
    success = throttle.reserve([("user-key", 50, WINDOW)])[1]
    throttle.release(success, forgive=("user-key",))
    assert [e[1] for e in events(throttle, "user-key")] == [t.events[0][1] for t in in_flight]
    assert all(not e[2] for e in events(throttle, "user-key"))                                 # still pending
    for ticket in in_flight:
        throttle.settle(ticket)                                                                # and they still settle as failures afterwards
    assert [e[2] for e in events(throttle, "user-key")] == [True, True]


def test_forgive_touches_only_the_named_keys():
    throttle, _ = make()
    for key in ("user-key", "account-key", "address-key"):
        throttle.record_failure(key, WINDOW)
        throttle.record_failure(key, WINDOW)
    success = throttle.reserve([("user-key", 50, WINDOW), ("account-key", 50, WINDOW), ("address-key", 50, WINDOW)])[1]
    throttle.release(success, forgive=("user-key",))
    assert events(throttle, "user-key") == []                                                  # forgiven (and the empty key is gone)
    assert len(events(throttle, "account-key")) == 2 and len(events(throttle, "address-key")) == 2
    assert "user-key" not in throttle._failures and "user-key" not in throttle._windows


def test_forgive_is_part_of_the_release_so_a_repeat_does_nothing():
    throttle, _ = make()
    throttle.record_failure("user-key", WINDOW)
    success = throttle.reserve([("user-key", 50, WINDOW)])[1]
    throttle.release(success, forgive=("user-key",))
    throttle.record_failure("user-key", WINDOW)                                                # a new failure after the success
    throttle.release(success, forgive=("user-key",))                                           # a repeated (buggy) call must not forgive it
    assert len(events(throttle, "user-key")) == 1


# ------------------------------------------------------------------ invariants under a storm
def test_a_storm_of_reserve_settle_release_never_breaks_a_limit_or_leaks():
    throttle, _ = make()
    limits = {"a": 5, "b": 8}
    settled_total, lock = [0], threading.Lock()

    def worker(i):
        rng = random.Random(i)                                                                 # each thread's choices are fixed; only the interleaving varies
        for _ in range(300):
            wait, ticket = throttle.reserve([("a", limits["a"], WINDOW), ("b", limits["b"], WINDOW)])
            with throttle._lock:                                                               # the invariant, checked at every step
                assert len(throttle._failures.get("a", ())) <= limits["a"] and len(throttle._failures.get("b", ())) <= limits["b"]
            if ticket is None:
                continue
            if rng.random() < 0.15:
                throttle.settle(ticket)
                with lock:
                    settled_total[0] += 1
            else:
                throttle.release(ticket)
    together(8, worker)
    assert not pending(throttle, "a") and not pending(throttle, "b")                           # nothing is left reserved: no leak
    assert len(events(throttle, "a")) == settled_total[0] <= limits["a"] and len(events(throttle, "b")) == settled_total[0]
    ids = [e[1] for key in ("a", "b") for e in events(throttle, key)]
    assert len(ids) == len(set(ids))                                                           # event ids are unique across keys


def test_the_event_cap_cannot_be_reached_through_reservations():
    throttle, _ = make()
    results = together(150, lambda i: throttle.reserve([("k", Throttle.MAX_PER_KEY, WINDOW)]))
    assert sum(ticket is not None for _wait, ticket in results) == Throttle.MAX_PER_KEY
    assert len(events(throttle, "k")) == Throttle.MAX_PER_KEY


# ------------------------------------------------------------------ expiry, memory, resets
def test_an_unfinished_reservation_expires_so_a_crash_cannot_block_for_ever():
    throttle, clock = make()
    leaked = throttle.reserve([("k", 1, WINDOW)])[1]                                           # never settled or released
    assert throttle.reserve([("k", 1, WINDOW)])[1] is None
    clock["now"] += WINDOW + 1
    assert throttle.reserve([("k", 1, WINDOW)])[1] is not None and leaked.state == "open"
    throttle.release(leaked)                                                                   # finishing it late harms nobody: its events are gone, the new one is not its own
    assert len(events(throttle, "k")) == 1


def test_clearing_a_key_while_a_ticket_is_open_is_harmless():
    throttle, _ = make()
    ticket = throttle.reserve([("k", 5, WINDOW)])[1]
    throttle.clear("k")
    throttle.settle(ticket)
    throttle.release(ticket)
    assert "k" not in throttle._failures and "k" not in throttle._windows


def test_keys_with_pending_attempts_are_the_last_to_be_evicted():
    throttle, _ = make(max_keys=50)
    held = throttle.reserve([("in-flight", 5, WINDOW)])[1]
    for i in range(500):
        throttle.record_failure(f"flood-{i}", WINDOW)
        assert len(throttle._failures) <= 50
    assert len(pending(throttle, "in-flight")) == 1                                            # survived the flood
    throttle.settle(held)
    assert [e[2] for e in events(throttle, "in-flight")] == [True]


def test_a_key_at_its_limit_survives_a_flood_of_reservations():
    throttle, _ = make(max_keys=100)
    for _ in range(5):
        throttle.record_failure("blocked", WINDOW)
    for i in range(2000):
        wait, ticket = throttle.reserve([(f"new-{i}", 5, WINDOW)])
        throttle.settle(ticket) if i % 2 else throttle.release(ticket)
        assert len(throttle._failures) <= 100 and set(throttle._failures) == set(throttle._windows)
    assert throttle.reserve([("blocked", 5, WINDOW)])[1] is None


def test_the_ticket_type_holds_nothing_that_could_grow():
    assert Ticket.__slots__ == ("id", "events", "state")
    throttle, _ = make()
    for _ in range(1000):
        throttle.release(throttle.reserve([("k", 5, WINDOW)])[1])
    assert throttle._failures == {} and throttle._windows == {}                                # no registry of tickets, no leftover keys
    assert not hasattr(throttle, "_tickets") and not hasattr(throttle, "_open")


def test_existing_check_and_record_calls_still_work_and_count_as_settled():
    throttle, clock = make()
    for _ in range(3):
        throttle.record_failure("k", 60)
    assert throttle.blocked_for("k", 3, 60) > 0 and throttle.blocked_for("k", 4, 60) == 0
    assert all(e[2] for e in events(throttle, "k"))
    clock["now"] += 61
    assert throttle.blocked_for("k", 3, 60) == 0 and "k" not in throttle._failures
