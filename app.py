from flask import Flask, request, abort
from datetime import datetime, timedelta
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, DatetimePickerAction, PostbackEvent
)

app = Flask(__name__)

access_token = 'grQlsjFJ72jCNKSZZThIF3XZTLm7KFGsG9Ca9XiFn8qqvem6Wn6314qVZ2fPkcX5v8iZi+qpdHUiuJxBlSojc4CIKCcy6vY7F4nxWpFfN9o7ZIxtmM1HlTCSc9S77sNBN1QSpLHZw+u2YSJxGkBsTAdB04t89/1O/w1cDnyilFU='
secret = 'e50b0f45eea8a920fe6ce14c81c507c6'
line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)

schedules = {}
tasks = []

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

# 處理文字訊息的事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global tasks, schedules
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    response_message = ""

    # 檢查是否有待添加描述的行程
    if user_id in schedules and any(desc is None for desc in schedules[user_id].values()):
        for datetime_str, desc in schedules[user_id].items():
            if desc is None:
                schedules[user_id][datetime_str] = user_message
                response_message = f"添加成功，行程 {datetime_str}，已更新描述：{user_message}"
                break
    else:
        # 如果收到的訊息是 '事項列表'
        if user_message.lower() == "事項列表":
            if tasks:
                response_message = "你的待辦事項：\n" + "\n".join([f"{'✔️' if task['completed'] else ''} {task['name']}" for task in tasks])
            else:
                response_message = "目前沒有待辦事項。"
        # 如果收到的訊息是 '管理行程'
        elif user_message == '管理行程':
            buttons_template = TemplateSendMessage(
                alt_text='行程管理選單：新增行程、刪除行程或查看行事曆',
                template=ButtonsTemplate(
                    title='管理行程',
                    text='請選擇一項功能',
                    actions=[
                        PostbackAction(
                            label='新增行程',
                            data='action=add'
                        ),
                        PostbackAction(
                            label='刪除行程',
                            data='action=delete'
                        ),
                        PostbackAction(
                            label='查看行事曆',
                            data='action=view'
                        )
                    ]
                )
            )
            line_bot_api.reply_message(event.reply_token, buttons_template)

        # 如果收到的訊息是以 '新增' 開頭
        elif user_message.startswith("新增"):
            task_name = user_message[3:]
            tasks.append({"name": task_name, "completed": False})
            response_message = f"已新增事項：{task_name}"
        # 如果收到的訊息是以 '刪除' 開頭
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
        # 如果收到的訊息是以 '完成' 開頭
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
            response_message = "請輸入 '事項列表' 來顯示所有待辦事項，或使用 '新增 <您的事項名稱>' 來新增事項，或使用 '刪除 <您的事項名稱>' 來刪除事項，或使用 '完成 <您的事項名稱>' 來標記事項為完成。"

    if response_message:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_message)
        )

# 處理 Postback 事件
@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    user_id = event.source.user_id

    if data == 'action=add':
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text='請選擇行程時間',
                template=ButtonsTemplate(
                    title='行程時間',
                    text='請選擇行程時間',
                    actions=[
                        DatetimePickerAction(
                            label='選擇時間',
                            data='action=add_datetime',
                            mode='datetime',
                            initial=datetime.now().strftime('%Y-%m-%dT%H:%M'),
                            min=datetime.now().strftime('%Y-%m-%dT%H:%M'),
                            max=(datetime.now() + timedelta(days=365)).strftime('%Y-%m-%dT%H:%M'),
                        )
                    ]
                )
            )
        )
    elif data.startswith('action=add_datetime'):
        if event.postback.params.get('datetime'):
            selected_datetime = event.postback.params['datetime']
            
            formatted_datetime = datetime.strptime(selected_datetime, '%Y-%m-%dT%H:%M')
            formatted_datetime_str = formatted_datetime.strftime('%Y-%m-%d %H:%M')
            
            if user_id not in schedules:
                schedules[user_id] = {}
            schedules[user_id][formatted_datetime_str] = None
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"添加時間：{formatted_datetime_str}")
            )
            
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text="請描述你的行程:")
            )
                
    elif data == 'action=delete':
        user_id = event.source.user_id

        if user_id in schedules and schedules[user_id]:
            buttons = []
            for datetime_str in schedules[user_id]:
                buttons.append(
                    PostbackAction(
                        label=f"刪除 {datetime_str}",
                        data=f"action=confirm_delete&datetime={datetime_str}"
                    )
                )
            buttons_template = TemplateSendMessage(
                alt_text='刪除行程',
                template=ButtonsTemplate(
                    title='刪除行程',
                    text='請選擇要刪除的行程',
                    actions=buttons[:4]
                )
            )
            line_bot_api.reply_message(event.reply_token, buttons_template)
            
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="尚無行程可以刪除")
            )
    
    elif data.startswith('action=confirm_delete'):
        params = dict(param.split('=') for param in data.split('&'))
        datetime_str = params.get('datetime')
        if datetime_str and user_id in schedules and datetime_str in schedules[user_id]:
            del schedules[user_id][datetime_str]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已成功刪除行程：{datetime_str}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="行程不存在或已被刪除")
            )          
        
    elif data == 'action=view':
        if user_id in schedules and schedules[user_id]:
            calendar_text = "查看行事曆：\n"
            for datetime_str, desc in schedules[user_id].items():
                calendar_text += f"時間：{datetime_str}\n描述：{desc or '無描述'}\n\n"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=calendar_text)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="查看行事曆：\n尚無行程")
            )

if __name__ == "__main__":
    app.run(port=5000)
