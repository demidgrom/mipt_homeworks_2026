import json
import time
from datetime import datetime, timezone
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    func_name: str
    block_time: datetime
    msg_error: str

    def __init__(self, func: CallableWithMeta[P, R_co], msg: str, original_exc: BaseException | None = None):
        self.func_name = func.__module__ + "." + func.__name__
        self.block_time = datetime.now(timezone.UTC)
        self.msg_error = msg
        super().__init__(msg)
        if original_exc is not None:
            self.__cause__ = original_exc


class CircuitBreaker:
    critical_count_: int
    time_to_recover_: int
    triggers_on_: type[Exception]
    errors_count_: int = 0
    status_: bool = True
    opened_at_: float | None = None

    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception
    ):
        errors: list[ValueError] = []

        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))

        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count_ = critical_count
        self.time_to_recover_ = time_to_recover
        self.triggers_on_ = triggers_on

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        def func_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            res: R_co

            if self.status_ is False:
                if self.opened_at_ is not None and (time.time() - self.opened_at_) < self.time_to_recover_:
                    raise BreakerError(func, TOO_MUCH)

                self.status_ = True
                self.errors_count_ = 0

            try:
                res = func(*args, **kwargs)
                self.errors_count_ = 0
            except self.triggers_on_ as err:
                self.errors_count_ += 1
                if self.errors_count_ >= self.critical_count_:
                    self.status_ = False
                    self.opened_at_ = time.time()
                    raise BreakerError(func, TOO_MUCH, err) from err
                raise
            return res

        func_wrapper.__name__ = func.__name__
        func_wrapper.__module__ = func.__module__
        return func_wrapper


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту
    Args:
        post_id (int): Идентификатор поста
    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
