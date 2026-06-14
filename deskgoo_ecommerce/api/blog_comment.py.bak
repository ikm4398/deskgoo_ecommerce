import frappe


def _require_login():
    if frappe.session.user == "Guest":
        frappe.throw("Login required", frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def create():
    _require_login()

    data = frappe.request.get_json()
    blog_name = data.get("blog_name")
    comment = data.get("comment")

    if not blog_name or not comment:
        frappe.throw("blog_name and comment are required")

    blog = frappe.get_doc("Blog Post", blog_name)

    new_comment = blog.add_comment(
        "Comment",
        f'<div class="ql-editor read-mode"><p>{comment}</p></div>'
    )

    frappe.db.commit()

    return {
        "message": "Comment added",
        "data": {
            "name": new_comment.name,
            "comment": new_comment.content,   # ✅ correct field
            "by": new_comment.owner,
            "creation": new_comment.creation
        }
    }
@frappe.whitelist(allow_guest=True)
def get_comments(blog_name):
    blog = frappe.get_doc("Blog Post", blog_name)

    comments = []
    if blog._comments:
        comments = frappe.parse_json(blog._comments)

    return {
        "status": "success",
        "data": comments
    }
