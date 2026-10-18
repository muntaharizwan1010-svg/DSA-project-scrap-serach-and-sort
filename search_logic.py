
import re


STRING_OPERATORS = [
    "Contains",
    "Does not contain",
    "Starts with",
    "Ends with",
    "Equals",
    "Does not equal",
    "Is empty",
    "Is not empty",
]

NUMERIC_OPERATORS = [
    "Equals",
    "Does not equal",
    "Greater than",
    "Less than",
    "Greater than or equal to",
    "Less than or equal to",
    "Is empty",
    "Is not empty",
]


def normalize(value):
    return str(value or "").strip()


def to_number(value):
    """Extract a numeric value, returning None if unavailable."""
    text = normalize(value).replace(",", "")

    if not text:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def is_numeric_column(column):
    return column in {
        "rating",
        "ratings_count",
        "want_to_read",
        "first_published",
        "editions",
    }


def get_operators(column):
    if is_numeric_column(column):
        return NUMERIC_OPERATORS
    return STRING_OPERATORS


def evaluate_condition(book, column, operator, query):
    actual = normalize(book.get(column, ""))
    expected = normalize(query)

    if operator == "Is empty":
        return not actual

    if operator == "Is not empty":
        return bool(actual)

    if is_numeric_column(column):
        actual_num = to_number(actual)
        expected_num = to_number(expected)

        if actual_num is None or expected_num is None:
            return False

        if operator == "Equals":
            return actual_num == expected_num
        if operator == "Does not equal":
            return actual_num != expected_num
        if operator == "Greater than":
            return actual_num > expected_num
        if operator == "Less than":
            return actual_num < expected_num
        if operator == "Greater than or equal to":
            return actual_num >= expected_num
        if operator == "Less than or equal to":
            return actual_num <= expected_num

        return False

    actual_lower = actual.casefold()
    expected_lower = expected.casefold()

    if operator == "Contains":
        return expected_lower in actual_lower
    if operator == "Does not contain":
        return expected_lower not in actual_lower
    if operator == "Starts with":
        return actual_lower.startswith(expected_lower)
    if operator == "Ends with":
        return actual_lower.endswith(expected_lower)
    if operator == "Equals":
        return actual_lower == expected_lower
    if operator == "Does not equal":
        return actual_lower != expected_lower

    return False


def search_books(books, conditions):
    """
    Each condition contains:
      column, operator, value, negate, join

    The first condition has no join requirement.
    Each later condition uses AND or OR to combine with
    the result accumulated so far.
    NOT negates that individual condition.
    """
    if not conditions:
        return list(books)

    results = []

    for book in books:
        combined = None

        for index, condition in enumerate(conditions):
            result = evaluate_condition(
                book,
                condition["column"],
                condition["operator"],
                condition["value"],
            )

            if condition.get("negate", False):
                result = not result

            if combined is None:
                combined = result
            elif condition.get("join", "AND") == "OR":
                combined = combined or result
            else:
                combined = combined and result

        if combined:
            results.append(book)

    return results
