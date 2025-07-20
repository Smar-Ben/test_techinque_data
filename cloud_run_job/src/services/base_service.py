from abc import ABC, abstractmethod


class BaseService(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def execute(self):
        raise NotImplementedError("Service must implement execute method.")
