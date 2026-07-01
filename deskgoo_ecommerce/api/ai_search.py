import frappe
import requests
import json

@frappe.whitelist(allow_guest=True)
def ai_rerank(query, products):
    try:
        api_key = frappe.conf.get("gemini_api_key")
        if not api_key:
            frappe.throw("Gemini API key not configured")

        if isinstance(products, str):
            products = json.loads(products)

        prompt = f"""You are a product search assistant for a tech e-commerce store.

Query: "{query}"

Rerank these products by relevance to the query. Return ONLY a JSON array of item_codes, most relevant first. No explanation, no markdown, no extra text.

Products:
{json.dumps(products, indent=2)}

Return format example: ["item_code_1", "item_code_2", "item_code_3"]"""

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,       # Low temp = more deterministic JSON
                    "maxOutputTokens": 500,
                    "responseMimeType": "application/json"  # Force JSON output
                }
            },
            timeout=10
        )

        result = response.json()

        # Extract text from Gemini response structure
        text = (
            result
            .get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "[]")
        )

        # Clean and parse
        clean = text.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)

        # Validate it's a list of strings
        if not isinstance(parsed, list):
            raise ValueError("Gemini did not return a list")

        return {"success": True, "data": parsed}

    except requests.exceptions.Timeout:
        frappe.log_error("Gemini API timeout", "AI Search")
        return {"success": False, "data": [], "error": "timeout"}

    except json.JSONDecodeError as e:
        frappe.log_error(f"Gemini JSON parse error: {str(e)} | raw: {text}", "AI Search")
        return {"success": False, "data": [], "error": "parse_error"}

    except Exception as e:
        frappe.log_error(f"AI rerank error: {str(e)}", "AI Search")
        return {"success": False, "data": [], "error": str(e)}
