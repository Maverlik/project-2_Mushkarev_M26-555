META_FILE = "db_meta.json"
DATA_DIR = "data"
VALID_TYPES = {"int": int, "str": str, "bool": bool}
ID_COLUMN = "ID"
ID_SCHEMA = {"name": ID_COLUMN, "type": "int"}
COMMAND_PROMPT = ">>> Введите команду: "
CONFIRM_PROMPT = 'Вы уверены, что хотите выполнить "{action}"? [y/n]: '
HELP_TEXT = """***База данных***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу
<command> insert into <имя_таблицы> values (<значение1>, ...) - создать запись
<command> select from <имя_таблицы> [where <столбец> = <значение>] - прочитать записи
<command> update <имя_таблицы> set <столбец> = <значение> where <столбец> = <значение>
<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить записи
<command> info <имя_таблицы> - вывести информацию о таблице
<command> exit - выход из программы
<command> help - справочная информация
Типы данных: int, str, bool. Строки вводятся в кавычках, bool — true или false.
"""
