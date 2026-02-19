import frappe
from erpnext.stock.utils import get_latest_stock_qty
from frappe import _

@frappe.whitelist()
def get_items_with_price_and_stock(price_list="Standard Selling", warehouse=None, limit=100):

    items = frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_sales_item": 1},
        fields=[
            "name",
            "item_code",
            "item_name",
            "stock_uom",
            "image",          # Product Image
            "item_group",     # Item Category
            "custom_product_rating"
        ],
        limit=limit
    )

    result = []

    for item in items:
        # Get selling price
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item.item_code, "price_list": price_list},
            "price_list_rate"
        ) or 0

        # Get stock
        if warehouse:
            stock = frappe.db.get_value(
                "Bin",
                {"item_code": item.item_code, "warehouse": warehouse},
                "actual_qty"
            ) or 0
        else:
            stock = get_latest_stock_qty(item.item_code) or 0

        result.append({
            "item_code": item.item_code,
            "item_name": item.item_name or item.item_code,
            "category": item.item_group,          # Item Category
            "image": item.image,                  # Product Image URL
            "price": float(price),
            "instock_quantity": float(stock),
            "rating": item.custom_product_rating  # Custom Product Rating
        })

    return result
