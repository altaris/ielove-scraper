# pylint: disable=missing-function-docstring
# pylint: disable=unnecessary-lambda
"""Webui"""

from typing import Callable, List

from nicegui import ui
from nicegui.element import Element
import pymongo
from ielove import db

PROPERTY_ICONS = {
    "chintai": "real_estate_agent",
    "kodate_chuko": "house",
    "kodate_shinchiku": "house",
    "mansion_chuko": "apartment",
    "mansion_shinchiku": "apartment",
    "tochi": "explore",
}
"""Icon for each property type"""


def populate_with_property(parent: Element, data: dict) -> None:
    """Populates an element (e.g. a card) with the data of a property"""
    with parent:
        card = ui.card()
    with card:
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
            ui.markdown(data["salespoint"])
            columns = [
                {
                    "label": "Field",
                    "field": "field",
                    "align": "right",
                    "sortable": True,
                },
                {
                    "label": "Value",
                    "field": "value",
                    "align": "left",
                },
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


def search_by_address():
    result_div.clear()
    key = str(search_field.value).strip()
    # TODO: Move query logic to ielove.db ?
    collection = db.get_collection("properties")
    results = collection.find(
        {"details.住所": {"$regex": f".*{key}.*"}},
        sort=[("details.住所", pymongo.ASCENDING)],
        limit=50,
    )
    if not results:
        ui.notify("No results", position="top", type="negative")
        return
    with result_div:
        for data in results:
            expansion = ui.expansion(
                f"【{data['details']['住所']}】　{data['name']}",
                icon=PROPERTY_ICONS.get(data["type"]),
            )
            populate_with_property(expansion, data)


def search_by_id_or_url():
    result_div.clear()
    key = str(search_field.value).strip()
    data = db.get_property(key)
    if data is None:
        ui.notify("No results", position="top", type="negative")
        return
    populate_with_property(result_div, data)


search_field = ui.input("Search").classes("w-full")
with ui.row():
    ui.button(
        "Search by ID or URL",
        icon="search",
        on_click=lambda: search_by_id_or_url(),
    )
    ui.button(
        "Search by address",
        icon="search",
        on_click=lambda: search_by_address(),
    )
    # ui.button(
    #     "Full-text search",
    #     icon="search",
    #     on_click=lambda: search_by_full_text(),
    # )
result_div = ui.element(tag="div")

if __name__ in ["__main__", "__mp_main__"]:
    db.ensure_indices()
    ui.run(
        host="0.0.0.0",
        title="ielove",
        uvicorn_logging_level="info",
    )
