import pytest

from src.main import MatchingEngine, Order, Trade


def scenario0():
    order_inputs = """5
09:30:00 1 b 100 l 9.99
09:31:00 2 b 1000 l 9.95
09:32:00 3 s 100 l 10.01
09:33:00 4 s 1000 l 10.05
09:41:00 5 b 200 m -1.00"""

    trade_outputs = """09:41:00 5 3 10.01 100
09:41:00 5 4 10.05 100"""

    return order_inputs, trade_outputs


def scenario1():
    order_inputs = """4
10:05:00 1 b 100 m -1.00
10:05:01 2 s 50 m -1.00
10:10:07 3 s 200 l 10.01
10:15:10 4 b 100 m -1.00"""

    trade_outputs = """10:15:10 4 3 10.01 100"""

    return order_inputs, trade_outputs


def scenario2():
    order_inputs = """5
09:30:00 1 b 100 l 9.99
09:31:00 2 b 1000 l 9.95
09:32:00 3 s 100 l 10.01
09:33:00 4 s 1000 l 9.99
09:41:00 5 b 200 m -1.00"""

    trade_outputs = """09:33:00 1 4 9.99 100
09:41:00 5 4 9.99 200"""

    return order_inputs, trade_outputs


def scenario3():
    order_inputs = """5
14:00:00 1 s 100 l 10.00
14:00:30 2 s 100 l 10.00
14:01:00 3 s 100 l 9.00
14:01:30 4 s 100 l 9.00
15:00:00 5 b 500 m -1.00"""

    trade_outputs = """15:00:00 5 3 9.00 100
15:00:00 5 4 9.00 100
15:00:00 5 1 10.00 100
15:00:00 5 2 10.00 100"""

    return order_inputs, trade_outputs


def scenario_not_crossing_spread_no_trade():
    order_inputs = """2
09:30:00 1 b 100 l 9.99
09:31:00 2 s 100 l 10.01
"""

    trade_outputs = """"""

    return order_inputs, trade_outputs


def scenario_partial_fill_and_order():
    order_inputs = """6
09:30:00 1 b 100 l 9.99
09:31:00 2 s 50 l 9.95
09:32:00 3 s 400 l 9.95
09:33:00 4 b 50 l 9.98
09:34:00 5 b 100 m -1.00
09:35:00 6 b 200 m -1.00
"""

    trade_outputs = """09:31:00 1 2 9.99 50
09:32:00 1 3 9.99 50
09:33:00 4 3 9.95 50
09:34:00 5 3 9.95 100
09:35:00 6 3 9.95 200
"""

    return order_inputs, trade_outputs


def scenario_fill_across_multiple_orders():
    order_inputs = """7
09:30:00 1 s 100 l 9.95
09:31:00 2 s 200 l 9.96
09:32:00 3 s 300 l 9.97
09:32:00 4 s 400 l 9.98
09:33:00 5 b 50 l 9.94
09:34:00 6 b 200 l 9.99
09:35:00 7 b 800 m -1.00
"""

    trade_outputs = """09:34:00 6 1 9.95 100
09:34:00 6 2 9.96 100
09:35:00 7 2 9.96 100
09:35:00 7 3 9.97 300
09:35:00 7 4 9.98 400
"""

    return order_inputs, trade_outputs


SCENARIOS_PROVIDED = [scenario0(), scenario1(), scenario2(), scenario3()]
ADDITIONAL_SCENARIOS = [scenario_not_crossing_spread_no_trade(),
                        scenario_partial_fill_and_order(),
                        scenario_fill_across_multiple_orders()]


@pytest.mark.parametrize("scenario", SCENARIOS_PROVIDED + ADDITIONAL_SCENARIOS)
def test_matching_engine(scenario):
    me = MatchingEngine()
    order_inputs, trade_outputs = scenario
    _, *orders = order_inputs.splitlines()

    for i, line_item in enumerate(orders):
        order = Order.parse(i, line_item)
        me.process(order)

    assert me.trades == [Trade.parse(t) for t in trade_outputs.splitlines()]
