from typing import Protocol


class Engine(Protocol):
    def start(self):
        pass

    def stop(self):
        pass


class AutoEngine(Engine):
    def start(self):
        print("Auto engine started")

    def stop(self):
        print("Auto engine stopped")


class PlaneEngine(Engine):
    def start(self):
        print("Plane engine started")

    def stop(self):
        print("Plane engine stopped")


def start_engine(engine: Engine):
    engine.start()


start_engine(AutoEngine())
start_engine(PlaneEngine())
