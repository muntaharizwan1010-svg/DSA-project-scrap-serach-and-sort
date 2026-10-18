
# sorting_logic.py
# Seven sorting algorithms, performance counters, and complexity metadata.
# Sorts copies of book records and preserves original book data.

from time import perf_counter
from math import isfinite, sqrt


ALGORITHMS = {
    "Insertion Sort": {
        "best": "O(n)", "average": "O(n²)", "worst": "O(n²)",
        "stable": "Yes", "numeric_only": False,
    },
    "Selection Sort": {
        "best": "O(n²)", "average": "O(n²)", "worst": "O(n²)",
        "stable": "No", "numeric_only": False,
    },
    "Merge Sort": {
        "best": "O(n log n)", "average": "O(n log n)",
        "worst": "O(n log n)", "stable": "Yes", "numeric_only": False,
    },
    "Quick Sort": {
        "best": "O(n log n)", "average": "O(n log n)", "worst": "O(n²)",
        "stable": "No", "numeric_only": False,
    },
    "Bubble Sort": {
        "best": "O(n)", "average": "O(n²)", "worst": "O(n²)",
        "stable": "Yes", "numeric_only": False,
    },
    "Counting Sort": {
        "best": "O(n + k)", "average": "O(n + k)", "worst": "O(n + k)",
        "stable": "Yes", "numeric_only": True,
    },
    "Bucket Sort": {
        "best": "O(n + k)", "average": "O(n + k)", "worst": "O(n²)",
        "stable": "Yes*", "numeric_only": True,
    },
}


MISSING_VALUES = {"", "n/a", "na", "none", "null", "nan", "—", "-"}


def is_missing(value):
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip().casefold() in MISSING_VALUES

    return False


def parse_numeric(value):
    """Return a finite float, None for missing data, or raise ValueError."""
    if is_missing(value):
        return None

    try:
        number = float(str(value).strip().replace(",", ""))
    except (ValueError, TypeError, OverflowError):
        raise ValueError(
            "This algorithm only supports numeric values. "
            "The selected column contains text that cannot be sorted "
            "numerically. Choose Insertion, Selection, Merge, Quick, "
            "or Bubble Sort for text columns such as Title or Authors."
        )

    if not isfinite(number):
        raise ValueError(
            "The selected column contains an invalid numeric value. "
            "Please check the data and try again."
        )

    return number


def sort_books(books, column, algorithm, descending=False):
    """
    Returns:
        sorted_books, statistics

    Empty values remain at the end for both sort directions.
    Counting Sort and Bucket Sort support integers and decimal values.
    """
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown sorting algorithm: {algorithm}")

    items = [dict(book) for book in books]
    comparisons = 0
    swaps = 0
    movements = 0

    def value_key(book):
        value = book.get(column, "")

        if is_missing(value):
            return (1, 0, "")

        text = str(value).strip()

        try:
            number = float(text.replace(",", ""))
            if isfinite(number):
                return (0, 0, number)
        except (ValueError, TypeError, OverflowError):
            pass

        return (0, 1, text.casefold())

    keys = [value_key(book) for book in items]

    def before(a, b):
        nonlocal comparisons
        comparisons += 1

        # Missing values stay last, even in descending order.
        if a[0] != b[0]:
            return a[0] < b[0]

        if descending:
            return a > b

        return a < b

    def swap(i, j):
        nonlocal swaps

        if i != j:
            items[i], items[j] = items[j], items[i]
            keys[i], keys[j] = keys[j], keys[i]
            swaps += 1

    start = perf_counter()

    if algorithm == "Insertion Sort":
        for i in range(1, len(items)):
            item, key = items[i], keys[i]
            j = i - 1

            while j >= 0 and before(key, keys[j]):
                items[j + 1] = items[j]
                keys[j + 1] = keys[j]
                movements += 1
                j -= 1

            items[j + 1] = item
            keys[j + 1] = key
            movements += 1

    elif algorithm == "Selection Sort":
        for i in range(len(items)):
            best = i

            for j in range(i + 1, len(items)):
                if before(keys[j], keys[best]):
                    best = j

            if best != i:
                swap(i, best)

    elif algorithm == "Bubble Sort":
        for end in range(len(items) - 1, 0, -1):
            changed = False

            for j in range(end):
                if before(keys[j + 1], keys[j]):
                    swap(j, j + 1)
                    changed = True

            if not changed:
                break

    elif algorithm == "Merge Sort":
        def merge_sort(lo, hi):
            nonlocal movements

            if hi - lo <= 1:
                return

            mid = (lo + hi) // 2
            merge_sort(lo, mid)
            merge_sort(mid, hi)

            left_items = items[lo:mid]
            right_items = items[mid:hi]
            left_keys = keys[lo:mid]
            right_keys = keys[mid:hi]

            i = j = 0
            out = lo

            while i < len(left_items) and j < len(right_items):
                if before(right_keys[j], left_keys[i]):
                    items[out] = right_items[j]
                    keys[out] = right_keys[j]
                    j += 1
                else:
                    items[out] = left_items[i]
                    keys[out] = left_keys[i]
                    i += 1

                out += 1
                movements += 1

            while i < len(left_items):
                items[out] = left_items[i]
                keys[out] = left_keys[i]
                i += 1
                out += 1
                movements += 1

            while j < len(right_items):
                items[out] = right_items[j]
                keys[out] = right_keys[j]
                j += 1
                out += 1
                movements += 1

        merge_sort(0, len(items))

    elif algorithm == "Quick Sort":
        def quick_sort(lo, hi):
            if lo >= hi:
                return

            pivot = keys[hi]
            boundary = lo

            for j in range(lo, hi):
                if before(keys[j], pivot):
                    swap(boundary, j)
                    boundary += 1

            swap(boundary, hi)
            quick_sort(lo, boundary - 1)
            quick_sort(boundary + 1, hi)

        # Inclusive upper bound: prevents IndexError.
        quick_sort(0, len(items) - 1)

    elif algorithm == "Counting Sort":
        # Numeric values are sorted by their ranks among distinct values.
        # This supports floats without allocating a huge integer range.
        numeric_records = []
        missing_records = []

        for book in items:
            number = parse_numeric(book.get(column, ""))
            if number is None:
                missing_records.append(book)
            else:
                numeric_records.append((number, book))

        distinct_values = sorted({number for number, _ in numeric_records})
        counts = {number: 0 for number in distinct_values}

        for number, _ in numeric_records:
            counts[number] += 1

        ordered_values = (
            reversed(distinct_values) if descending else distinct_values
        )

        # Stable placement preserves the order of records with equal values.
        grouped = {}
        for number, book in numeric_records:
            grouped.setdefault(number, []).append(book)

        sorted_records = []
        for number in ordered_values:
            sorted_records.extend(grouped[number])

        items = sorted_records + missing_records
        movements += len(items)

    elif algorithm == "Bucket Sort":
        numeric_records = []
        missing_records = []

        for book in items:
            number = parse_numeric(book.get(column, ""))
            if number is None:
                missing_records.append(book)
            else:
                numeric_records.append((number, book))

        if numeric_records:
            numbers = [number for number, _ in numeric_records]
            low, high = min(numbers), max(numbers)
            bucket_count = max(1, int(sqrt(len(numeric_records))))
            buckets = [[] for _ in range(bucket_count)]

            if low == high:
                buckets[0] = list(numeric_records)
            else:
                for record in numeric_records:
                    number = record[0]
                    index = int(
                        (number - low) / (high - low) * (bucket_count - 1)
                    )
                    index = min(max(index, 0), bucket_count - 1)
                    buckets[index].append(record)

            result = []
            ordered_buckets = reversed(buckets) if descending else buckets

            # Stable insertion sort within each bucket.
            for bucket in ordered_buckets:
                for i in range(1, len(bucket)):
                    current = bucket[i]
                    j = i - 1

                    while j >= 0:
                        comparisons += 1

                        if descending:
                            should_move = current[0] > bucket[j][0]
                        else:
                            should_move = current[0] < bucket[j][0]

                        if not should_move:
                            break

                        bucket[j + 1] = bucket[j]
                        movements += 1
                        j -= 1

                    bucket[j + 1] = current
                    movements += 1

                result.extend(bucket)

            numeric_records = result

        items = [book for _, book in numeric_records] + missing_records
        movements += len(items)

    elapsed_ms = (perf_counter() - start) * 1000

    info = ALGORITHMS[algorithm]
    stats = {
        "algorithm": algorithm,
        "column": column,
        "time_ms": elapsed_ms,
        "comparisons": comparisons,
        "swaps": swaps,
        "movements": movements,
        "best": info["best"],
        "average": info["average"],
        "worst": info["worst"],
        "stable": info["stable"],
    }

    return items, stats


