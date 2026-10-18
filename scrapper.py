
import csv
import re
import os
import time
from playwright.sync_api import sync_playwright

URL = (
    "https://openlibrary.org/search?q=trending_score_hourly_sum%3A%5B1+TO+%2A%5D"
    "+AND+readinglog_count%3A%5B4+TO+%2A%5D+language%3Aeng"
    "&has_fulltext=true&sort=trending"
)

# Configure the default page range (inclusive)
START_PAGE = 160
END_PAGE = 600

# Timeouts
NAVIGATION_TIMEOUT = 120000
SELECTOR_TIMEOUT = 60000

CSV_FILE = "openlibrary_books.csv"


def get_text(parent, selector):
    el = parent.query_selector(selector)
    return el.inner_text().strip() if el else ""


def get_attr(parent, selector, attr):
    el = parent.query_selector(selector)
    if el:
        value = el.get_attribute(attr)
        return value.strip() if value else ""
    return ""


def make_full_url(link):
    if not link:
        return ""
    if link.startswith("//"):
        return "https:" + link
    if link.startswith("/"):
        return "https://openlibrary.org" + link
    return link


def scrape_book(item):
    book = {}

    book["title"] = get_text(item, "h3.booktitle a")
    book["book_url"] = make_full_url(
        get_attr(item, "h3.booktitle a", "href")
    )

    authors = [
        a.inner_text().strip()
        for a in item.query_selector_all("span.bookauthor a")
        if a.inner_text().strip()
    ]
    book["authors"] = ", ".join(authors)

    book["series"] = get_text(item, ".bookseries a")
    book["series_position"] = get_text(
        item, ".bookseries__position"
    )

    book["rating"] = get_attr(
        item, "meta[itemprop='ratingValue']", "content"
    )
    book["ratings_count"] = get_attr(
        item, "meta[itemprop='ratingCount']", "content"
    )

    book["want_to_read"] = ""
    for el in item.query_selector_all("span.ratingsByline"):
        text = el.inner_text().strip()
        if "Want to read" in text:
            match = re.search(r"([\d,]+)", text)
            if match:
                book["want_to_read"] = match.group(1).replace(",", "")
                break

    details = get_text(item, ".resultDetails")

    year = re.search(r"First published in (\d{3,4})", details)
    editions = re.search(r"(\d+)\s+editions?", details)
    ebooks = re.search(r"(\d+)\s+ebooks?", details)

    book["first_published"] = year.group(1) if year else ""
    book["editions"] = editions.group(1) if editions else ""
    book["ebooks"] = ebooks.group(1) if ebooks else ""

    book["availability"] = get_text(
        item,
        ".searchResultItemCTA-lending a, "
        ".searchResultItemCTA-lending .cta-btn"
    )

    book["cover_url"] = make_full_url(
        get_attr(item, "img[itemprop='image']", "src")
    )

    return book


def scrape_page(page):
    page.wait_for_selector(
        "li.searchResultItem",
        timeout=SELECTOR_TIMEOUT
    )

    # Trigger lazy-loaded cover images.
    page.mouse.wheel(0, 10000)
    page.wait_for_timeout(1500)

    items = page.query_selector_all("li.searchResultItem")
    return [scrape_book(item) for item in items]


def main(
    start_page=None,
    end_page=None,
    progress_callback=None,
    book_callback=None,
    status_callback=None,
    pause_event=None,
    stop_event=None,
):
    start_page = start_page if start_page is not None else START_PAGE
    end_page = end_page if end_page is not None else END_PAGE

    if start_page < 1 or end_page < start_page:
        raise ValueError(
            "START_PAGE must be >= 1 and END_PAGE must be >= START_PAGE."
        )

    fieldnames = [
        "title",
        "book_url",
        "authors",
        "series",
        "series_position",
        "rating",
        "ratings_count",
        "want_to_read",
        "first_published",
        "editions",
        "ebooks",
        "availability",
        "cover_url",
    ]

    total_books = 0
    total_pages = end_page - start_page + 1

    file_exists = (
        os.path.exists(CSV_FILE)
        and os.path.getsize(CSV_FILE) > 0
    )

    with open(
        CSV_FILE,
        "a" if file_exists else "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()
            f.flush()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
            page.set_default_timeout(SELECTOR_TIMEOUT)

            try:
                for page_number in range(start_page, end_page + 1):

                    # Stop immediately between pages.
                    if stop_event and stop_event.is_set():
                        break

                    # Pause between pages until Resume is clicked.
                    while pause_event and pause_event.is_set():
                        if stop_event and stop_event.is_set():
                            break

                        if status_callback:
                            status_callback(
                                "Paused — waiting to resume..."
                            )

                        time.sleep(0.2)

                    if stop_event and stop_event.is_set():
                        break

                    if status_callback:
                        status_callback(
                            f"Scraping page {page_number}..."
                        )

                    try:
                        page_url = (
                            URL if page_number == 1
                            else URL + "&page=" + str(page_number)
                        )

                        page.goto(
                            page_url,
                            wait_until="domcontentloaded",
                            timeout=NAVIGATION_TIMEOUT,
                        )

                        books = scrape_page(page)

                        if not books:
                            if status_callback:
                                status_callback(
                                    "No books found. Stopping."
                                )
                            break

                        # Save each completed page immediately.
                        writer.writerows(books)
                        f.flush()

                        total_books += len(books)

                        # Send each scraped book to the GUI.
                        if book_callback:
                            for book in books:
                                book_callback(book)

                        completed = page_number - start_page + 1

                        if progress_callback:
                            progress_callback(
                                completed,
                                total_pages,
                                total_books,
                            )

                        if status_callback:
                            status_callback(
                                f"Page {page_number}: saved "
                                f"{len(books)} books. "
                                f"Total this run: {total_books}"
                            )

                    except Exception as e:
                        if status_callback:
                            status_callback(
                                f"Stopped at page {page_number}: {e}"
                            )
                        break

            finally:
                browser.close()

    # Report whether the run was stopped or completed.
    if stop_event and stop_event.is_set():
        message = (
            f"Stopped. Saved {total_books} books during this run "
            f"to {CSV_FILE}."
        )
    else:
        message = (
            f"Finished. Saved {total_books} books during this run "
            f"to {CSV_FILE}."
        )

    if status_callback:
        status_callback(message)


if __name__ == "__main__":
    main()
