from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from sorting_logic import ALGORITHMS, sort_books


class BenchmarkDialog(QDialog):
    """Modal popup comparing all available sorting algorithms."""

    def __init__(
        self,
        books,
        column,
        column_label,
        descending=False,
        parent=None,
    ):
        super().__init__(parent)

        self.books = books
        self.column = column
        self.column_label = column_label
        self.descending = descending

        self.setWindowTitle("Sorting Algorithm Benchmark")
        self.setMinimumSize(760, 440)
        self.resize(850, 490)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #281326;
                color: #FFF4FA;
            }

            QLabel {
                color: #FFF4FA;
                font-size: 10pt;
            }

            QLabel#heading {
                color: #FFB6D0;
                font-size: 19pt;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #E5C8D9;
                font-size: 10pt;
            }

            QLabel#summary {
                background-color: #43213E;
                color: #FFD5E4;
                border: 1px solid #875078;
                border-radius: 7px;
                padding: 10px;
                font-weight: bold;
            }

            QTableWidget {
                background-color: #FFF7FA;
                alternate-background-color: #F8E5EF;
                color: #38152E;
                gridline-color: #D8A6BF;
                border: 1px solid #A75C83;
                border-radius: 5px;
                selection-background-color: #DDA5C1;
                selection-color: #38152E;
            }

            QTableWidget::item {
                padding: 9px;
            }

            QHeaderView::section {
                background-color: #8D285D;
                color: white;
                padding: 10px 7px;
                border: none;
                font-weight: bold;
            }

            QPushButton {
                background-color: #E9A1C0;
                color: #321328;
                border: none;
                border-radius: 6px;
                padding: 10px 22px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #FFC0D8;
            }
        """)

        self.init_ui()
        self.run_benchmark()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        heading = QLabel("Benchmark Results")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        subtitle = QLabel(
            f"Comparing sorting algorithms for "
            f"'{self.column_label}' using {len(self.books):,} books."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.summary_label = QLabel("Running benchmark...")
        self.summary_label.setObjectName("summary")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Algorithm",
            "Time (ms)",
            "Comparisons",
            "Swaps",
            "Result",
        ])

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout.addWidget(self.table, 1)

        bottom = QHBoxLayout()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        bottom.addStretch()
        bottom.addWidget(self.close_button)

        layout.addLayout(bottom)

    def run_benchmark(self):
        results = []

        for algorithm in ALGORITHMS:
            try:
                # Each algorithm receives the same original dataset.
                _, stats = sort_books(
                    self.books,
                    self.column,
                    algorithm,
                    self.descending,
                )

                results.append({
                    "algorithm": algorithm,
                    "time_ms": stats["time_ms"],
                    "comparisons": stats["comparisons"],
                    "swaps": stats["swaps"],
                    "result": "Completed",
                })

            except (ValueError, TypeError) as error:
                results.append({
                    "algorithm": algorithm,
                    "time_ms": None,
                    "comparisons": None,
                    "swaps": None,
                    "result": "Not supported",
                })

            except Exception as error:
                results.append({
                    "algorithm": algorithm,
                    "time_ms": None,
                    "comparisons": None,
                    "swaps": None,
                    "result": f"Failed: {type(error).__name__}",
                })

        self.populate_table(results)

    def populate_table(self, results):
        self.table.setRowCount(len(results))

        successful = []

        for row, result in enumerate(results):
            algorithm = result["algorithm"]
            time_ms = result["time_ms"]
            comparisons = result["comparisons"]
            swaps = result["swaps"]
            status = result["result"]

            values = [
                algorithm,
                f"{time_ms:.3f}" if time_ms is not None else "—",
                f"{comparisons:,}" if comparisons is not None else "—",
                f"{swaps:,}" if swaps is not None else "—",
                status,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col in (1, 2, 3):
                    item.setTextAlignment(Qt.AlignCenter)

                if col == 4 and status == "Completed":
                    item.setForeground(Qt.darkGreen)
                elif col == 4:
                    item.setForeground(Qt.darkRed)

                self.table.setItem(row, col, item)

            if status == "Completed":
                successful.append(result)

        if successful:
            fastest = min(successful, key=lambda item: item["time_ms"])
            self.summary_label.setText(
                f"Fastest: {fastest['algorithm']} "
                f"({fastest['time_ms']:.3f} ms)  |  "
                f"Algorithms completed: {len(successful)}/{len(results)}"
            )
        else:
            self.summary_label.setText(
                "No algorithms completed successfully. "
                "Check the selected column and dataset."
            )

        self.table.resizeRowsToContents()
