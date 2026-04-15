import json
from datetime import datetime, timedelta, timezone
from time import time
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

    def __init__(
        self,
        func: CallableWithMeta[P, R_co],
        msg: str,
        original_exc: BaseException | None = None,
    ):
        self.func_name = f"{func.__module__}.{func.__name__}"
        self.block_time = datetime.now(timezone(timedelta(hours=0)))
        self.msg_error = msg
        super().__init__(msg)
        if original_exc is not None:
            self.__cause__ = original_exc


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        errors: list[ValueError] = []

        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))

        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self.errors_count = 0
        self.status = True
        self.opened_at: float | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        def func_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            self._handle_open_state(func)
            return self._execute_request(func, args, kwargs)

        func_wrapper.__name__ = func.__name__
        func_wrapper.__module__ = func.__module__
        return func_wrapper

    def _handle_open_state(self, func: CallableWithMeta[P, R_co]) -> None:
        if not self.status:
            if self.opened_at is not None and (time() - self.opened_at) < self.time_to_recover:
                raise BreakerError(func, TOO_MUCH)
            self.status = True
            self.errors_count = 0

    def _execute_request(
        self,
        func: CallableWithMeta[P, R_co],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        try:
            result = func(*args, **kwargs)
        except self.triggers_on as err:
            self.errors_count += 1
            if self.errors_count >= self.critical_count:
                self.status = False
                self.opened_at = time()
                raise BreakerError(func, TOO_MUCH, err) from err
            raise
        else:
            self.errors_count = 0
            return result


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту.

    Args:
        post_id (int): Идентификатор поста.

    Returns:
        list[dict[int | str]]: Список комментариев.
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
