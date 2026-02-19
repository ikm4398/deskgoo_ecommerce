import frappe

@frappe.whitelist(allow_guest=True)
def get_blog_posts_with_categories():
    posts = frappe.get_all(
        "Blog Post",
        filters={"is_activate": 1},
        fields=["*"],
        order_by="creation desc"
    )

    result = []

    for post in posts:
        doc = frappe.get_doc("Blog Post", post.name)

        result.append({
            **post,
            "category": [
                {"blog_category": c.blog_category}
                for c in doc.category
            ]
        })

    return result
