import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import COMMAND_PROMPT, HELP_TEXT, ID_COLUMN, META_FILE
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Выводит справку по командам базы данных."""
    print(HELP_TEXT)


def print_records(columns, records):
    """Выводит записи в PrettyTable с порядком столбцов из схемы."""
    table = PrettyTable()
    table.field_names = [column["name"] for column in columns]
    for record in records:
        table.add_row([record[column["name"]] for column in columns])
    print(table)


def process_data_command(metadata, parsed):
    """Выполняет CRUD-команду и сохраняет успешные изменения данных."""
    table_name = parsed["table"]
    columns = core.require_table(metadata, table_name)
    command = parsed["command"]
    if command == "insert":
        table_data = core.insert(metadata, table_name, parsed["values"])
        if table_data is not None:
            save_table_data(table_name, table_data)
        return
    table_data = load_table_data(table_name)
    where_clause = parsed["where"]
    core.validate_clauses(columns, where_clause, parsed.get("set"))
    if command == "select":
        records = core.select(table_data, where_clause)
        if records is not None:
            print_records(columns, records)
        return
    affected_ids = [
        record[ID_COLUMN] for record in table_data if core.matches(record, where_clause)
    ]
    if command == "update":
        changed_data = core.update(table_data, parsed["set"], where_clause)
    else:
        changed_data = core.delete(table_data, where_clause)
    if changed_data is None:
        return
    save_table_data(table_name, changed_data)
    for record_id in affected_ids:
        if command == "update":
            print(
                f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.'
            )
        else:
            print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')
    if not affected_ids:
        print("Записи по заданному условию не найдены.")


@handle_db_errors
def execute_command(user_input):
    """Разбирает команду, вызывает операцию и возвращает False для выхода."""
    parsed = parse_command(user_input)
    command = parsed["command"]
    if command == "exit":
        return False
    if command == "help":
        print_help()
        return True
    if command == "unknown":
        print(f"Функции {parsed['name']} нет. Попробуйте снова.")
        return True
    metadata = load_metadata(META_FILE)
    if command == "create_table":
        changed_metadata = core.create_table(
            metadata, parsed["table"], parsed["columns"]
        )
        if changed_metadata is not None:
            save_metadata(META_FILE, changed_metadata)
    elif command == "drop_table":
        changed_metadata = core.drop_table(metadata, parsed["table"])
        if changed_metadata is not None:
            save_metadata(META_FILE, changed_metadata)
    elif command == "list_tables":
        core.list_tables(metadata)
    elif command == "info":
        core.info(metadata, parsed["table"])
    else:
        process_data_command(metadata, parsed)
    return True


def run():
    """Читает команды до exit, конца ввода или прерывания пользователем."""
    print_help()
    while True:
        try:
            user_input = prompt.string(COMMAND_PROMPT)
            if execute_command(user_input) is False:
                return
        except (EOFError, KeyboardInterrupt):
            print()
            return


def welcome():
    """Запускает интерактивную работу с базой данных."""
    run()
