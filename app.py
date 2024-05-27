from flask import Flask, request, abort
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 初始化 LineBotApi 和 WebhookHandler
access_token = 'UHoIQNmTwqPjqUcvF8NXGIRRyjM+/1mX/kIX+qOtjqqsJhhEUSPqeXmNwXSXpDFoA+gjZivwSi7yqQ55s16yvGc4kC4u1/OqDmLBX0qAw4uI5YVbiFdyLmalKlOon9+xsaNLM++6XWcbcQ6CWcnpzwdB04t89/1O/w1cDnyilFU='
secret = 'ef1cc014485b4be2b8297e1d0827b0ab'
line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)

# 定義全局的 tasks 列表
tasks = []

@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 LINE 平台傳送過來的 request body
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global tasks
    user_message = event.message.text
    response_message = ""

    if user_message.lower() == "事項列表":
        if tasks:
            response_message = "你的待辦事項：\n" + "\n".join([f"{'✔️' if task['completed'] else ''} {task['name']}" for task in tasks])
        else:
            response_message = "目前沒有待辦事項。"
    elif user_message.startswith("新增"):
        task_name = user_message[3:]
        tasks.append({"name": task_name, "completed": False})
        response_message = f"已新增事項：{task_name}"
    elif user_message.startswith("刪除"):
        task_name = user_message[3:]
        task_found = False
        for task in tasks:
            if task['name'] == task_name:
                tasks.remove(task)
                task_found = True
                response_message = f"已刪除事項：{task_name}"
                break
        if not task_found:
            response_message = f"找不到事項：{task_name}"
    elif user_message.startswith("完成"):
        task_name = user_message[3:]
        task_found = False
        for task in tasks:
            if task['name'] == task_name:
                task['completed'] = True
                task_found = True
                response_message = f"已完成事項：{task_name}"
                break
        if not task_found:
            response_message = f"找不到事項：{task_name}"
    else:
        response_message = "請輸入 '事項列表' 來顯示所有待辦事項，或使用 '新增<您的事項名稱>' 來新增事項，或使用 '刪除<您的事項名稱>' 來刪除事項，或使用 '完成<您的事項名稱>' 來標記事項為完成。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_message)
    )

if __name__ == "__main__":
    app.run(port=5000)
