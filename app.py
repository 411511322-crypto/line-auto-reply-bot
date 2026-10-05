import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# 載入 .env 環境變數
load_dotenv()

app = Flask(__name__)

# 讀取 LINE Channel 憑證
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not channel_secret or not channel_access_token:
    print("【警告】未讀取到 LINE_CHANNEL_SECRET 或 LINE_CHANNEL_ACCESS_TOKEN，請檢查 .env 檔案設定！")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/", methods=["GET"])
def index():
    return "LINE Auto Reply Bot is running!", 200


@app.route("/callback", methods=["POST"])
def callback():
    # 取得 LINE 簽章 header
    signature = request.headers.get("X-Line-Signature", "")

    # 取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # 驗證簽章並處理事件
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("簽章驗證失敗！請確認 LINE_CHANNEL_SECRET 是否正確。")
        abort(400)

    return "OK", 200


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()
    user_id = event.source.user_id
    app.logger.info(f"收到來自使用者 {user_id} 的訊息：{user_text}")

    # ===== 自訂關鍵字自動回覆邏輯 =====
    # 你可以依據需求自由新增、修改關鍵字與回覆內容
    if user_text in ["你好", "嗨", "哈囉", "hello", "hi", "Hi", "Hello"]:
        reply_text = "您好！很高興為您服務 😊\n輸入「選單」或「幫助」可查看更多服務說明！"

    elif user_text in ["選單", "目錄", "幫助", "help", "說明"]:
        reply_text = (
            "📋 【服務選單】\n"
            "------------------------\n"
            "🔹 輸入「營業時間」：查看營業與客服時段\n"
            "🔹 輸入「客服」：取得真人客服聯繫方式\n"
            "🔹 輸入「常見問題」：查看 FAQ\n"
            "🔹 輸入「最新活動」：查看本期特惠活動\n"
            "------------------------\n"
            "請直接回覆您想查詢的項目名稱。"
        )

    elif user_text == "營業時間":
        reply_text = "⏰ 【營業時間】\n週一至週五：09:00 - 18:00\n週六、日及國定假日休息。"

    elif user_text == "客服":
        reply_text = "📞 【聯絡客服】\n客服電話：0800-123-456\n客服信箱：support@example.com\n上班時段專員將儘速回覆您的問題！"

    elif user_text == "常見問題":
        reply_text = (
            "❓ 【常見問題 FAQ】\n\n"
            "Q1: 如何下單？\n"
            "A1: 可至我們的官方網站直接選購。\n\n"
            "Q2: 出貨需要多久？\n"
            "A2: 下單後約 1-3 個工作天出貨。"
        )

    elif user_text == "最新活動":
        reply_text = "🎉 【最新活動】\n現在加入官方帳號，結帳輸入折扣碼「WELCOME」現折 100 元！"

    else:
        # 預設回覆（當輸入未匹配的關鍵字時）
        reply_text = f"已收到您的訊息：「{user_text}」\n目前非人工客服時段，若有急事請輸入「選單」查看指引，或留下詳細需求，我們會於上班時間回覆您！"

    # 發送回覆訊息給使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
