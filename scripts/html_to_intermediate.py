#!/usr/bin/env python3
"""
Parse the Scribe-generated EasyTrans API HTML documentation
into a structured intermediate JSON file.

Usage:
    python scripts/html_to_intermediate.py
"""

import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, Tag

HTML_FILE = Path("EasyTrans Documentation/easytrans rest api.html")
OUTPUT_FILE = Path("EasyTrans Documentation/api_intermediate.json")


def get_text_clean(element) -> str:
    """Extract and clean inner text from a BS4 element."""
    if element is None:
        return ""
    text = element.get_text(separator=" ", strip=True)
    # Collapse multiple whitespace
    return re.sub(r"\s+", " ", text).strip()


def get_inner_html_clean(element) -> str:
    """Extract inner HTML as clean text, stripping tags."""
    if element is None:
        return ""
    return get_text_clean(element)


def parse_param_block(block: Tag) -> dict:
    """
    Parse a single parameter block (div.sl-flex.sl-relative.sl-max-w-full).
    Returns a dict with name, type, required, description, example.
    """
    param = {
        "name": "",
        "type": "",
        "required": False,
        "description": "",
        "example": None,
    }

    # Name — in sl-font-mono sl-font-semibold sl-mr-2
    name_div = block.find("div", class_=lambda c: c and "sl-font-mono" in c and "sl-font-semibold" in c and "sl-mr-2" in c)
    if name_div:
        param["name"] = name_div.get_text(strip=True)

    # Type — in span.sl-truncate.sl-text-muted
    type_span = block.find("span", class_=lambda c: c and "sl-truncate" in c and "sl-text-muted" in c)
    if type_span:
        param["type"] = type_span.get_text(strip=True)

    # Required — span with text "required"
    req_span = block.find("span", class_=lambda c: c and "sl-text-warning" in c)
    if req_span and "required" in req_span.get_text(strip=True).lower():
        param["required"] = True

    # Description — in div.sl-prose.sl-markdown-viewer
    desc_div = block.find("div", class_=lambda c: c and "sl-prose" in c and "sl-markdown-viewer" in c)
    if desc_div:
        param["description"] = get_text_clean(desc_div)

    # Example value — in div.sl-bg-canvas-tint
    example_div = block.find("div", class_=lambda c: c and "sl-bg-canvas-tint" in c)
    if example_div:
        param["example"] = example_div.get_text(strip=True)

    return param


def parse_param_section(section_div: Tag) -> list[dict]:
    """
    Within a parameter section (Headers/URL Parameters/Query Parameters/Body Parameters/Response Fields),
    find all parameter blocks and parse each one.
    """
    params = []
    # Each parameter is inside a div.sl-flex.sl-relative or similar structure
    # The outer wrapper is often div.sl-text-sm containing the actual param rows
    text_sm_divs = section_div.find_all("div", class_=lambda c: c and "sl-text-sm" in c, recursive=False)

    for container in text_sm_divs:
        # Find all top-level sl-flex sl-relative sl-max-w-full blocks
        param_blocks = container.find_all(
            "div",
            class_=lambda c: c and "sl-flex" in c and "sl-relative" in c and "sl-max-w-full" in c and "sl-py-2" in c,
            recursive=False,
        )
        # If not found at top level, search one level deeper (expandable wrappers)
        if not param_blocks:
            expandables = container.find_all("div", class_=lambda c: c and "expandable" in c, recursive=False)
            for exp in expandables:
                pb = exp.find(
                    "div",
                    class_=lambda c: c and "sl-flex" in c and "sl-relative" in c and "sl-max-w-full" in c and "sl-py-2" in c,
                )
                if pb:
                    param_blocks.append(pb)

        for block in param_blocks:
            p = parse_param_block(block)
            if p["name"]:
                params.append(p)

    # Also handle response field expandable wrappers at the same level
    if not params:
        expandables = section_div.find_all("div", class_=lambda c: c and "expandable" in c)
        for exp in expandables:
            pb = exp.find(
                "div",
                class_=lambda c: c and "sl-flex" in c and "sl-relative" in c and "sl-max-w-full" in c and "sl-py-2" in c,
            )
            if pb:
                p = parse_param_block(pb)
                if p["name"]:
                    params.append(p)

    return params


def parse_json_example(code_elem: Tag) -> dict | list | None:
    """Extract and parse JSON from a <code class='language-json'> element."""
    raw = code_elem.get_text()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def parse_operation(op_div: Tag, current_tag: str) -> dict:
    """
    Parse a single HttpOperation div into a structured dict.
    """
    operation = {
        "tag": current_tag,
        "summary": "",
        "method": "",
        "path": "",
        "description": "",
        "auth_required": False,
        "headers": [],
        "url_parameters": [],
        "query_parameters": [],
        "body_parameters": [],
        "response_fields": [],
        "response_examples": [],
    }

    # ----- Summary (h2 title) -----
    h2 = op_div.find("h2")
    if h2:
        operation["summary"] = h2.get_text(strip=True)

    # ----- Method & Path -----
    # Method div has style="background-color: green;" or darkblue etc.
    method_div = op_div.find(
        "div",
        class_=lambda c: c and "sl-text-lg" in c and "sl-font-semibold" in c and "sl-px-2.5" in c,
    )
    if method_div:
        operation["method"] = method_div.get_text(strip=True).upper()

    # Path is in the flex-1 font-semibold sibling
    path_div = op_div.find("div", class_=lambda c: c and "sl-flex-1" in c and "sl-font-semibold" in c)
    if path_div:
        operation["path"] = path_div.get_text(strip=True)

    # Auth required
    auth_badge = op_div.find(
        "div",
        class_=lambda c: c and "sl-font-prose" in c and "sl-font-semibold" in c and "sl-px-1.5" in c,
    )
    if auth_badge and "requires authentication" in auth_badge.get_text(strip=True).lower():
        operation["auth_required"] = True

    # ----- Description paragraph(s) -----
    # These are <p> tags directly inside the first sl-stack--5 div (before the two-column layout)
    top_section = op_div.find("div", class_=lambda c: c and "sl-stack--5" in c)
    if top_section:
        desc_parts = []
        for p in top_section.find_all("p", recursive=False):
            desc_parts.append(get_text_clean(p))
        if not desc_parts:
            # Try at the op_div level
            for p in op_div.find_all("p", limit=5):
                txt = get_text_clean(p)
                if txt and txt not in desc_parts:
                    desc_parts.append(txt)
                    break
        operation["description"] = " ".join(desc_parts)

    # ----- Left column: parameters & response fields -----
    left_col = op_div.find("div", attrs={"data-testid": "two-column-left"})
    if left_col:
        # Find all h3 sections
        for h3 in left_col.find_all("h3"):
            section_title = h3.get_text(strip=True).lower()
            # The parameter content follows in the sibling div
            section_container = h3.find_parent(
                "div", class_=lambda c: c and "sl-stack--6" in c
            ) or h3.find_parent(
                "div", class_=lambda c: c and "sl-stack--5" in c
            )
            if not section_container:
                continue

            params = parse_param_section(section_container)

            if "headers" in section_title:
                operation["headers"] = params
            elif "url parameters" in section_title or "url param" in section_title:
                operation["url_parameters"] = params
            elif "query parameters" in section_title or "query param" in section_title:
                operation["query_parameters"] = params
            elif "body parameters" in section_title or "body param" in section_title:
                operation["body_parameters"] = params
            elif "response fields" in section_title or "response field" in section_title:
                operation["response_fields"] = params

    # ----- Right column: response examples -----
    right_col = op_div.find("div", attrs={"data-testid": "two-column-right"})
    if right_col:
        for code_elem in right_col.find_all("code", class_=lambda c: c and "language-json" in c):
            parsed = parse_json_example(code_elem)
            if parsed is not None:
                # Try to find the associated HTTP status from the select option
                status = "200"
                panel = code_elem.find_parent("div", class_=lambda c: c and "sl-panel" in c)
                if panel:
                    select = panel.find("select")
                    if select:
                        opt = select.find("option", selected=True) or select.find("option")
                        if opt:
                            status = opt.get_text(strip=True)
                operation["response_examples"].append({"status": int(status) if status.isdigit() else status, "body": parsed})

    return operation


def parse_html(html_path: Path) -> dict:
    """
    Top-level parser. Returns a dict with:
      - info: API metadata
      - endpoints: list of parsed operations
    """
    print(f"Reading {html_path} …")
    with open(html_path, "r", encoding="utf-8") as fh:
        soup = BeautifulSoup(fh, "lxml")

    result = {
        "info": {
            "title": "EasyTrans Documentation",
            "description": "",
            "base_url": "https://www.mytrans.nl/demo/api",
            "version": "v1",
        },
        "endpoints": [],
    }

    # Extract base URL
    aside = soup.find("aside")
    if aside:
        code = aside.find("code")
        if code:
            result["info"]["base_url"] = code.get_text(strip=True)

    # Extract intro description
    intro_section = soup.find("div", class_=lambda c: c and "sl-prose" in c and "sl-markdown-viewer" in c)
    if intro_section:
        intro_h1 = intro_section.find("h1", id="introduction")
        if intro_h1:
            # Get the next sibling paragraphs
            desc_parts = []
            for sib in intro_h1.find_next_siblings():
                if sib.name == "h1":
                    break
                if sib.name in ("p", "aside"):
                    desc_parts.append(get_text_clean(sib))
            result["info"]["description"] = " ".join(desc_parts)

    # Walk through the main content, tracking the current section tag (h1 headings)
    main_content = soup.find("div", class_=lambda c: c and "sl-overflow-y-auto" in c and "sl-flex-1" in c)
    if not main_content:
        # Fallback: entire body
        main_content = soup.body

    current_tag = "General"
    for elem in main_content.descendants:
        if not isinstance(elem, Tag):
            continue

        # Track h1 section headings (the resource groups)
        if elem.name == "h1" and elem.get("id") and elem.get("id") not in ("introduction", "authenticating-requests"):
            current_tag = elem.get_text(strip=True)

        # HttpOperation divs
        if "HttpOperation" in (elem.get("class") or []):
            op = parse_operation(elem, current_tag)
            if op["method"] and op["path"]:
                result["endpoints"].append(op)

    print(f"  Found {len(result['endpoints'])} endpoints.")
    return result


def main():
    if not HTML_FILE.exists():
        print(f"ERROR: {HTML_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    data = parse_html(HTML_FILE)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    print(f"Intermediate JSON written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
