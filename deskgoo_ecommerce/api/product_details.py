import frappe
from bs4 import BeautifulSoup
from erpnext.stock.utils import get_latest_stock_qty

@frappe.whitelist(allow_guest=True)
def get_items_with_price_and_stock(
    price_list="Standard Selling",
    warehouse=None,
    item=None,
    item_group=None,
    search=None
):
    """
    Fetch items with price, stock, specifications, attachments, and additional fields.
    No hardcoded limit - returns all matching items.
    """
    filters = {
        "disabled": 0,
        "is_sales_item": 1
    }

    if item:
        filters["item_code"] = item

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
        "custom_saved_specifications",
        "brand",
        "warranty_period",
        "description",
        "custom_discount"
    ]

    # No limit - fetch all items matching filters
    items = frappe.get_all("Item", filters=filters, fields=fields)

    result = []

    for item_doc in items:
        # Search filter (post-query, but no limit so acceptable)
        if search:
            search_text = search.lower()
            if (search_text not in (item_doc.item_name or "").lower()
                    and search_text not in (item_doc.item_code or "").lower()):
                continue

        # Price
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item_doc.item_code, "price_list": price_list},
            "price_list_rate"
        ) or 0

        # Stock
        if warehouse:
            stock = frappe.db.get_value(
                "Bin",
                {"item_code": item_doc.item_code, "warehouse": warehouse},
                "actual_qty"
            ) or 0
        else:
            stock = get_latest_stock_qty(item_doc.item_code) or 0

        # Clean specifications from HTML
        specifications = {}
        if item_doc.custom_saved_specifications:
            soup = BeautifulSoup(item_doc.custom_saved_specifications, "html.parser")
            for p in soup.find_all("p"):
                strong = p.find("strong")
                if strong:
                    key = strong.get_text(strip=True).replace(":", "")
                    strong.extract()
                    value = p.get_text(" ", strip=True)
                    specifications[key] = value

        # Attachments
        attachments = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Item",
                "attached_to_name": item_doc.name
            },
            fields=["name", "file_name", "file_url", "is_private"]
        )

        # Final response with all requested fields
        result.append({
            "item_code": item_doc.item_code,
            "item_name": item_doc.item_name or item_doc.item_code,
            "category": item_doc.item_group,
            "image": item_doc.image,
            "price": float(price),
            "instock_quantity": float(stock),
            "rating": item_doc.custom_product_rating or 0,
            "brand": item_doc.brand,
            "warranty_period": item_doc.warranty_period,
            "description": item_doc.description,
            "custom_discount": item_doc.custom_discount,
	    "specifications": specifications,
	    "attachments": attachments,
        })

    return result
