"""Dijkstra routing with the shared educational dispatch model."""
from dispatcher import Dispatcher
from routing import best_first


class DijkstraDispatcher(Dispatcher):
    algorithm = "dijkstra"

    def dijkstra(self, start, end):
        return self._measure(lambda: best_first(self.network, start, end))

    def route(self, start, end):
        return self.dijkstra(start, end)


def main():
    DijkstraDispatcher().run_simulation()


if __name__ == "__main__":
    main()