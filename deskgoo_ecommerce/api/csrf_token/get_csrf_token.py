import frappe

@frappe.whitelist(allow_guest=False)
def get_csrf_token():
    return {
        "csrf_token": frappe.sessions.get_csrf_token(),
        "user": frappe.session.user
    }