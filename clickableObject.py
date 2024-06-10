from abc import abstractmethod


class ClickableObject:
    @abstractmethod
    def is_clicked(self, x: float, y: float) -> bool:
        pass
