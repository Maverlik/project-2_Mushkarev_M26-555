import json
import os

from primitive_db.constants import DATA_DIR


def load_metadata(filepath):
    """Загружает схемы из JSON или возвращает пустой словарь при отсутствии файла."""
    try:
        with open(filepath, encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
    except FileNotFoundError:
        return {}
    if not isinstance(metadata, dict):
        raise ValueError("Файл метаданных должен содержать словарь.")
    return metadata


def save_metadata(filepath, data):
    """Сохраняет метаданные таблиц в JSON с кодировкой UTF-8."""
    with open(filepath, "w", encoding="utf-8") as metadata_file:
        json.dump(data, metadata_file, ensure_ascii=False, indent=4)


def table_filepath(table_name):
    """Проверяет имя таблицы и возвращает путь к её JSON-файлу."""
    if not isinstance(table_name, str) or not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Загружает записи таблицы или возвращает пустой список, если файла нет."""
    try:
        with open(table_filepath(table_name), encoding="utf-8") as table_file:
            table_data = json.load(table_file)
    except FileNotFoundError:
        return []
    if not isinstance(table_data, list) or not all(
        isinstance(record, dict) for record in table_data
    ):
        raise ValueError("Файл таблицы должен содержать список записей.")
    return table_data


def save_table_data(table_name, data):
    """Создаёт директорию данных и сохраняет записи таблицы в JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(table_filepath(table_name), "w", encoding="utf-8") as table_file:
        json.dump(data, table_file, ensure_ascii=False, indent=4)


def remove_table_data(table_name):
    """Удаляет файл таблицы, если он существует."""
    filepath = table_filepath(table_name)
    if os.path.exists(filepath):
        os.remove(filepath)
