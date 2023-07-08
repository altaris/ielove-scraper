# pylint: disable=missing-function-docstring
# pylint: disable=unnecessary-lambda
"""Webui"""

from typing import List

import pymongo
from nicegui import ui

from ielove import db, ielove, tasks

PROPERTY_ICONS = {
    "chintai": "real_estate_agent",
    "kodate_chuko": "house",
    "kodate_shinchiku": "house",
    "mansion_chuko": "apartment",
    "mansion_shinchiku": "apartment",
    "tochi": "explore",
}
"""Icon for each property type"""


def populate_with_properties(results: List[dict]):
    """
    Populates an element (e.g. a div) with the data for multiple properties
    """
    for data in results:
        expansion = ui.expansion(
            f"【{data['details']['住所']}】　{data['name']}",
            icon=PROPERTY_ICONS.get(data["type"]),
        ).classes("w-full")
        with expansion:
            populate_with_property(data)
    if len(results) == 1:
        expansion.set_value(True)


def populate_with_property(data: dict) -> None:
    """Populates an element (e.g. a div) with the data of a property"""
    with ui.card():
        ui.markdown(f"# [{data['name']}]({data['url']})")
        splitter = ui.splitter().classes("w-full")
        with splitter.before:
            maps_url = "https://www.google.com/maps?q=" + data["details"]["住所"]
            ui.markdown(f"[{data['details']['住所']}]({maps_url})")
            if data["type"] == "chintai":
                ui.markdown(f"Rent: __{data['details']['賃料']}__")
            else:
                ui.markdown(f"Price: __{data['details']['価格']}__")
            ui.markdown(f"_scraped at {str(data['datetime'])}_")
            if "salespoint" in data:
                ui.markdown(data["salespoint"])
            columns = [
                {"label": "Field", "field": "field", "align": "right"},
                {"label": "Value", "field": "value", "align": "left"},
            ]
            rows = [
                {"field": k, "value": str(v)}
                for k, v in data["details"].items()
            ]
            props = "hide-header; wrap-cells"
            ui.table(columns=columns, rows=rows).props(props)
        with splitter.after:
            ui.image(
                "data:image/png;base64,"
                + str(data["floor_plan"]["img"].decode("utf-8"))
            )


def s_search_by_address():
    result_div.clear()
    key = str(le_search_field.value).strip()
    # TODO: Move query logic to ielove.db ?
    collection = db.get_collection("properties")
    results = collection.find(
        {"details.住所": {"$regex": f".*{key}.*"}},
        sort=[("details.住所", pymongo.ASCENDING)],
        limit=50,
    )
    results = list(results)
    if not results:
        ui.notify("No results", position="top", type="negative")
        return
    with result_div:
        populate_with_properties(results)


def s_search_by_id_or_url():
    result_div.clear()
    key = str(le_search_field.value).strip()
    data = db.get_property(key)
    if data is None:
        ui.notify("No results", position="top", type="negative")
        return
    with result_div:
        populate_with_properties([data])


def s_scrape_region():
    r = le_region.value
    t = le_property_type.value
    l = int(n_limit.value)
    if r is None or t is None:
        ui.notify(
            "Select a region and a property type",
            position="top",
            type="negative",
        )
        return
    tasks.scrape_region.delay(r, t, l)
    ui.notify("Submitted task", position="top", type="positive")


def s_scrape_result_page():
    u = le_result_page_url.value
    if not u:
        ui.notify(
            "Input a result page URL",
            position="top",
            type="negative",
        )
        return
    tasks.scrape_result_page.delay(u)
    ui.notify("Submitted task", position="top", type="positive")


def s_scrape_property_page():
    u = le_property_page_url.value
    if not u:
        ui.notify(
            "Input a property page URL",
            position="top",
            type="negative",
        )
        return
    tasks.scrape_property_page.delay(u)
    ui.notify("Submitted task", position="top", type="positive")


with ui.tabs().classes("w-full") as tabs:
    tab_search = ui.tab("Search", icon="search")
    tab_jobs = ui.tab("Tasks", icon="add_task")

with ui.tab_panels(tabs, value=tab_search).classes("w-full"):
    with ui.tab_panel(tab_search):
        with ui.column():
            with ui.row():
                le_search_field = ui.input("Search")
                ui.button(
                    "Search by ID or URL",
                    icon="search",
                    on_click=lambda: s_search_by_id_or_url(),
                )
                ui.button(
                    "Search by address",
                    icon="search",
                    on_click=lambda: s_search_by_address(),
                )
            result_div = ui.element(tag="div")

    with ui.tab_panel(tab_jobs):
        with ui.column():
            with ui.expansion("Scrape property page").classes("w-full"):
                with ui.card():
                    with ui.row().classes("w-full"):
                        le_property_page_url = ui.input(
                            "Property page URL"
                        ).classes("w-1/2")
                        ui.button(
                            "Submit task",
                            icon="add_task",
                            on_click=lambda: s_scrape_property_page(),
                        )
            with ui.expansion("Scrape result page").classes("w-full"):
                with ui.card():
                    with ui.row().classes("w-full"):
                        le_result_page_url = ui.input(
                            "Result page URL"
                        ).classes("w-1/2")
                        ui.button(
                            "Submit task",
                            icon="add_task",
                            on_click=lambda: s_scrape_result_page(),
                        )
            with ui.expansion("Scrape region").classes("w-full"):
                with ui.card():
                    with ui.row().classes("w-full"):
                        le_region = ui.select(
                            ielove.ALL_REGIONS, label="Region"
                        ).classes("w-1/4")
                        le_property_type = ui.select(
                            ielove.ALL_PROPERTY_TYPES, label="Property type"
                        ).classes("w-1/4")
                        n_limit = ui.number(
                            label="limit", value=100, min=1, max=1000, step=1
                        )
                        ui.button(
                            "Submit task",
                            icon="add_task",
                            on_click=lambda: s_scrape_region(),
                        )


if __name__ in ["__main__", "__mp_main__"]:
    db.ensure_indices()
    ui.run(
        host="0.0.0.0",
        title="ielove",
        uvicorn_logging_level="info",
    )
