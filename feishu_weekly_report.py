import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import urllib.request


FEISHU_API = "https://open.feishu.cn/open-apis"


def env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def request_json(method, url, headers=None, payload=None):
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **(headers or {}),
        },
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_tenant_access_token(app_id, app_secret):
    result = request_json(
        "POST",
        f"{FEISHU_API}/auth/v3/tenant_access_token/internal",
        payload={"app_id": app_id, "app_secret": app_secret},
    )
    if result.get("code") != 0:
        raise RuntimeError(f"Failed to get tenant access token: {result}")
    return result["tenant_access_token"]


def list_sheets(token, spreadsheet_token):
    result = request_json(
        "GET",
        f"{FEISHU_API}/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query",
        headers={"Authorization": f"Bearer {token}"},
    )
    if result.get("code") != 0:
        raise RuntimeError(f"Failed to list sheets: {result}")
    return result.get("data", {}).get("sheets", [])


def find_sheet_id(token, spreadsheet_token, sheet_title):
    sheets = list_sheets(token, spreadsheet_token)
    for sheet in sheets:
        if sheet.get("title") == sheet_title:
            return sheet.get("sheet_id")

    available = ", ".join(sheet.get("title", "<unknown>") for sheet in sheets)
    raise RuntimeError(f"Sheet title not found: {sheet_title}. Available sheets: {available}")


def read_cell(token, spreadsheet_token, sheet_id, cell):
    range_value = f"{sheet_id}!{cell}:{cell}"
    encoded_range = urllib.parse.quote(range_value, safe="")
    result = request_json(
        "GET",
        f"{FEISHU_API}/sheets/v2/spreadsheets/{spreadsheet_token}/values/{encoded_range}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if result.get("code") != 0:
        raise RuntimeError(f"Failed to read cell {range_value}: {result}")

    values = result.get("data", {}).get("valueRange", {}).get("values", [])
    if not values or not values[0]:
        return ""
    return values[0][0]


def sign_bot_message(timestamp, secret):
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(string_to_sign, b"", digestmod=hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def send_bot_message(webhook_url, secret, text):
    payload = {
        "msg_type": "text",
        "content": {"text": text},
    }

    if secret:
        timestamp = str(int(time.time()))
        payload["timestamp"] = timestamp
        payload["sign"] = sign_bot_message(timestamp, secret)

    result = request_json("POST", webhook_url, payload=payload)
    if result.get("code") not in (0, None):
        raise RuntimeError(f"Failed to send bot message: {result}")
    return result


def main():
    app_id = env("FEISHU_APP_ID", required=True)
    app_secret = env("FEISHU_APP_SECRET", required=True)
    spreadsheet_token = env("FEISHU_SPREADSHEET_TOKEN", required=True)
    sheet_title = env("FEISHU_SHEET_TITLE", "报价日期-5月第3周")
    cell = env("FEISHU_CELL", "AB4")
    webhook_url = env("FEISHU_BOT_WEBHOOK", required=True)
    bot_secret = env("FEISHU_BOT_SECRET", "")

    token = get_tenant_access_token(app_id, app_secret)
    sheet_id = find_sheet_id(token, spreadsheet_token, sheet_title)
    value = read_cell(token, spreadsheet_token, sheet_id, cell)
    message = f"当前最新海运单价为：{value}元/kg"

    send_bot_message(webhook_url, bot_secret, message)
    print(message)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
