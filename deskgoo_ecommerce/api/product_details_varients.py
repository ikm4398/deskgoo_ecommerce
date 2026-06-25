import frappe
from bs4 import BeautifulSoup
from erpnext.stock.utils import get_latest_stock_qty


@frappe.whitelist(allow_guest=True)
def get_item_variants(item_code, price_list="Standard Selling", warehouse=None, search=None):
    """Return variant items for an Item template code."""
    if not item_code:
        frappe.throw("Item code is required")

    parent_template = frappe.db.get_value("Item", item_code, "variant_of")
    if parent_template:
        item_code = parent_template

    item_fields = [
        "name",
        "item_code",
        "item_name",
        "stock_uom",
        "image",
        "item_group",
        "brand",
        "warranty_period",
        "description",
        "variant_of"
    ]

    variants = frappe.get_all(
        "Item",
        filters={
            "disabled": 0,
            "is_sales_item": 1,
            "variant_of": item_code
        },
        fields=item_fields
    )

    def safe_item_value(item_code, fieldname):
        try:
            if frappe.db.has_column("Item", fieldname):
                return frappe.db.get_value("Item", item_code, fieldname)
        except Exception:
            return None
        return None

    result = []
    for item_doc in variants:
        if search:
            search_text = search.lower()
            if (search_text not in (item_doc.item_name or "").lower()
                    and search_text not in (item_doc.item_code or "").lower()):
                continue

        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item_doc.item_code, "price_list": price_list},
            "price_list_rate"
        ) or 0

        if warehouse:
            stock = frappe.db.get_value(
                "Bin",
                {"item_code": item_doc.item_code, "warehouse": warehouse},
                "actual_qty"
            ) or 0
        else:
            stock = get_latest_stock_qty(item_doc.item_code) or 0

        specifications = {}
        spec_html = (
            safe_item_value(item_doc.item_code, "custom_saved_specifications")
            or safe_item_value(item_doc.item_code, "custom_item_specifications")
            or safe_item_value(item_doc.item_code, "custom_specifications")
        )
        if spec_html:
            soup = BeautifulSoup(spec_html, "html.parser")
            for p in soup.find_all("p"):
                strong = p.find("strong")
                if strong:
                    key = strong.get_text(strip=True).replace(":", "")
                    strong.extract()
                    value = p.get_text(" ", strip=True)
                    specifications[key] = value

        attachments = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Item",
                "attached_to_name": item_doc.name
            },
            fields=["name", "file_name", "file_url", "is_private"]
        )

        result.append({
            "item_code": item_doc.item_code,
            "item_name": item_doc.item_name or item_doc.item_code,
            "category": item_doc.item_group,
            "image": item_doc.image,
            "price": float(price),
            "instock_quantity": float(stock),
            "rating": safe_item_value(item_doc.item_code, "custom_product_rating") or 0,
            "brand": item_doc.brand,
            "warranty_period": item_doc.warranty_period,
            "description": item_doc.description,
            "custom_discount": safe_item_value(item_doc.item_code, "custom_discount"),
            "variant_of": item_doc.variant_of,
            "specifications": specifications,
            "attachments": attachments,
        })

    return result
