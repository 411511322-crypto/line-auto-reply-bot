import os
from dotenv import load_dotenv
from flask import Flask, request, abort
import google.generativeai as genai
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
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not channel_secret or not channel_access_token:
    print("【警告】未讀取到 LINE_CHANNEL_SECRET 或 LINE_CHANNEL_ACCESS_TOKEN，請檢查 .env 檔案設定！")

# 初始化 LINE SDK
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# 初始化 Google Gemini AI
gemini_model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=(
                "你是一位親切、熱情且專業的 LINE 智慧客服助理。"
                "請始終使用繁體中文（台灣習慣用語）簡明扼要地回答使用者的任何問題。"
                "回答風格保持自然有禮，排版適當空行，非常適合在手機通訊軟體上閱讀。"
                "若使用者詢問公司內部專案或具體訂單，但你無法確定時，可引導使用者輸入「客服」以聯繫真人專員。"
            )
        )
        print("【成功】Google Gemini AI 已成功啟用！")
    except Exception as e:
        print(f"【錯誤】Gemini 初始化失敗：{e}")
else:
    print("【提示】未設定 GEMINI_API_KEY，將僅使用固定關鍵字模式。")


@app.route("/", methods=["GET"])
def index():
    return "LINE Auto Reply Bot with Gemini AI is running!", 200


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

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

    # ===== 1. 優先匹配官方固定業務指令 (避免 AI 幻覺) =====
    if user_text in ["選單", "目錄", "幫助", "help", "說明"]:
        reply_text = (
            "📋 【服務選單】\n"
            "------------------------\n"
            "🔹 輸入「營業時間」：查看營業與客服時段\n"
            "🔹 輸入「客服」：取得真人客服聯繫方式\n"
            "🔹 輸入「常見問題」：查看 FAQ\n"
            "🔹 輸入「最新活動」：查看本期特惠活動\n"
            "------------------------\n"
            "💡 提示：您也可以直接問我任何問題（例如：天氣、生活常識、寫程式、生活大小事），AI 助理會為您即時解答！"
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

    # ===== 2. 其餘任何訊息 ➜ 由 Google Gemini AI 智慧解答 =====
    else:
        if gemini_model:
            try:
                # 呼叫 Gemini AI 生成回覆
                ai_response = gemini_model.generate_content(user_text)
                reply_text = ai_response.text.strip()
                # 確保不超過 LINE 訊息 5000 字限制
                if len(reply_text) > 4000:
                    reply_text = reply_text[:4000] + "..."
            except Exception as e:
                app.logger.error(f"Gemini API 處理錯誤: {e}")
                reply_text = (
                    "抱歉，目前 AI 正在熱烈思考中，請稍候片刻再試一次！\n"
                    "您也可以輸入「選單」查看常用功能指引。"
                )
        else:
            reply_text = f"已收到您的訊息：「{user_text}」\n若有任何需要，請輸入「選單」查看更多功能！"

    # 發送回覆給使用者
    app.logger.info(f"準備發送回覆內容：{reply_text}")
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        app.logger.info("【成功】已成功發送訊息給使用者！")
    except Exception as e:
        app.logger.error(f"【失敗】呼叫 LINE Reply API 發生錯誤：{e}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
