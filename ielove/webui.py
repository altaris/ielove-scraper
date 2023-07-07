# pylint: disable=missing-function-docstring
# pylint: disable=unnecessary-lambda
"""Webui"""

from functools import partial
from typing import Callable, List

from nicegui import ui
from nicegui.element import Element
from ielove.db import get_property

PROPERTY_ICONS = {
    "chintai": "real_estate_agent",
    "kodate_chuko": "house",
    "kodate_shinchiku": "house",
    "mansion_chuko": "apartment",
    "mansion_shinchiku": "apartment",
    "tochi": "explore",
}


def populate_with_property(parent: Element, data: dict) -> None:
    with parent:
        name, url, dt = data["name"], data["url"], data["datetime"]
        ui.markdown(f"# [{name}]({url})")
        ui.markdown(f"_scraped at {str(dt)}_")
        ui.markdown(data["salespoint"])
        ui.aggrid(
            {
                "columnDefs": [
                    {"headerName": "Field", "field": "field"},
                    {"headerName": "Value", "field": "value"},
                ],
                "rowData": [
                    {"field": k, "value": v}
                    for k, v in data["details"].items()
                ],
            }
        )


def populate_result_card(results: List[dict]):
    result_card.clear()
    if not results:
        result_card.set_visibility(False)
        ui.notify("No results", position="top", type="negative")
        return
    result_card.set_visibility(True)
    with result_card:
        with ui.tabs() as tabs:
            for i, data in enumerate(results):
                d = str(data["datetime"].date())
                ui.tab(i, label=d, icon=PROPERTY_ICONS[data["type"]])
        with ui.tab_panels(tabs, value=0):
            for i, data in enumerate(results):
                populate_with_property(ui.tab_panel(i), data)


def on_button_search_clicked():
    key = str(field_url.value).strip()
    results = get_property(key)
    populate_result_card(results)


field_url = ui.input("ID or URL")
button_search = ui.button(
    "Search",
    icon="search",
    on_click=lambda: on_button_search_clicked(),
)
ui.separator()
result_card = ui.card()
result_card.set_visibility(False)

if __name__ in ["__main__", "__mp_main__"]:
    ui.run(
        host="0.0.0.0",
        title="ielove",
        uvicorn_logging_level="info",
    )
