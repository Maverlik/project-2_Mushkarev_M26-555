import time

from primitive_db.constants import CONFIRM_PROMPT


def handle_db_errors(func):
    """Оборачивает функцию обработкой ожидаемых ошибок базы данных."""

    def wrapper(*args, **kwargs):
        """Выполняет операцию и выводит понятное сообщение при ошибке."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except (ValueError, TypeError) as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлом: {error}")
        return None

    wrapper.__name__ = func.__name__
    return wrapper


def confirm_action(action_name):
    """Создаёт декоратор подтверждения действия ответом y."""

    def decorator(func):
        """Добавляет запрос подтверждения перед вызовом функции."""

        def wrapper(*args, **kwargs):
            """Выполняет действие при подтверждении или сообщает об отмене."""
            answer = input(CONFIRM_PROMPT.format(action=action_name))
            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def log_time(func):
    """Добавляет вывод времени выполнения функции в секундах."""

    def wrapper(*args, **kwargs):
        """Возвращает результат операции и выводит затраченное время."""
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start_time
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд")
        return result

    wrapper.__name__ = func.__name__
    return wrapper


def create_cacher():
    """Возвращает функцию с собственным словарём кэша в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        """Кэширует вычисление по ключу; value_func=None очищает весь кэш."""
        if value_func is None:
            cache.clear()
            return None
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    return cache_result
