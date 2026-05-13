import frappe
from bs4 import BeautifulSoup
from erpnext.stock.utils import get_latest_stock_qty

@frappe.whitelist(allow_guest=True)
def get_items_with_price_and_stock(
    price_list="Standard Selling",
    warehouse=None,
    item=None,
    item_group=None,
    search=None,
    limit=100
):

    filters = {
        "disabled": 0,
        "is_sales_item": 1
    }

    # Filter by exact item code/name
    if item:
        filters["item_code"] = item

    # Filter by item group/category
    if item_group:
        filters["item_group"] = item_group

    fields = [
        "name",
        "item_code",
        "item_name",
        "stock_uom",
        "image",
        "item_group",
        "custom_product_rating",
        "custom_saved_specifications"
    ]

    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=fields,
        limit=limit
    )

    result = []

    for item_doc in items:

        # Search filter
        if search:
            search_text = search.lower()

            if (
                search_text not in (item_doc.item_name or "").lower()
                and search_text not in (item_doc.item_code or "").lower()
            ):
                continue

        # =========================
        # PRICE
        # =========================
        price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": item_doc.item_code,
                "price_list": price_list
            },
            "price_list_rate"
        ) or 0

        # =========================
        # STOCK
        # =========================
        if warehouse:
            stock = frappe.db.get_value(
                "Bin",
                {
                    "item_code": item_doc.item_code,
                    "warehouse": warehouse
                },
                "actual_qty"
            ) or 0
        else:
            stock = get_latest_stock_qty(item_doc.item_code) or 0

        # =========================
        # CLEAN SPECIFICATIONS
        # =========================
        specifications = {}

        if item_doc.custom_saved_specifications:

            soup = BeautifulSoup(
                item_doc.custom_saved_specifications,
                "html.parser"
            )

            paragraphs = soup.find_all("p")

            for p in paragraphs:
                strong = p.find("strong")

                if strong:
                    key = strong.get_text(strip=True).replace(":", "")

                    strong.extract()

                    value = p.get_text(" ", strip=True)

                    specifications[key] = value

        # =========================
        # ATTACHMENTS
        # =========================
        attachments = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Item",
                "attached_to_name": item_doc.name
            },
            fields=[
                "name",
                "file_name",
                "file_url",
                "is_private"
            ]
        )

        # =========================
        # FINAL RESPONSE
        # =========================
        result.append({
            "item_code": item_doc.item_code,
            "item_name": item_doc.item_name or item_doc.item_code,
            "category": item_doc.item_group,
            "image": item_doc.image,
            "price": float(price),
            "instock_quantity": float(stock),
            "rating": item_doc.custom_product_rating or 0,

            # Clean JSON specification
            "specifications": specifications,

            # All attachments
            "attachments": attachments
        })

    return result
