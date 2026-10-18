from benchmark_page import BenchmarkDialog
import csv
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QGridLayout,
    QSizePolicy,
)

from sorting_logic import ALGORITHMS, sort_books


CSV_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "openlibrary_books.csv",
)

DISPLAY_COLUMNS = [
    ("title", "Title"),
    ("authors", "Authors"),
    ("rating", "Rating"),
    ("ratings_count", "Ratings Count"),
    ("want_to_read", "Want to Read"),
    ("first_published", "First Published"),
    ("editions", "Editions"),
    ("availability", "Availability"),
]

COLUMN_WIDTHS = [280, 180, 85, 110, 120, 110, 90, 150]


class SortingPage(QWidget):
    def __init__(self, parent=None):
        # Create an independent window rather than embedding it in the scraper.
        super().__init__(None)

        self.setWindowTitle("Book Sorting Algorithms")
        self.resize(1250, 760)
        self.setMinimumSize(800, 550)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.books = []
        self.init_ui()
        self.load_books()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #FCECF2;
                color: #4B1830;
                font-size: 10pt;
            }

            QLabel#heading {
                font-size: 19pt;
                font-weight: bold;
                color: #7B1748;
            }

            QComboBox {
                background: white;
                border: 1px solid #D96C91;
                border-radius: 5px;
                padding: 7px;
                min-width: 120px;
            }

            QPushButton {
                background-color: #7B1748;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 9px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #A52D63;
            }

            QPushButton:disabled {
                background-color: #C9A0B1;
            }

            QFrame#metric {
                background: white;
                border: 1px solid #F0B8CC;
                border-radius: 8px;
            }

            QLabel#metricValue {
                font-size: 15pt;
                font-weight: bold;
                color: #7B1748;
            }

            QTableWidget {
                background: white;
                alternate-background-color: #FFF5F8;
                gridline-color: #F0C7D6;
                border: 1px solid #E9B1C6;
                selection-background-color: #F3C4D7;
                selection-color: #4B1830;
            }

            QHeaderView::section {
                background-color: #7B1748;
                color: white;
                padding: 7px;
                font-weight: bold;
                border: none;
            }
        """)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        heading = QLabel("Sorting Laboratory")
        heading.setObjectName("heading")
        root.addWidget(heading)

        description = QLabel(
            "Choose a book column and sorting algorithm to compare performance."
        )
        description.setWordWrap(True)
        root.addWidget(description)

        # Sorting controls
        controls = QHBoxLayout()
        controls.setSpacing(8)

        controls.addWidget(QLabel("Column:"))

        self.column_combo = QComboBox()
        for key, label in DISPLAY_COLUMNS:
            self.column_combo.addItem(label, key)
        controls.addWidget(self.column_combo)

        controls.addWidget(QLabel("Algorithm:"))

        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(list(ALGORITHMS.keys()))
        controls.addWidget(self.algorithm_combo)

        controls.addWidget(QLabel("Order:"))

        self.order_combo = QComboBox()
        self.order_combo.addItems(["Ascending", "Descending"])
        controls.addWidget(self.order_combo)

        self.sort_button = QPushButton("Sort Books")
        self.sort_button.clicked.connect(self.perform_sort)
        controls.addWidget(self.sort_button)

        self.benchmark_button = QPushButton("Benchmark")
        self.benchmark_button.setToolTip(
            "Compare all sorting algorithms on the selected column"
        )
        self.benchmark_button.clicked.connect(self.open_benchmark)
        controls.addWidget(self.benchmark_button)

        self.reload_button = QPushButton("Reload CSV")
        self.reload_button.clicked.connect(self.load_books)
        controls.addWidget(self.reload_button)

        root.addLayout(controls)

        self.algorithm_info = QLabel()
        self.algorithm_info.setWordWrap(True)
        root.addWidget(self.algorithm_info)

        self.algorithm_combo.currentTextChanged.connect(
            self.update_algorithm_info
        )
        self.update_algorithm_info()

        # Performance metric cards
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(8)

        self.metric_labels = {}

        metric_names = [
            ("time_ms", "Execution Time", "—"),
            ("comparisons", "Comparisons", "—"),
            ("swaps", "Swaps", "—"),
            ("movements", "Movements", "—"),
            ("rows", "Books Loaded", "0"),
        ]

        for index, (key, title, initial) in enumerate(metric_names):
            card = QFrame()
            card.setObjectName("metric")
            card.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Preferred,
            )

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)

            title_label = QLabel(title)
            title_label.setWordWrap(True)

            value_label = QLabel(initial)
            value_label.setObjectName("metricValue")
            value_label.setWordWrap(True)

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            metrics_layout.addWidget(card, 0, index)

            self.metric_labels[key] = value_label

        root.addLayout(metrics_layout)

        self.status_label = QLabel("Loading books...")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        # Books table
        self.table = QTableWidget()
        self.table.setColumnCount(len(DISPLAY_COLUMNS))
        self.table.setHorizontalHeaderLabels(
            [label for _, label in DISPLAY_COLUMNS]
        )

        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideRight)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)

        for index, width in enumerate(COLUMN_WIDTHS):
            self.table.setColumnWidth(index, width)

        # Allow row heights to fit wrapped text.
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        root.addWidget(self.table, 1)

    def update_algorithm_info(self, *_):
        name = self.algorithm_combo.currentText()
        info = ALGORITHMS.get(name)

        if not info:
            self.algorithm_info.setText("")
            return

        extra_info = ""

        if name == "Counting Sort":
            extra_info = " | Requires integer numeric values"
        elif name == "Bucket Sort":
            extra_info = " | Numeric columns only"

        self.algorithm_info.setText(
            f"<b>{name}</b> | "
            f"Best: {info['best']} | "
            f"Average: {info['average']} | "
            f"Worst: {info['worst']} | "
            f"Stable: {info['stable']}"
            f"{extra_info}"
        )

    def load_books(self):
        if not os.path.exists(CSV_FILE):
            self.books = []
            self.table.setRowCount(0)
            self.status_label.setText(
                f"CSV not found: {CSV_FILE}. Run the scraper first."
            )
            self.metric_labels["rows"].setText("0")
            return

        try:
            with open(
                CSV_FILE,
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                reader = csv.DictReader(file)
                self.books = list(reader)

            self.display_books(self.books)

            self.status_label.setText(
                f"Loaded {len(self.books):,} books from CSV."
            )
            self.metric_labels["rows"].setText(
                f"{len(self.books):,}"
            )

        except (OSError, csv.Error) as error:
            QMessageBox.critical(
                self,
                "CSV Error",
                f"Could not read the CSV:\n{error}",
            )

    def perform_sort(self):
        if not self.books:
            QMessageBox.warning(
                self,
                "No Books",
                "Scrape some books or load a CSV first.",
            )
            return

        column = self.column_combo.currentData()
        algorithm = self.algorithm_combo.currentText()
        descending = (
            self.order_combo.currentText() == "Descending"
        )

        self.sort_button.setEnabled(False)
        self.status_label.setText(
            f"Sorting by {column} using {algorithm}..."
        )

        try:
            print(
                f"Sorting started: algorithm={algorithm}, "
                f"column={column}, records={len(self.books)}",
                flush=True,
            )

            sorted_books, stats = sort_books(
                self.books,
                column,
                algorithm,
                descending,
            )

            print("Sorting function returned successfully.", flush=True)

            self.display_books(sorted_books)

            self.metric_labels["time_ms"].setText(
                f"{stats['time_ms']:.3f} ms"
            )
            self.metric_labels["comparisons"].setText(
                f"{stats['comparisons']:,}"
            )
            self.metric_labels["swaps"].setText(
                f"{stats['swaps']:,}"
            )
            self.metric_labels["movements"].setText(
                f"{stats['movements']:,}"
            )
            self.metric_labels["rows"].setText(
                f"{len(sorted_books):,}"
            )

            self.status_label.setText(
                f"Sorted {len(sorted_books):,} books by "
                f"'{self.column_combo.currentText()}' "
                f"using {algorithm}."
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Cannot Sort Column",
                str(error),
            )
            self.status_label.setText(
                "Sorting could not be completed."
            )

        except Exception as error:
            import traceback
            traceback.print_exc()

            QMessageBox.critical(
                self,
                "Sorting Error",
                f"Unexpected error:\n{error}",
            )
            self.status_label.setText(
                "An error occurred during sorting."
            )

        finally:
            self.sort_button.setEnabled(True)
    def open_benchmark(self):
        if not self.books:
            QMessageBox.warning(
                self,
                "No Books",
                "Load or scrape some books before running a benchmark.",
            )
            return

        column = self.column_combo.currentData()
        column_label = self.column_combo.currentText()
        descending = self.order_combo.currentText() == "Descending"

        dialog = BenchmarkDialog(
            books=self.books,
            column=column,
            column_label=column_label,
            descending=descending,  
            parent=self,
        )

        dialog.exec_()
    def display_books(self, books):
        print("Display started:", len(books), flush=True)

        self.table.setRowCount(0)
        self.table.setRowCount(len(books))

        print("Rows allocated", flush=True)

        for row_index, book in enumerate(books):
            for col_index, (key, _) in enumerate(DISPLAY_COLUMNS):
                value = book.get(key, "")
                self.table.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem("" if value is None else str(value))
                )

        print("Display finished", flush=True)
