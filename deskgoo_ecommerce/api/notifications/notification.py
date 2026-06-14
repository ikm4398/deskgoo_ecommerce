@frappe.whitelist()
def get_notifications(limit=20, offset=0, notification_type=None):
    """Main API endpoint for customer notifications"""
    try:
        user = frappe.session.user
        
        if user == "Guest":
            return {
                "success": False,
                "message": "Please login to view notifications",
                "status": 401
            }
        
        # Get customer
        customer = frappe.db.get_value("Customer", {"user_id": user}, "name")
        
        if not customer:
            return {
                "success": False,
                "message": "No customer account found. Please contact support.",
                "status": 404
            }
        
        # Initialize response
        notifications = []
        
        # Fetch based on type
        if notification_type in [None, "Order"]:
            order_notifications = get_order_notifications(customer, limit, offset)
            notifications.extend(order_notifications)
        
        if notification_type in [None, "Offer"]:
            offer_notifications = get_offer_notifications(customer, limit, offset)
            notifications.extend(offer_notifications)
        
        if notification_type in [None, "System"]:
            system_notifications = get_system_notifications(customer)
            notifications.extend(system_notifications)
        
        # Sort by creation date
        notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply limit
        notifications = notifications[:limit]
        
        # Get counts
        unread_count = get_unread_count(customer)
        
        return {
            "success": True,
            "data": {
                "notifications": notifications,
                "summary": {
                    "total": len(notifications),
                    "unread": unread_count,
                    "orders": len([n for n in notifications if n.get("type") == "Order"]),
                    "offers": len([n for n in notifications if n.get("type") == "Offer"]),
                    "system": len([n for n in notifications if n.get("type") == "System"])
                }
            }
        }
    
    except Exception as e:
        frappe.log_error(f"Notification API Error: {str(e)}", "Customer Notifications")
        return {
            "success": False,
            "message": "An error occurred. Please try again later.",
            "status": 500
        }


def get_order_notifications(customer, limit, offset):
    """Fetch order notifications from database"""
    
    orders = frappe.db.sql("""
        SELECT 
            so.name as id,
            'Order' as type,
            so.status as title,
            so.modified as created_at,
            so.grand_total,
            so.currency,
            COALESCE((
                SELECT is_read 
                FROM `tabNotification Log` 
                WHERE document_id = so.name 
                    AND customer = %s
                LIMIT 1
            ), 0) as is_read
        FROM `tabSales Order` so
        WHERE so.customer = %s 
            AND so.docstatus = 1
            AND so.status IN ('To Deliver and Bill', 'Completed', 'Cancelled')
        ORDER BY so.modified DESC
        LIMIT %s OFFSET %s
    """, (customer, customer, limit, offset), as_dict=True)
    
    # Format each order
    for order in orders:
        order["message"] = format_order_message(order)
        order["action_text"] = get_order_action(order["status"])
        order["icon"] = get_order_icon(order["status"])
        order["color"] = get_order_color(order["status"])
        order["priority"] = get_order_priority(order["status"])
        
        # Format amount
        if order.get("grand_total"):
            order["formatted_amount"] = f"{order.get('currency', 'USD')} {order['grand_total']:,.2f}"
    
    return orders


def get_offer_notifications(customer, limit, offset):
    """Fetch offer notifications"""
    
    current_date = now()
    
    offers = frappe.db.sql("""
        SELECT 
            name as id,
            'Offer' as type,
            offer_title as title,
            description as message,
            discount_percentage,
            valid_from,
            valid_upto,
            modified as created_at,
            COALESCE((
                SELECT is_read 
                FROM `tabNotification Log` 
                WHERE document_id = name 
                    AND customer = %s
                LIMIT 1
            ), 0) as is_read
        FROM `tabPricing Rule`
        WHERE (customer = %s OR applicable_for = 'All')
            AND disabled = 0
            AND valid_upto >= %s
        ORDER BY valid_upto ASC
        LIMIT %s OFFSET %s
    """, (customer, customer, current_date, limit, offset), as_dict=True)
    
    # Format each offer
    for offer in offers:
        offer["type"] = "Offer"
        offer["action_text"] = "Shop Now"
        offer["icon"] = "tag"
        offer["color"] = "blue"
        offer["priority"] = get_offer_priority(offer)
        
        # Add discount display
        if offer.get("discount_percentage"):
            offer["discount_display"] = f"{offer['discount_percentage']}% OFF"
        
        # Add days remaining
        if offer.get("valid_upto"):
            days_left = (getdate(offer["valid_upto"]) - getdate(current_date)).days
            if days_left >= 0:
                offer["days_left"] = days_left
                if days_left <= 3:
                    offer["priority"] = "high"
                    offer["badge"] = f"Ends in {days_left} days"
    
    return offers


def get_system_notifications(customer):
    """Generate system notifications dynamically"""
    
    notifications = []
    
    # Birthday notification
    customer_dob = frappe.db.get_value("Customer", customer, "date_of_birth")
    if customer_dob:
        today = getdate(now())
        birthday = getdate(customer_dob)
        birthday = birthday.replace(year=today.year)
        
        if birthday == today:
            notifications.append({
                "id": f"birthday_{customer}_{today}",
                "type": "System",
                "title": "Happy Birthday! 🎂",
                "message": "Enjoy a special 20% discount on your next purchase!",
                "created_at": now(),
                "action_text": "Claim Gift",
                "icon": "gift",
                "color": "purple",
                "priority": "high",
                "is_read": 0
            })
    
    # Loyalty notification
    order_count = frappe.db.count("Sales Order", {
        "customer": customer,
        "docstatus": 1,
        "status": "Completed"
    })
    
    if order_count > 0 and order_count % 5 == 0:
        notifications.append({
            "id": f"loyalty_{customer}_{order_count}",
            "type": "System",
            "title": "Loyalty Reward! 🏆",
            "message": f"Congratulations on {order_count} orders! You've unlocked exclusive perks.",
            "created_at": now(),
            "action_text": "View Rewards",
            "icon": "award",
            "color": "gold",
            "priority": "medium",
            "is_read": 0
        })
    
    return notifications


def get_unread_count(customer):
    """Get total unread notifications count"""
    
    # Count unread orders
    unread_orders = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabSales Order` so
        WHERE so.customer = %s
            AND so.docstatus = 1
            AND so.status IN ('To Deliver and Bill', 'Completed', 'Cancelled')
            AND NOT EXISTS (
                SELECT 1 FROM `tabNotification Log` nl
                WHERE nl.document_id = so.name 
                    AND nl.customer = %s
                    AND nl.is_read = 1
            )
    """, (customer, customer), as_dict=True)
    
    # Count unread offers
    current_date = now()
    unread_offers = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabPricing Rule` pr
        WHERE (pr.customer = %s OR pr.applicable_for = 'All')
            AND pr.disabled = 0
            AND pr.valid_upto >= %s
            AND NOT EXISTS (
                SELECT 1 FROM `tabNotification Log` nl
                WHERE nl.document_id = pr.name 
                    AND nl.customer = %s
                    AND nl.is_read = 1
            )
    """, (customer, current_date, customer), as_dict=True)
    
    return (unread_orders[0].get("count", 0) or 0) + (unread_offers[0].get("count", 0) or 0)


def format_order_message(order):
    """Generate dynamic message for order status"""
    status = order.get("status", "")
    name = order.get("id", "")
    
    messages = {
        "To Deliver and Bill": f"Your order #{name} has been confirmed and is being processed.",
        "Completed": f"Your order #{name} has been delivered successfully. Thank you for shopping with us!",
        "Cancelled": f"Your order #{name} has been cancelled. Contact support if this was a mistake."
    }
    
    return messages.get(status, f"Your order #{name} is now {status}")


def get_order_action(status):
    """Get action button text based on status"""
    actions = {
        "To Deliver and Bill": "Track Order",
        "Completed": "Write a Review",
        "Cancelled": "View Details"
    }
    return actions.get(status, "View Details")


def get_order_icon(status):
    """Get icon based on status"""
    icons = {
        "To Deliver and Bill": "truck",
        "Completed": "check-circle",
        "Cancelled": "x-circle"
    }
    return icons.get(status, "bell")


def get_order_color(status):
    """Get color based on status"""
    colors = {
        "To Deliver and Bill": "blue",
        "Completed": "green",
        "Cancelled": "red"
    }
    return colors.get(status, "gray")


def get_order_priority(status):
    """Get priority based on status"""
    priorities = {
        "To Deliver and Bill": "high",
        "Completed": "low",
        "Cancelled": "low"
    }
    return priorities.get(status, "normal")


def get_offer_priority(offer):
    """Get priority based on offer expiry"""
    if offer.get("valid_upto"):
        days_left = (getdate(offer["valid_upto"]) - getdate(now())).days
        if days_left <= 3:
            return "high"
        elif days_left <= 7:
            return "medium"
    return "normal"


@frappe.whitelist()
def mark_as_read(notification_type, notification_id):
    """Mark a single notification as read"""
    try:
        user = frappe.session.user
        
        if user == "Guest":
            return {"success": False, "message": "Please login"}
        
        customer = frappe.db.get_value("Customer", {"user_id": user}, "name")
        
        if not customer:
            return {"success": False, "message": "Customer not found"}
        
        # Check if log exists
        existing = frappe.db.get_value("Notification Log", {
            "customer": customer,
            "document_id": notification_id,
            "notification_type": notification_type
        }, "name")
        
        if existing:
            frappe.db.set_value("Notification Log", existing, "is_read", 1)
        else:
            # Create new log
            log = frappe.get_doc({
                "doctype": "Notification Log",
                "customer": customer,
                "notification_type": notification_type,
                "document_id": notification_id,
                "is_read": 1,
                "title": "Read",
                "message": "Marked as read"
            })
            log.insert(ignore_permissions=True)
        
        frappe.db.commit()
        
        return {"success": True, "message": "Marked as read"}
    
    except Exception as e:
        frappe.log_error(f"Mark as read error: {str(e)}", "Notifications")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def mark_all_as_read():
    """Mark all notifications as read"""
    try:
        user = frappe.session.user
        
        if user == "Guest":
            return {"success": False, "message": "Please login"}
        
        customer = frappe.db.get_value("Customer", {"user_id": user}, "name")
        
        if not customer:
            return {"success": False, "message": "Customer not found"}
        
        # Get all unread orders
        orders = frappe.db.sql("""
            SELECT name FROM `tabSales Order`
            WHERE customer = %s AND docstatus = 1
        """, customer, as_dict=True)
        
        for order in orders:
            mark_as_read("Order", order["name"])
        
        return {"success": True, "message": "All notifications marked as read"}
    
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_settings():
    """Get user notification settings"""
    user = frappe.session.user
    
    settings = frappe.db.get_value("Notification Settings", 
                                   {"user": user}, 
                                   ["push_notifications", "email_notifications", "sound_enabled"], 
                                   as_dict=True)
    
    if not settings:
        settings = {
            "push_notifications": 1,
            "email_notifications": 0,
            "sound_enabled": 1
        }
    
    return {"success": True, "settings": settings}


@frappe.whitelist()
def update_settings():
    """Update notification settings"""
    try:
        user = frappe.session.user
        data = frappe.local.form_dict
        
        existing = frappe.db.get_value("Notification Settings", {"user": user}, "name")
        
        settings_data = {
            "doctype": "Notification Settings",
            "user": user,
            "push_notifications": data.get("push_notifications", 1),
            "email_notifications": data.get("email_notifications", 0),
            "sound_enabled": data.get("sound_enabled", 1)
        }
        
        if existing:
            frappe.db.set_value("Notification Settings", existing, settings_data)
        else:
            doc = frappe.get_doc(settings_data)
            doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
        
        return {"success": True, "message": "Settings updated"}
    
    except Exception as e:
        return {"success": False, "message": str(e)}
