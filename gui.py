
import sys
import threading
import scrapper
from sorting_page import SortingPage
from search_page import SearchPage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QMessageBox
)




class ScraperWorker(QThread):
    progress = pyqtSignal(int)
    book_found = pyqtSignal(dict)
    status = pyqtSignal(str)

    def __init__(self, start_page, end_page):
        super().__init__()

        self.start_page = start_page
        self.end_page = end_page

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

    def run(self):
        try:
            scrapper.main(
                start_page=self.start_page,
                end_page=self.end_page,
                progress_callback=self.update_progress,
                book_callback=self.book_found.emit,
                status_callback=self.status.emit,
                pause_event=self.pause_event,
                stop_event=self.stop_event,
            )
        except Exception as e:
            self.status.emit(f"Error: {e}")

    def update_progress(self, completed, total, total_books):
        if total > 0:
            self.progress.emit(int(completed / total * 100))

    def pause(self):
        self.pause_event.set()

    def resume(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()


class ScraperGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Open Library Scraper")
        self.resize(1200, 700)

        self.worker = None
        self.sorting_window = None
        self.search_window = None

        self.setStyleSheet("""
            QWidget {
                background-color: #D96C91;
                color: #4A1830;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }

            QLabel {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                padding: 4px;
            }

            QSpinBox {
                background-color: #FFFFFF;
                color: #4A1830;
                border: 2px solid #F5B7CC;
                border-radius: 8px;
                padding: 8px;
                min-width: 75px;
            }

            QPushButton {
                background-color: #7B1748;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: #A52A60;
                border-color: #FFE1EB;
            }

            QPushButton:pressed {
                background-color: #58102F;
            }

            QPushButton:disabled {
                background-color: #E8A2BA;
                color: #754156;
                border-color: #F5D4DF;
            }

            QProgressBar {
                background-color: #FFFFFF;
                color: #4A1830;
                border: 2px solid #7B1748;
                border-radius: 9px;
                height: 24px;
                text-align: center;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background-color: #7B1748;
                border-radius: 6px;
            }

            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #FFF0F5;
                color: #4A1830;
                border: 3px solid #7B1748;
                border-radius: 10px;
                gridline-color: #F0B5C9;
                selection-background-color: #7B1748;
                selection-color: #FFFFFF;
            }

            QHeaderView::section {
                background-color: #7B1748;
                color: #FFFFFF;
                border: 1px solid #9B3564;
                padding: 11px;
                font-weight: bold;
            }

            QTableWidget::item {
                padding: 7px;
            }

            QTableWidget::item:selected {
                background-color: #7B1748;
                color: #FFFFFF;
            }

            QScrollBar:vertical {
                background-color: #FCE5ED;
                width: 12px;
                margin: 2px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #A52A60;
                min-height: 25px;
                border-radius: 6px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        layout = QVBoxLayout(self)
                # Project Branding Header
        branding_layout = QVBoxLayout()
        branding_layout.setSpacing(2)

        self.brand_title = QLabel("Scrap Sort & Search")
        self.brand_title.setAlignment(Qt.AlignCenter)
        self.brand_title.setStyleSheet("""
            QLabel {
                color: #7B1748;
                font-family: 'Georgia';
                font-size: 34px;
                font-weight: bold;
                font-style: italic;
                padding: 8px 0px 0px 0px;
                background-color: transparent;
                letter-spacing: 1px;
            }
        """)

        self.brand_subtitle = QLabel(
            "SCRAPE  •  SORT  •  DISCOVER"
        )
        self.brand_subtitle.setAlignment(Qt.AlignCenter)
        self.brand_subtitle.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Segoe UI';
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 3px;
                padding-bottom: 12px;
                background-color: transparent;
            }
        """)

        branding_layout.addWidget(self.brand_title)
        branding_layout.addWidget(self.brand_subtitle)

        layout.addLayout(branding_layout)

        # Page range and action buttons
        controls = QHBoxLayout()

        controls.addWidget(QLabel("Start page:"))

        self.start_page = QSpinBox()
        self.start_page.setRange(1, 10000)
        self.start_page.setValue(scrapper.START_PAGE)
        controls.addWidget(self.start_page)

        controls.addWidget(QLabel("End page:"))

        self.end_page = QSpinBox()
        self.end_page.setRange(1, 10000)
        self.end_page.setValue(scrapper.END_PAGE)
        controls.addWidget(self.end_page)

        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        controls.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_scraping)
        controls.addWidget(self.pause_button)

        self.resume_button = QPushButton("Resume")
        self.resume_button.setEnabled(False)
        self.resume_button.clicked.connect(self.resume_scraping)
        controls.addWidget(self.resume_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_scraping)
        controls.addWidget(self.stop_button)

        # Sorting navigation button
        self.sorting_button = QPushButton("Sorting")
        self.sorting_button.clicked.connect(self.open_sorting_page)
        controls.addWidget(self.sorting_button)
        # Search navigation button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.open_search_page)
        controls.addWidget(self.search_button)

        layout.addLayout(controls)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Live scraped books table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Title",
            "Authors",
            "Rating",
            "Ratings Count",
            "Want to Read",
            "First Published",
            "Editions",
            "Availability",
        ])

        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        self.table.setWordWrap(False)

        layout.addWidget(self.table)
    def open_search_page(self):
        if self.search_window is None:
            self.search_window = SearchPage()

        self.search_window.load_books()
        self.search_window.show()
        self.search_window.showMaximized()
        self.search_window.raise_()
        self.search_window.activateWindow()
    def open_sorting_page(self):
        # Keep the window reference so it remains available.
        if self.sorting_window is None:
            self.sorting_window = SortingPage()

        self.sorting_window.load_books()
        self.sorting_window.show()
        self.sorting_window.showMaximized()
        self.sorting_window.raise_()
        self.sorting_window.activateWindow()

    def start_scraping(self):
        start = self.start_page.value()
        end = self.end_page.value()

        if end < start:
            QMessageBox.warning(
                self,
                "Invalid range",
                "End page must be greater than or equal to start page."
            )
            return

        if self.worker is not None and self.worker.isRunning():
            return

        self.table.setRowCount(0)
        self.progress_bar.setValue(0)

        self.start_button.setEnabled(False)
        self.start_page.setEnabled(False)
        self.end_page.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.worker = ScraperWorker(start, end)

        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.book_found.connect(self.add_book)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.scraping_finished)

        self.status_label.setText("Starting scraper...")
        self.worker.start()

    def pause_scraping(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.pause()

            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(True)

            self.status_label.setText(
                "Pause requested — finishing current page..."
            )

    def resume_scraping(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.resume()

            self.pause_button.setEnabled(True)
            self.resume_button.setEnabled(False)

            self.status_label.setText("Resuming scraping...")

    def stop_scraping(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()

            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(False)
            self.stop_button.setEnabled(False)

            self.status_label.setText(
                "Stopping — the current page may finish first..."
            )

    def scraping_finished(self):
        self.start_button.setEnabled(True)
        self.start_page.setEnabled(True)
        self.end_page.setEnabled(True)

        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)

    def add_book(self, book):
        row = self.table.rowCount()
        self.table.insertRow(row)

        values = [
            book.get("title", ""),
            book.get("authors", ""),
            book.get("rating", ""),
            book.get("ratings_count", ""),
            book.get("want_to_read", ""),
            book.get("first_published", ""),
            book.get("editions", ""),
            book.get("availability", ""),
        ]

        for column, value in enumerate(values):
            self.table.setItem(
                row,
                column,
                QTableWidgetItem(str(value))
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = ScraperGUI()
    window.show()

    sys.exit(app.exec_())
