from flask import Flask, request

# 載入 json 標準函式庫，處理回傳的資料格式
import json

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)                    # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                         # json 格式化訊息內容
        access_token = 'UHoIQNmTwqPjqUcvF8NXGIRRyjM+/1mX/kIX+qOtjqqsJhhEUSPqeXmNwXSXpDFoA+gjZivwSi7yqQ55s16yvGc4kC4u1/OqDmLBX0qAw4uI5YVbiFdyLmalKlOon9+xsaNLM++6XWcbcQ6CWcnpzwdB04t89/1O/w1cDnyilFU='
        secret = 'ef1cc014485b4be2b8297e1d0827b0ab'
        line_bot_api = LineBotApi(access_token)              # 確認 token 是否正確
        handler = WebhookHandler(secret)                     # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']      # 加入回傳的 headers
        handler.handle(body, signature)                      # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']            # 取得回傳訊息的 Token
        type = json_data['events'][0]['message']['type']     # 取得 LINe 收到的訊息類型
        if type=='text':
            msg = json_data['events'][0]['message']['text']  # 取得 LINE 收到的文字訊息
            print(msg)                                       # 印出內容
            reply = msg
        else:
            reply = '你傳的不是文字呦～'
        print(reply)
        line_bot_api.reply_message(tk,TextSendMessage(reply))# 回傳訊息
    except:
        print(body)                                          # 如果發生錯誤，印出收到的內容
    return 'OK'                                              # 驗證 Webhook 使用，不能省略


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_text = event.message.text

    if message_text == '管理行程':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='請輸入「增加」、「修改」或「刪除」來操作功能\n如需設定通知請輸入「設定通知」'))
    elif message_text == '待辦事項':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='請輸入「增加」、「修改」或「刪除」來操作功能\n如需設定通知請輸入「設定通知」'))
    elif message_text == '???????':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='This is keyword for @register!'))
    elif message_text == '@message':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='This is keyword for @message!'))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='請輸入正確關鍵字'))

if __name__ == "__main__":

    app.run()