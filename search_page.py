
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
    QLineEdit,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
)

from search_logic import search_books, get_operators


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


class SearchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(None)

        self.setWindowTitle("Book Search")
        self.resize(1250, 760)
        self.setMinimumSize(850, 580)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.books = []
        self.filter_rows = []

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

            QLabel#status {
                color: #7B1748;
                font-weight: bold;
            }

            QComboBox, QLineEdit {
                background: white;
                color: #4B1830;
                border: 1px solid #D96C91;
                border-radius: 5px;
                padding: 7px;
                min-height: 18px;
            }

            QCheckBox {
                color: #7B1748;
                spacing: 5px;
            }

            QPushButton {
                background-color: #7B1748;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 9px 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #A52D63;
            }

            QFrame#filter {
                background: #FFF7FA;
                border: 1px solid #F0B8CC;
                border-radius: 7px;
            }

            QTableWidget {
                background: white;
                alternate-background-color: #FFF5F8;
                color: #4B1830;
                gridline-color: #F0C7D6;
                border: 1px solid #E9B1C6;
                selection-background-color: #F3C4D7;
                selection-color: #4B1830;
            }

            QHeaderView::section {
                background-color: #7B1748;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

        self.init_ui()
        self.load_books()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        heading = QLabel("Search Books")
        heading.setObjectName("heading")
        root.addWidget(heading)

        description = QLabel(
            "Build filters for any column. Combine conditions with AND or OR, "
            "or negate individual conditions using NOT."
        )
        description.setWordWrap(True)
        root.addWidget(description)

        filter_heading = QHBoxLayout()
        filter_heading.addWidget(QLabel("Advanced Filters"))
        filter_heading.addStretch()

        add_button = QPushButton("+ Add Filter")
        add_button.clicked.connect(self.add_filter_row)
        filter_heading.addWidget(add_button)

        root.addLayout(filter_heading)

        self.filters_layout = QVBoxLayout()
        self.filters_layout.setSpacing(7)
        root.addLayout(self.filters_layout)

        actions = QHBoxLayout()

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        actions.addWidget(self.search_button)

        self.clear_button = QPushButton("Clear Filters")
        self.clear_button.clicked.connect(self.clear_filters)
        actions.addWidget(self.clear_button)

        actions.addStretch()
        root.addLayout(actions)

        self.status_label = QLabel("Loading books...")
        self.status_label.setObjectName("status")
        root.addWidget(self.status_label)

        self.table = QTableWidget(0, len(DISPLAY_COLUMNS))
        self.table.setHorizontalHeaderLabels(
            [label for _, label in DISPLAY_COLUMNS]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        root.addWidget(self.table, 1)

        self.add_filter_row()

    def load_books(self):
        if not os.path.exists(CSV_FILE):
            self.books = []
            self.status_label.setText(
                f"CSV not found: {CSV_FILE}. Run the scraper first."
            )
            return

        try:
            with open(
                CSV_FILE,
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                self.books = list(csv.DictReader(file))

            self.display_books(self.books)
            self.status_label.setText(
                f"Loaded {len(self.books):,} books."
            )

        except (OSError, csv.Error) as error:
            QMessageBox.critical(
                self,
                "CSV Error",
                f"Could not load the books CSV:\n{error}",
            )

    def add_filter_row(self):
        frame = QFrame()
        frame.setObjectName("filter")

        row_layout = QHBoxLayout(frame)
        row_layout.setContentsMargins(8, 7, 8, 7)
        row_layout.setSpacing(7)

        join_combo = QComboBox()
        join_combo.addItems(["AND", "OR"])
        join_combo.setToolTip(
            "How this condition combines with the previous condition"
        )
        join_combo.setFixedWidth(75)

        if not self.filter_rows:
            join_combo.setEnabled(False)
            join_combo.setToolTip("The first condition has no join operator")

        column_combo = QComboBox()
        for key, label in DISPLAY_COLUMNS:
            column_combo.addItem(label, key)

        operator_combo = QComboBox()
        value_input = QLineEdit()
        value_input.setPlaceholderText("Enter value...")
        negate_checkbox = QCheckBox("NOT")

        remove_button = QPushButton("Remove")
        remove_button.setFixedWidth(80)

        row_layout.addWidget(join_combo)
        row_layout.addWidget(column_combo, 2)
        row_layout.addWidget(operator_combo, 2)
        row_layout.addWidget(value_input, 3)
        row_layout.addWidget(negate_checkbox)
        row_layout.addWidget(remove_button)

        row_data = {
            "frame": frame,
            "join": join_combo,
            "column": column_combo,
            "operator": operator_combo,
            "value": value_input,
            "negate": negate_checkbox,
        }

        self.filter_rows.append(row_data)
        self.filters_layout.addWidget(frame)

        column_combo.currentIndexChanged.connect(
            lambda _, data=row_data: self.update_operators(data)
        )
        operator_combo.currentTextChanged.connect(
            lambda operator, field=value_input:
                field.setEnabled(operator not in ("Is empty", "Is not empty"))
        )
        remove_button.clicked.connect(
            lambda _, data=row_data: self.remove_filter_row(data)
        )

        self.update_operators(row_data)

    def update_operators(self, row_data):
        column = row_data["column"].currentData()
        previous = row_data["operator"].currentText()
        operators = get_operators(column)

        row_data["operator"].blockSignals(True)
        row_data["operator"].clear()
        row_data["operator"].addItems(operators)

        if previous in operators:
            row_data["operator"].setCurrentText(previous)

        row_data["operator"].blockSignals(False)

        row_data["value"].setEnabled(
            row_data["operator"].currentText()
            not in ("Is empty", "Is not empty")
        )

    def remove_filter_row(self, row_data):
        self.filters_layout.removeWidget(row_data["frame"])
        row_data["frame"].deleteLater()
        self.filter_rows.remove(row_data)

        if self.filter_rows:
            self.filter_rows[0]["join"].setEnabled(False)

        else:
            self.add_filter_row()

    def collect_conditions(self):
        conditions = []

        for row in self.filter_rows:
            operator = row["operator"].currentText()
            value = row["value"].text().strip()

            if operator not in ("Is empty", "Is not empty") and not value:
                continue

            conditions.append({
                "column": row["column"].currentData(),
                "operator": operator,
                "value": value,
                "negate": row["negate"].isChecked(),
                "join": row["join"].currentText(),
            })

        return conditions

    def perform_search(self):
        conditions = self.collect_conditions()

        if not conditions:
            self.display_books(self.books)
            self.status_label.setText(
                f"Showing all {len(self.books):,} books. "
                "Enter a value or choose an empty-value filter."
            )
            return

        try:
            results = search_books(self.books, conditions)
            self.display_books(results)
            self.status_label.setText(
                f"Found {len(results):,} matching books "
                f"out of {len(self.books):,}."
            )

        except (ValueError, TypeError, KeyError) as error:
            QMessageBox.warning(
                self,
                "Search Error",
                f"Could not apply the search filters:\n{error}",
            )

    def clear_filters(self):
        for row in list(self.filter_rows):
            self.filters_layout.removeWidget(row["frame"])
            row["frame"].deleteLater()

        self.filter_rows.clear()
        self.add_filter_row()

        self.display_books(self.books)
        self.status_label.setText(
            f"Filters cleared. Showing {len(self.books):,} books."
        )

    def display_books(self, books):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(books))

        for row_index, book in enumerate(books):
            for col_index, (key, _) in enumerate(DISPLAY_COLUMNS):
                value = str(book.get(key, "") or "")
                item = QTableWidgetItem(value)

                if key in {
                    "rating",
                    "ratings_count",
                    "want_to_read",
                    "first_published",
                    "editions",
                }:
                    item.setTextAlignment(Qt.AlignCenter)

                self.table.setItem(row_index, col_index, item)

        self.table.setUpdatesEnabled(True)
