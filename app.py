from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['UHoIQNmTwqPjqUcvF8NXGIRRyjM+/1mX/kIX+qOtjqqsJhhEUSPqeXmNwXSXpDFoA+gjZivwSi7yqQ55s16yvGc4kC4u1/OqDmLBX0qAw4uI5YVbiFdyLmalKlOon9+xsaNLM++6XWcbcQ6CWcnpzwdB04t89/1O/w1cDnyilFU='])
handler = WebhookHandler(os.environ['ef1cc014485b4be2b8297e1d0827b0ab'])


@app.route("/callback", methods=['POST'])
def callback():
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
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)