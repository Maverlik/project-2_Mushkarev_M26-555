import shlex


def tokenize_fragment(fragment):
    """Разбирает фрагмент без строковых литералов на слова и разделители."""
    lexer = shlex.shlex(fragment, posix=False, punctuation_chars="(),=")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = []
    for token in lexer:
        if all(character in "(),=" for character in token):
            tokens.extend(token)
        else:
            tokens.append(token)
    return tokens


def tokenize(user_input):
    """Разбивает команду на токены, сохраняя строки и экранированные кавычки."""
    tokens = []
    position = 0
    fragment_start = 0
    while position < len(user_input):
        quote = user_input[position]
        if quote not in "\"'":
            position += 1
            continue
        tokens.extend(tokenize_fragment(user_input[fragment_start:position]))
        quote_start = position
        position += 1
        escaped = False
        while position < len(user_input):
            character = user_input[position]
            if character == quote and not escaped:
                break
            if quote == '"' and character == "\\" and not escaped:
                escaped = True
            else:
                escaped = False
            position += 1
        if position == len(user_input):
            raise ValueError("Строка должна заканчиваться закрывающей кавычкой.")
        tokens.append(user_input[quote_start : position + 1])
        position += 1
        fragment_start = position
    tokens.extend(tokenize_fragment(user_input[fragment_start:]))
    return tokens


def parse_value(token):
    """Преобразует токен в int, bool или строку, заключённую в кавычки."""
    if len(token) >= 2 and token[0] in "\"'" and token[-1] == token[0]:
        return shlex.split(token)[0]
    if token.lower() in ("true", "false"):
        return token.lower() == "true"
    try:
        return int(token)
    except ValueError as error:
        raise ValueError(
            f"Некорректное значение: {token}. Строки заключайте в кавычки."
        ) from error


def parse_assignments(tokens):
    """Преобразует присваивания столбец = значение в словарь."""
    if not tokens:
        raise ValueError("Условие не может быть пустым.")
    assignments = {}
    position = 0
    while position < len(tokens):
        if position + 2 >= len(tokens) or tokens[position + 1] != "=":
            raise ValueError("Ожидается условие: <столбец> = <значение>.")
        column = tokens[position]
        if not column.isidentifier() or column in assignments:
            raise ValueError(f"Некорректный или повторный столбец: {column}.")
        assignments[column] = parse_value(tokens[position + 2])
        position += 3
        if position < len(tokens):
            if tokens[position] != ",":
                raise ValueError("Несколько присваиваний разделяются запятыми.")
            position += 1
            if position == len(tokens):
                raise ValueError("После запятой ожидается присваивание.")
    return assignments


def parse_values(tokens):
    """Разбирает список значений в скобках с обязательными запятыми."""
    if len(tokens) < 2 or tokens[0] != "(" or tokens[-1] != ")":
        raise ValueError("Список значений должен быть заключён в круглые скобки.")
    values = []
    inner_tokens = tokens[1:-1]
    for position, token in enumerate(inner_tokens):
        if position % 2:
            if token != ",":
                raise ValueError("Значения должны быть разделены запятыми.")
        else:
            values.append(parse_value(token))
    if inner_tokens and len(inner_tokens) % 2 == 0:
        raise ValueError("После запятой ожидается значение.")
    return values


def parse_command(user_input):
    """Преобразует пользовательскую строку в команду и структурированные аргументы."""
    tokens = tokenize(user_input)
    if not tokens:
        raise ValueError("Команда не может быть пустой.")
    command = tokens[0].lower()
    if command in ("help", "exit", "list_tables") and len(tokens) == 1:
        return {"command": command}
    if command == "create_table" and len(tokens) >= 3:
        return {"command": command, "table": tokens[1], "columns": tokens[2:]}
    if command in ("drop_table", "info") and len(tokens) == 2:
        return {"command": command, "table": tokens[1]}
    if command == "insert" and len(tokens) >= 6:
        if tokens[1].lower() == "into" and tokens[3].lower() == "values":
            return {
                "command": command,
                "table": tokens[2],
                "values": parse_values(tokens[4:]),
            }
    if command in ("select", "delete") and len(tokens) >= 3:
        if tokens[1].lower() == "from":
            if command == "select" and len(tokens) == 3:
                return {"command": command, "table": tokens[2], "where": None}
            if len(tokens) >= 7 and tokens[3].lower() == "where":
                return {
                    "command": command,
                    "table": tokens[2],
                    "where": parse_assignments(tokens[4:]),
                }
    if command == "update" and len(tokens) >= 10:
        if tokens[2].lower() == "set":
            where_position = next(
                (
                    index
                    for index in range(6, len(tokens), 4)
                    if tokens[index].lower() == "where"
                ),
                None,
            )
            if where_position is not None:
                return {
                    "command": command,
                    "table": tokens[1],
                    "set": parse_assignments(tokens[3:where_position]),
                    "where": parse_assignments(tokens[where_position + 1 :]),
                }
    if command not in (
        "help",
        "exit",
        "list_tables",
        "create_table",
        "drop_table",
        "info",
        "insert",
        "select",
        "delete",
        "update",
    ):
        return {"command": "unknown", "name": tokens[0]}
    raise ValueError(f"Некорректная команда: {user_input}. Попробуйте снова.")
