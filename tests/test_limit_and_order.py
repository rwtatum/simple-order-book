from collections import deque
from datetime import datetime

import pytest

from src.main import Order, Limit


def test_limit_add_and_pop():
    limit = Limit("b", 9.99)
    orders = [
        ("09:30:00 1 b 100 l 9.99", 1, 100),
        ("09:31:00 2 b 200 l 9.99", 2, 300),
        ("09:30:00 1 b 300 l 9.99", 3, 600),
        ("09:30:00 1 b 400 l 9.99", 4, 1000),
    ]
    assert limit.is_empty() is True

    for i, (order, limit_len, total_volume) in enumerate(orders):
        limit.add(Order.parse(i, order))
        assert limit.is_empty() is False
        assert len(limit) == limit_len
        assert limit.total_volume == total_volume

    for i, limit_volume in enumerate([900, 700, 400, 0], start=1):
        limit.pop()
        assert limit.total_volume == limit_volume
        assert len(orders) - i == len(limit)

    assert limit.is_empty() is True


def test_limit_ordering():
    prices = (5, 2.22, 3, 12, 99, 7)
    buy_limits = sorted([Limit("b", p) for p in prices])
    sells_limits = sorted([Limit("s", p) for p in prices])

    assert [limit.price for limit in buy_limits] == sorted(prices, reverse=True)
    assert [limit.price for limit in sells_limits] == sorted(prices)


def test_limit_iter():
    limit = Limit("b", 10)
    orders = [Order.parse(i, "09:30:00 1 b 100 l 9.99") for i in range(5)]
    limit._orders = deque(orders)
    counter = 0

    while not limit.is_empty():
        assert counter == limit.pop().id_
        counter += 1


def test_parse_single_order():
    ord0 = "09:30:00 1 b 100 l 9.99"
    tm = datetime(1900, 1, 1, 9, 30, 0, 0).time()
    assert Order.parse(0, ord0) == Order(0, tm, 1, "b", 100, "l", 9.99)


@pytest.mark.parametrize("ord0,ord1,expected", [
    ("09:30:00 1 b 100 l 9.98", "09:31:00 1 s 100 l 9.99", False),
    ("09:30:00 1 b 100 l 9.98", "09:31:00 1 s 100 l 9.97", True),
    ("09:30:00 1 b 100 l 9.98", "09:31:00 1 s 90 l 9.97", True),
    ("09:30:00 1 b 100 l 9.98", "09:31:00 1 s 100 l 9.97", True),
    ("09:30:00 1 s 100 l 9.98", "09:31:00 1 b 100 l 9.97", False),
    ("09:30:00 1 s 100 l 9.98", "09:31:00 1 b 110 l 9.99", True),
    ("09:30:00 1 s 100 l 9.98", "09:31:00 1 b 90 l 9.99", True),
    ("09:30:00 1 s 100 l 9.98", "09:31:00 1 b 100 l 9.99", True),
    ("09:30:00 1 s 100 l 9.98", "09:31:00 1 b 100 l 9.98", True),
    ("09:30:00 1 s 100 l 9.98", "09:31:00 1 s 100 l 9.98", False),
    ("09:30:00 1 b 100 l 9.98", "09:31:00 1 s 100 l 9.98", True),
])
def test_limit_can_execute_limit_order(ord0, ord1, expected):
    order0 = Order.parse(0, ord0)
    order1 = Order.parse(1, ord1)

    limit0 = Limit(*order0.key)
    limit0.add(order0)
    assert limit0.can_execute(order1) is expected

    limit1 = Limit(*order1.key)
    limit1.add(order1)
    assert limit1.can_execute(order0) is expected


@pytest.mark.parametrize("ord0,ord1,expected", [
    ("09:30:00 1 b 100 l 9.98", "09:31:00 1 s 100 m -1.00", True),
    ("09:30:00 1 s 100 l 9.98", "09:31:00 1 b 100 m -1.00", True),
    ("09:30:00 1 s 100 m 9.98", "09:31:00 1 s 90 m -1.00", False),
])
def test_limit_can_execute_market_order(ord0, ord1, expected):
    order0 = Order.parse(0, ord0)
    order1 = Order.parse(1, ord1)

    limit0 = Limit(*order0.key)
    limit0.add(order0)
    assert limit0.can_execute(order1) is expected
