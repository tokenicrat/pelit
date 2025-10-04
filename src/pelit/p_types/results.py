from typing import Generic, TypeVar, Union


T = TypeVar("T")
E = TypeVar("E")

class Ok(Generic[T]):
    """
    Rust 风格的 Ok 类型，表示成功结果

    Attributes:
        value: 任意类型的值
    """
    def __init__(self, value: T) -> None:
        self.value = value
    def __repr__(self) -> str:
        if hasattr(self.value, '__repr__'):
            return f"{self.value}"
        else:
            return "<value>"

class Err(Generic[E]):
    """
    Rust 风格的 Err 类型，表示报错

    Attributes:
        error: 任意类型的报错信息，建议使用 str
    """
    def __init__(self, error: E) -> None:
        self.error = error
    def __repr__(self) -> str:
        if hasattr(self.error, '__repr__'):
            return f"{self.error}"
        else:
            return "<error>"

# Rust 风格的 Result 类型，包含 Ok 和 Err
Result = Union[Ok[T], Err[E]]
