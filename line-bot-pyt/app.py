#主要測試
from flask import Flask, request, abort
from datetime import datetime, timedelta
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, DatetimePickerAction, PostbackEvent, QuickReply, QuickReplyButton, FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, ButtonComponent, SeparatorComponent
)
import sqlite3

app = Flask(__name__)

access_token = 'UHoIQNmTwqPjqUcvF8NXGIRRyjM+/1mX/kIX+qOtjqqsJhhEUSPqeXmNwXSXpDFoA+gjZivwSi7yqQ55s16yvGc4kC4u1/OqDmLBX0qAw4uI5YVbiFdyLmalKlOon9+xsaNLM++6XWcbcQ6CWcnpzwdB04t89/1O/w1cDnyilFU='
secret = 'ef1cc014485b4be2b8297e1d0827b0ab'
line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)

# 初始化 SQLite 資料庫和表
def init_db():
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        task_name TEXT,
        completed BOOLEAN
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        datetime_str TEXT,
        description TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        pending_task TEXT,
        pending_schedule TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# 資料庫操作函数
def add_task(user_id, task_name):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, task_name, completed) VALUES (?, ?, ?)", (user_id, task_name, False))
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("SELECT task_name, completed FROM tasks WHERE user_id = ?", (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def delete_task(user_id, task_name):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE user_id = ? AND task_name = ?", (user_id, task_name))
    conn.commit()
    conn.close()

def mark_task_completed(user_id, task_name):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET completed = ? WHERE user_id = ? AND task_name = ?", (True, user_id, task_name))
    conn.commit()
    conn.close()

def add_schedule(user_id, datetime_str, description):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO schedules (user_id, datetime_str, description) VALUES (?, ?, ?)", (user_id, datetime_str, description))
    conn.commit()
    conn.close()

def get_schedules(user_id):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("SELECT datetime_str, description FROM schedules WHERE user_id = ?", (user_id,))
    schedules = cursor.fetchall()
    conn.close()
    return schedules

def delete_schedule(user_id, datetime_str):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE user_id = ? AND datetime_str = ?", (user_id, datetime_str))
    conn.commit()
    conn.close()

def set_pending_task(user_id, task_name):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, pending_task, pending_schedule) VALUES (?, ?, ?)", (user_id, task_name, None))
    conn.commit()
    conn.close()

def get_pending_task(user_id):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("SELECT pending_task FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_pending_schedule(user_id, datetime_str):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, pending_task, pending_schedule) VALUES (?, ?, ?)", (user_id, None, datetime_str))
    conn.commit()
    conn.close()

def get_pending_schedule(user_id):
    conn = sqlite3.connect('tasks_schedules.db')
    cursor = conn.cursor()
    cursor.execute("SELECT pending_schedule FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

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
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    response_message = ""

    # 先檢查是否有待添加的行程描述或待辦事項
    pending_task = get_pending_task(user_id)
    pending_schedule = get_pending_schedule(user_id)

    if pending_schedule:
        add_schedule(user_id, pending_schedule, user_message)
        response_message = f"添加成功，行程 {pending_schedule}，已更新行程：{user_message}"
        set_pending_schedule(user_id, None)  # 清除待添加行程
        line_bot_api.reply_message(
            event.reply_token,
            create_flex_message("行程已更新", pending_schedule, user_message)
        )
    elif pending_task:
        add_task(user_id, user_message)
        response_message = f"添加成功，待辦事項：{user_message}"
        set_pending_task(user_id, None)  # 清除待添加事項
        line_bot_api.reply_message(
            event.reply_token,
            create_task_flex_message(user_message)
        )
    else:
        # 根據用戶的指令來操作
        if user_message.lower() == "事項列表":
            tasks = get_tasks(user_id)
            if tasks:
                response_message = "你的待辦事項：\n" + "\n".join([f"{'✔️' if completed else ''} {task_name}" for task_name, completed in tasks])
            else:
                response_message = "目前沒有待辦事項。"
        elif user_message == '管理行程':
            quick_reply_buttons = [
                QuickReplyButton(action=PostbackAction(label="新增行程", data="action=add")),
                QuickReplyButton(action=PostbackAction(label="刪除行程", data="action=delete")),
                QuickReplyButton(action=PostbackAction(label="查看行事曆", data="action=view"))
            ]
            quick_reply = QuickReply(items=quick_reply_buttons)
            text_message = TextSendMessage(text="選擇行程管理功能：", quick_reply=quick_reply)
            line_bot_api.reply_message(event.reply_token, text_message)

        elif user_message == '待辦事項':
            quick_reply_buttons = [
                QuickReplyButton(action=PostbackAction(label="新增待辦事項", data="action=add_task")),
                QuickReplyButton(action=PostbackAction(label="刪除待辦事項", data="action=delete_task")),
                QuickReplyButton(action=PostbackAction(label="查看待辦事項", data="action=view_tasks"))
            ]
            quick_reply = QuickReply(items=quick_reply_buttons)
            text_message = TextSendMessage(text="選擇待辦事項功能：", quick_reply=quick_reply)
            line_bot_api.reply_message(event.reply_token, text_message)

        else:
            response_message = "請輸入 '待辦事項' 以查看待辦事項選單或 '管理行程' 以查看行程管理選單"

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

            set_pending_schedule(user_id, formatted_datetime_str)  # 設置待添加行程

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"添加時間：{formatted_datetime_str}")
            )
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text="請輸入你的行程:")
            )
    
    elif data == 'action=delete':
        schedules = get_schedules(user_id)

        if schedules:
            buttons = []
            for datetime_str, description in schedules:
                buttons.append(
                    PostbackAction(
                        label=f"刪除 {description}",
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
        if datetime_str:
            schedules = get_schedules(user_id)
            description = None
            for sched in schedules:
                if sched[0] == datetime_str:
                    description = sched[1]
                    break
            delete_schedule(user_id, datetime_str)
            if description:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"已成功刪除行程：{description}")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="行程不存在或已被刪除")
                )

    elif data == 'action=view':
        schedules = get_schedules(user_id)
        if schedules:
            line_bot_api.reply_message(
                event.reply_token,
                create_flex_schedule_message(schedules)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="查看行事曆：\n尚無行程")
            )
            
    elif data == 'action=add_task':
        set_pending_task(user_id, True)  # 設置待添加事項
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入待辦事項名稱：")
        )

    elif data.startswith('action=delete_task'):
        tasks = get_tasks(user_id)
        if tasks:
            buttons = [
                PostbackAction(label=task_name, data=f"action=confirm_delete_task&task={task_name}")
                for task_name, completed in tasks
            ]
            template = ButtonsTemplate(
                title="刪除待辦事項",
                text="選擇要刪除的待辦事項：",
                actions=buttons
            )
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(alt_text="刪除待辦事項", template=template)
            )
    
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="尚無待辦事項可以刪除")
            )
            
    elif data.startswith('action=complete_task'):
        params = dict(param.split('=') for param in data.split('&'))
        task_name = params.get('task')
        if task_name:
            mark_task_completed(user_id, task_name)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已完成待辦事項：{task_name}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="待辦事項不存在或已完成")
            )
            
    # 添加以下處理待辦事項刪除完成的回應
    if data.startswith('action=confirm_delete_task'):
        params = dict(param.split('=') for param in data.split('&'))
        task_name = params.get('task')
        if not task_name:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="抱歉，找不到待辦事項名稱")
            )
            return

        delete_task(user_id, task_name)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"已成功刪除待辦事項：{task_name}")
        )

    elif data == 'action=view_tasks':
        tasks = get_tasks(user_id)
        if tasks:
            task_text = "查看待辦事項：\n"
            for task_name, completed in tasks:
                task_text += f"{'✔️' if completed else ''} {task_name}\n"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=task_text)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="查看待辦事項：\n尚無待辦事項")
            )

    elif data.startswith('action=complete_task'):
        params = dict(param.split('=') for param in data.split('&'))
        task_name = params.get('task')
        if task_name:
            mark_task_completed(user_id, task_name)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已完成待辦事項：{task_name}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="待辦事項不存在或已完成")
            )
            
            print(f"收到 Postback 事件，資料為：{data}")

# 建立 Flex Message
def create_flex_message(title, datetime_str, description):
    flex_message = FlexSendMessage(
        alt_text="行程已更新",
        contents=BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text=title, weight="bold", size="xl"),
                    SeparatorComponent(margin="md"),
                    TextComponent(text=f"時間：{datetime_str}", margin="md"),
                    TextComponent(text=f"行程：{description}", margin="md")
                ]
            )
        )
    )
    return flex_message

# 建立行程 Flex Message
def create_flex_schedule_message(schedules):
    contents = []
    for datetime_str, description in schedules:
        contents.append(
            BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text=f"時間：{datetime_str}", margin="md"),
                    TextComponent(text=f"行程：{description or '無行程'}", margin="md"),
                    SeparatorComponent(margin="md")  # 用於分隔不同行程
                ]
            )
        )
        
    flex_message = FlexSendMessage(
        alt_text="查看行事曆",
        contents=BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text="查看行事曆", weight="bold", size="xl"),
                    SeparatorComponent(margin="md"),
                    *contents
                ]
            )
        )
    )
    return flex_message

# 建立待辦事項 Flex Message
def create_task_flex_message(task_name):
    flex_message = FlexSendMessage(
        alt_text="待辦事項已更新",
        contents=BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text="待辦事項", weight="bold", size="xl"),
                    SeparatorComponent(margin="md"),
                    TextComponent(text=task_name, margin="md", size="lg"),
                    BoxComponent(
                        layout="horizontal",
                        contents=[
                            ButtonComponent(
                                style="primary",
                                color="#00B900",
                                action=PostbackAction(label="完成", data=f"action=complete_task&task={task_name}")
                            ),
                            ButtonComponent(
                                style="secondary",
                                color="#FFFFFF",
                                action=PostbackAction(label="刪除", data=f"action=confirm_delete_task&task={task_name}")
                            )
                        ]
                    )
                ]
            )
        )
    )
    return flex_message

if __name__ == "__main__":
    app.run(port=5000)
