from collections import deque
from dataclasses import dataclass
from datetime import datetime
from heapq import heappop, heappush
from typing import List

BUY = "b"
SELL = "s"
MARKET = "m"
LIMIT = "l"


@dataclass
class Order:
    id_: int  # added unique identifier
    time_: datetime.time
    client_id: int
    direction: str  # b or s (buy or sell)
    size: int  # number of shares traded
    type_: str  # m or l (market or limit)
    price: float

    def can_execute(self, order) -> bool:
        """Return true if at least part of the order can fill."""
        if order.direction == self.direction:
            return False
        elif order.type_ == MARKET:
            return self.size >= 0
        elif order.direction == BUY and order.price >= self.price:
            return self.size >= 0
        elif order.direction == SELL and order.price <= self.price:
            return self.size >= 0
        else:
            return False

    def reduce(self, size: int):
        """Reduce order size on partial fill, feels a bit hacky.."""
        self.size -= size

    @classmethod
    def parse(cls, order_id: int, line: str):
        item = line.split()
        return cls(
            id_=order_id,
            time_=datetime.strptime(item[0], "%H:%M:%S").time(),
            client_id=int(item[1]),
            direction=item[2],
            size=int(item[3]),
            type_=item[4],
            price=float(item[5]),
        )

    @property
    def key(self):
        return self.direction, self.price


@dataclass
class Trade:
    time_: datetime.time
    buy_client_id: int
    sell_client_id: int
    price: float
    size: int  # number of shares traded

    @classmethod
    def create(cls, executing_order: Order, consumed_order: Order, qty_executed: int):
        if executing_order.direction == BUY:
            buy_client_id = executing_order.client_id
            sell_client_id = consumed_order.client_id
        else:
            buy_client_id = consumed_order.client_id
            sell_client_id = executing_order.client_id

        return cls(executing_order.time_,
                   buy_client_id,
                   sell_client_id,
                   consumed_order.price,
                   qty_executed)

    @classmethod
    def parse(cls, line: str):
        item = line.split()
        return cls(
            time_=datetime.strptime(item[0], "%H:%M:%S").time(),
            buy_client_id=int(item[1]),
            sell_client_id=int(item[2]),
            price=float(item[3]),
            size=int(item[4]),
        )

    def __str__(self):
        return f"{self.time_} {self.buy_client_id} {self.sell_client_id} {self.price} {self.size}"


class Limit:
    """
    Data structure to store orders by direction and price and keep track of available volume.
    Using deque to store orders for O(1) pop and append to both head and tail.
    """

    def __init__(self, direction: str, price: float):
        self.direction = direction
        self.price = price
        self.total_volume = 0
        self._orders = deque([])

    def add(self, order: Order):
        self._orders.append(order)
        self.total_volume += order.size

    def put(self, order: Order):
        """Used if order only partially filled."""
        self._orders.appendleft(order)
        self.total_volume += order.size

    def can_execute(self, order: Order) -> bool:
        """Return true if at least part of the order can fill."""
        if order.direction == self.direction:
            return False
        elif order.type_ == MARKET:
            return self.total_volume >= 0
        elif order.direction == BUY and order.price >= self.price:
            return self.total_volume >= 0
        elif order.direction == SELL and order.price <= self.price:
            return self.total_volume >= 0
        else:
            return False

    def pop(self) -> Order:
        try:
            order = self._orders.popleft()
            self.total_volume -= order.size
            return order
        except IndexError as e:
            raise e

    def is_empty(self) -> bool:
        return self.total_volume == 0

    def __len__(self):
        return len(self._orders)

    def __iter__(self):
        return iter(self._orders)

    def __lt__(self, other):
        if self.direction == BUY:
            return self.price > other.price
        return self.price < other.price


class OrderBook:
    """
    For a given instrument store both sides of the book, using min heap property and
    ordering of Limits to give O(1) access to the inside of the book.
    """

    def __init__(self, ticker="XYZ"):
        self.ticker = ticker
        self._limits = {}
        self._buy_limits = []
        self._sell_limits = []

    def add_order(self, order: Order):
        if order.key not in self._limits:
            limit = Limit(*order.key)
            self._limits[order.key] = limit
        else:
            limit = self._limits[order.key]

        limit.add(order)
        self.add_limit(limit)

    def add_limit(self, limit: Limit):
        if limit.direction == BUY:
            heappush(self._buy_limits, limit)
        elif limit.direction == SELL:
            heappush(self._sell_limits, limit)

    def pop_limit(self, direction: str) -> Limit:
        if direction == BUY:
            return heappop(self._sell_limits)
        return heappop(self._buy_limits)

    def peek_limit(self, direction) -> Limit:
        if direction == BUY:
            return self._sell_limits[0]
        return self._buy_limits[0]

    def execute(self, order: Order) -> List[Trade]:
        trades = []
        qty_to_execute = order.size

        while qty_to_execute > 0:
            try:
                curr_limit = self.peek_limit(order.direction)
            except IndexError:
                if order.size > 0 and order.type_ == LIMIT:
                    self.add_order(order)
                return trades

            if not curr_limit.can_execute(order):
                self.add_order(order)
                return trades

            curr_limit = self.pop_limit(order.direction)

            while not curr_limit.is_empty():
                try:
                    next_order = curr_limit.pop()
                except IndexError:
                    break

                # partial fill check
                if qty_to_execute < next_order.size:
                    next_order.reduce(qty_to_execute)
                    curr_limit.put(next_order)

                qty = min(qty_to_execute, next_order.size)
                trade = Trade.create(order, next_order, qty)
                trades.append(trade)
                qty_to_execute -= trade.size
                order.reduce(trade.size)

                if qty_to_execute == 0:
                    if curr_limit.total_volume > 0:
                        self.add_limit(curr_limit)
                    return trades

        return trades


class MatchingEngine:

    def __init__(self):
        self.ob = OrderBook()
        self.trades = []

    def process(self, order: Order):
        if order.type_ == MARKET:
            trades = self.ob.execute(order)
            self.trades.extend(trades)
        else:
            try:
                limit = self.ob.peek_limit(order.direction)
            except IndexError:
                self.ob.add_order(order)
            else:
                if limit.can_execute(order):
                    trades = self.ob.execute(order)
                    self.trades.extend(trades)
                else:
                    self.ob.add_order(order)


def solve():
    order_inputs = input()
    _, *orders = order_inputs.splitlines()
    me = MatchingEngine()

    for i, line_item in enumerate(orders):
        try:
            order = Order.parse(i, line_item)
        except Exception as e:
            # taking the decision to throw away junk input, this might not be wise!
            continue
        me.process(order)

    for t in me.trades:
        print(t, end="\n")


if __name__ == "__main__":
    solve()
