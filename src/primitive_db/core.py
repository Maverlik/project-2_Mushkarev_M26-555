import json

from primitive_db.constants import ID_COLUMN, ID_SCHEMA, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data, remove_table_data, save_table_data

select_cacher = create_cacher()


def require_table(metadata, table_name):
    """Возвращает схему таблицы или вызывает KeyError, если её нет."""
    if table_name not in metadata:
        raise KeyError(table_name)
    return metadata[table_name]


def validate_clauses(columns, *clauses):
    """Проверяет имена столбцов и точное соответствие значений типам схемы."""
    schema = {column["name"]: column["type"] for column in columns}
    for clause in clauses:
        for column, value in (clause or {}).items():
            if column not in schema:
                raise KeyError(column)
            if type(value) is not VALID_TYPES[schema[column]]:
                raise ValueError(
                    f'Столбец "{column}" должен иметь тип {schema[column]}.'
                )


def matches(record, where_clause):
    """Проверяет совпадение записи со всеми условиями выборки."""
    return all(
        record[column] == value for column, value in (where_clause or {}).items()
    )


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт пустую таблицу со схемой и автоматически добавляет ID:int."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None
    schema = [dict(ID_SCHEMA)]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное описание столбца: {column}.")
        column_name, column_type = parts
        if not column_name.isidentifier() or column_name in names:
            raise ValueError(f"Некорректный или повторный столбец: {column_name}.")
        if column_type not in VALID_TYPES:
            raise ValueError(f"Неподдерживаемый тип данных: {column_type}.")
        names.add(column_name)
        if column_name == ID_COLUMN:
            if column_type != ID_SCHEMA["type"]:
                raise ValueError("Столбец ID должен иметь тип int.")
        else:
            schema.append({"name": column_name, "type": column_type})
    save_table_data(table_name, [])
    metadata[table_name] = schema
    select_cacher(None, None)
    column_text = ", ".join(f"{column['name']}:{column['type']}" for column in schema)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {column_text}')
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет схему таблицы и её файл данных после подтверждения."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None
    remove_table_data(table_name)
    del metadata[table_name]
    select_cacher(None, None)
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


@handle_db_errors
def list_tables(metadata):
    """Выводит имена таблиц или сообщение об отсутствии таблиц."""
    if not metadata:
        print("Таблиц пока нет.")
    for table_name in metadata:
        print(f"- {table_name}")


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Проверяет значения и возвращает данные с новой записью и уникальным ID."""
    columns = require_table(metadata, table_name)
    user_columns = [column for column in columns if column["name"] != ID_COLUMN]
    if len(values) != len(user_columns):
        raise ValueError(
            f"Ожидается {len(user_columns)} значений без ID, получено {len(values)}."
        )
    record = dict(zip((column["name"] for column in user_columns), values))
    validate_clauses(columns, record)
    table_data = load_table_data(table_name)
    next_id = max((row[ID_COLUMN] for row in table_data), default=0) + 1
    record = {ID_COLUMN: next_id, **record}
    table_data.append(record)
    select_cacher(None, None)
    print(f'Запись с ID={next_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает копии подходящих записей, кэшируя одинаковые выборки."""
    cache_key = json.dumps([table_data, where_clause], sort_keys=True)
    result = select_cacher(
        cache_key,
        lambda: [
            dict(record) for record in table_data if matches(record, where_clause)
        ],
    )
    return [dict(record) for record in result]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет поля подходящих записей и сбрасывает кэш выборок."""
    if ID_COLUMN in set_clause:
        raise ValueError("Столбец ID генерируется автоматически и не изменяется.")
    for record in table_data:
        if matches(record, where_clause):
            record.update(set_clause)
    select_cacher(None, None)
    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """После подтверждения возвращает данные без подходящих под условие записей."""
    remaining = [record for record in table_data if not matches(record, where_clause)]
    select_cacher(None, None)
    return remaining


@handle_db_errors
def info(metadata, table_name):
    """Выводит название, схему и количество записей таблицы."""
    columns = require_table(metadata, table_name)
    column_text = ", ".join(f"{column['name']}:{column['type']}" for column in columns)
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {column_text}")
    print(f"Количество записей: {len(load_table_data(table_name))}")
