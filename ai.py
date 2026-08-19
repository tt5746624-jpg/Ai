import requests
import time
import re
import html
import json
import urllib.parse

BOT_TOKEN = "8707250409:AAF_uLsSYVL_-nik_kYZVDBXioxcaBXxafs"
BOT_USERNAME = "@xoni_ai_testbot"
AI_API = "https://r-bots-free-apis.co08.art/api/gemini"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# AI Image Generator
IMAGE_API = "https://image.pollinations.ai/prompt"

MESSAGE_LIMIT = 3500
MAX_HISTORY = 6

user_history = {}
last_question = {}

XONI_PROFILE = """
XONI PROFILE:
Xoni is a developer/project creator. Xoni works with Android
development, Sketchware, Telegram bots, developer tools, automation,
Termux, Python, PHP, Java, JSON and XML. Xoni has worked on projects
such as Xoni Tools and other developer utilities, including MLBB-related
developer/tool projects. Xoni commonly communicates in Burmese and English.

Only use these facts for Xoni-related questions. Never invent Xoni's
age, real name, address, phone, family, school, income, private accounts,
passwords, tokens, or other unsupported/private information. If a detail
is unknown, say you do not have reliable information about it.
"""

SYSTEM_PROMPT = """
You are Xoni AI.
Your name is Xoni AI. You were created/configured by Xoni.
You are NOT Xoni himself.

For questions about Xoni, use the supplied XONI PROFILE as the source
of truth. If asked "Xoni ဆိုတာဘယ်သူလဲ" or "Who is Xoni?", answer clearly,
naturally, and in the user's language. Never invent unsupported facts.

Understand Burmese, English and mixed Burmese-English.
Be helpful, accurate and direct.

You are a programming assistant. Support Java, Kotlin, Python, PHP,
JavaScript, TypeScript, HTML, CSS, JSON, XML, Bash, C/C++, C#, SQL
and other languages.

If the user asks for code, provide actual code.
If they ask for full code/full fix/all full fix, provide complete code.
Preserve existing names and structure when practical.
Put code in Markdown fenced blocks.
Do not claim code was executed unless actually tested.

The Telegram bot detects code requests and explicit file requests.
"""

EXT = {
    "python": "py", "py": "py", "java": "java",
    "kotlin": "kt", "kt": "kt", "javascript": "js", "js": "js",
    "typescript": "ts", "ts": "ts", "php": "php", "html": "html",
    "css": "css", "json": "json", "xml": "xml", "bash": "sh",
    "shell": "sh", "sh": "sh", "c": "c", "cpp": "cpp", "c++": "cpp",
    "csharp": "cs", "cs": "cs", "sql": "sql", "yaml": "yml",
    "yml": "yml", "markdown": "md", "md": "md"
}


def telegram(method, data=None, files=None, timeout=60):
    try:
        url = f"{TELEGRAM_API}/{method}"
        if files:
            r = requests.post(url, data=data or {}, files=files, timeout=timeout)
        else:
            r = requests.post(url, json=data or {}, timeout=timeout)
        return r.json()
    except Exception as e:
        print("[Telegram Error]", e)
        return None


def send_message(chat_id, text, reply_to=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_to:
        data["reply_to_message_id"] = reply_to
    return telegram("sendMessage", data)


def send_photo(chat_id, photo, caption=None, reply_to=None):
    data = {"chat_id": chat_id, "photo": photo}
    if caption:
        data["caption"] = caption[:1024]
        data["parse_mode"] = "HTML"
    if reply_to:
        data["reply_to_message_id"] = reply_to
    return telegram("sendPhoto", data)


def create_image(chat_id, prompt, reply_to=None):
    prompt = prompt.strip()
    if not prompt:
        send_message(
            chat_id,
            "🎨 <b>Image Creator</b>\n\n"
            "ပုံဖန်တီးချင်တဲ့ prompt ကိုရေးပေးပါ။\n\n"
            "ဥပမာ — <code>/image cyberpunk developer desk, neon lights</code>",
            reply_to
        )
        return

    status = send_message(chat_id, "🎨 <b>Creating image...</b>", reply_to)
    status_id = status.get("result", {}).get("message_id") if status and status.get("ok") else None

    try:
        encoded = urllib.parse.quote(prompt, safe="")
        image_url = f"{IMAGE_API}/{encoded}?width=1024&height=1024&nologo=true&model=flux"

        result = send_photo(
            chat_id,
            image_url,
            "🎨 <b>Xoni AI Image Creator</b>\n"
            f"📝 {html.escape(prompt[:700])}",
            reply_to
        )

        if not result or not result.get("ok"):
            send_message(chat_id, "❌ <b>Image creation failed.</b>\nခဏနေပြီး prompt ပြန်စမ်းကြည့်ပါ။", reply_to)
    except Exception as e:
        print("[Image Error]", e)
        send_message(chat_id, "❌ <b>Image Creator Error</b>\nပုံဖန်တီးရာမှာ error ဖြစ်သွားပါတယ်။", reply_to)
    finally:
        if status_id:
            delete_message(chat_id, status_id)


def edit_message(chat_id, message_id, text):
    return telegram("editMessageText", {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    })


def delete_message(chat_id, message_id):
    return telegram("deleteMessage", {
        "chat_id": chat_id,
        "message_id": message_id
    })


def typing(chat_id):
    return telegram("sendChatAction", {
        "chat_id": chat_id,
        "action": "typing"
    })


def send_document(chat_id, content, filename, caption=None, reply_to=None):
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption[:1024]
        data["parse_mode"] = "HTML"
    if reply_to:
        data["reply_to_message_id"] = reply_to

    files = {
        "document": (
            filename,
            content.encode("utf-8"),
            "text/plain"
        )
    }

    return telegram(
        "sendDocument",
        data,
        files=files,
        timeout=120
    )


def normalize(text):
    return re.sub(r"\s+", " ", text.lower().strip())


def is_image_request(text):
    t = normalize(text)
    patterns = [
        "/image", "/img", "image create", "create image",
        "generate image", "make an image", "image generator",
        "image creator", "ပုံလုပ်", "ပုံဖန်တီး", "ပုံဆွဲ",
        "image လုပ်"
    ]
    return any(x in t for x in patterns)


def extract_image_prompt(text):
    t = text.strip()
    for cmd in ("/image", "/img"):
        if t.lower().startswith(cmd):
            return t[len(cmd):].strip()

    patterns = [
        "create image", "generate image", "make an image",
        "image create", "image creator", "image generator",
        "ပုံဖန်တီး", "ပုံလုပ်", "ပုံဆွဲ", "image လုပ်"
    ]
    low = t.lower()
    for prefix in patterns:
        if low.startswith(prefix):
            return t[len(prefix):].strip(" :,-")
    return t


def is_file_request(text):
    t = normalize(text)
    patterns = [
        "send as file", "send as a file", "send file",
        "send the file", "as file", "as a file", "source file",
        "file နဲ့ပို့", "file နဲ့ပေး", "file နဲ့ပို့ပေး",
        "file နဲ့ပေးပါ", "ဖိုင်နဲ့ပို့", "ဖိုင်နဲ့ပေး",
        "ဖိုင်နဲ့ပို့ပေး", "ဖိုင်နဲ့ပေးပါ",
        "ဖိုင်အနေနဲ့ပို့", "ဖိုင်အနေနဲ့ပေး"
    ]
    return any(x in t for x in patterns)


def is_code_request(text):
    t = normalize(text)
    patterns = [
        "write code", "write a code", "write me code", "code for",
        "coding", "programming", "full code", "full fix", "all full fix",
        "complete code", "complete source", "source code",
        "fix this code", "fix code", "debug this", "debug code",
        "python code", "java code", "kotlin code", "php code",
        "javascript code", "html code", "css code", "json code",
        "xml code", "bash code", "shell script", "script ရေး",
        "code ရေး", "code ရေးပေး", "code ပြင်", "code ပြင်ပေး",
        "ကုဒ်ရေး", "ကုဒ်ရေးပေး", "ကုဒ်ပြင်", "ကုဒ်ပြင်ပေး",
        "code လုပ်", "code လုပ်ပေး", "full fix ပေး", "full code ပေး"
    ]
    return any(x in t for x in patterns)


def detect_language(text):
    s = text.lower()

    if "public class " in s or "system.out.println" in s:
        return "java"
    if "fun main(" in s or ("val " in s and "println(" in s):
        return "kotlin"
    if "def " in s or "if __name__ ==" in s:
        return "python"
    if "<?php" in s:
        return "php"
    if "<!doctype html" in s or "<html" in s:
        return "html"
    if "console.log(" in s or "function " in s:
        return "javascript"
    if "#include <iostream>" in s or "using namespace std" in s:
        return "cpp"
    if "#include <stdio.h>" in s or "printf(" in s:
        return "c"
    if "<?xml" in s or "<manifest" in s:
        return "xml"
    if "select " in s or "insert into " in s:
        return "sql"
    if "#!/bin/bash" in s or "pkg install " in s:
        return "bash"

    return "text"


def detect_code_language(text):
    m = re.search(r"```([a-zA-Z0-9_+#.-]*)", text)
    if m and m.group(1).lower() in EXT:
        return m.group(1).lower()
    return detect_language(text)


def is_code_response(text):
    if "```" in text:
        return True

    s = text.lower()
    signs = [
        "public class ", "def ", "<?php", "<html", "console.log(",
        "#include ", "fun main(", "using namespace std", "select ",
        "import android.", "package com.", "function "
    ]
    return any(x in s for x in signs)


def extract_code(text):
    blocks = re.findall(
        r"```(?:[a-zA-Z0-9_+#.-]*)?\s*\n?(.*?)```",
        text,
        flags=re.DOTALL
    )
    if blocks:
        return "\n\n".join(x.strip() for x in blocks)
    return text.strip()


def format_response(text):
    blocks = []

    def replace_code(match):
        i = len(blocks)
        blocks.append(match.group(2).strip())
        return f"___XONI_CODE_{i}___"

    text = re.sub(
        r"```([a-zA-Z0-9_+#.-]*)\s*\n?(.*?)```",
        replace_code,
        text,
        flags=re.DOTALL
    )

    text = html.escape(text)

    for i, code in enumerate(blocks):
        text = text.replace(
            f"___XONI_CODE_{i}___",
            "<pre>" + html.escape(code) + "</pre>"
        )

    return text


def ask_ai(user_id, question):
    old = user_history.get(user_id, [])
    previous = ""

    for item in old[-MAX_HISTORY:]:
        previous += (
            "\nUSER:\n" + item["user"] +
            "\nXONI AI:\n" + item["assistant"] + "\n"
        )

    prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + XONI_PROFILE
        + "\n\nPREVIOUS CONVERSATION:\n"
        + previous
        + "\n\nCURRENT USER MESSAGE:\n"
        + question
    )

    try:
        start = time.time()
        r = requests.get(
            AI_API,
            params={"q": prompt},
            timeout=90
        )
        elapsed = time.time() - start

        if not r.ok:
            print("[AI HTTP]", r.status_code, r.text[:500])
            return None, elapsed

        try:
            data = r.json()
        except Exception:
            data = None

        answer = None

        if isinstance(data, dict):
            answer = (
                data.get("message")
                or data.get("response")
                or data.get("answer")
                or data.get("result")
                or data.get("text")
            )

        if isinstance(answer, dict):
            answer = (
                answer.get("message")
                or answer.get("response")
                or answer.get("text")
                or json.dumps(answer, ensure_ascii=False)
            )

        if not answer:
            answer = r.text

        answer = str(answer).strip()

        if not answer:
            return None, elapsed

        old.append({
            "user": question,
            "assistant": answer
        })
        user_history[user_id] = old[-MAX_HISTORY:]

        return answer, elapsed

    except Exception as e:
        print("[AI Error]", e)
        return None, 0


def status_message(chat_id, code_mode):
    text = (
        "💻 <b>Writing code...</b>"
        if code_mode
        else "🧠 <b>Thinking...</b>"
    )

    result = send_message(chat_id, text)

    if result and result.get("ok"):
        return result["result"]["message_id"]

    return None


def animate_status(chat_id, message_id, code_mode):
    if not message_id:
        return

    if code_mode:
        states = [
            "💻 <b>Writing code.</b>",
            "💻 <b>Writing code..</b>",
            "💻 <b>Writing code...</b>"
        ]
    else:
        states = [
            "🧠 <b>Thinking.</b>",
            "🧠 <b>Thinking..</b>",
            "🧠 <b>Thinking...</b>"
        ]

    for state in states:
        time.sleep(0.3)
        edit_message(chat_id, message_id, state)


def send_answer(chat_id, answer, elapsed, file_requested, reply_to=None):
    code = is_code_response(answer)

    # Explicit file request always wins.
    if file_requested:
        if code:
            content = extract_code(answer)
            language = detect_code_language(answer)
            ext = EXT.get(language, "txt")
            filename = f"xoni_code.{ext}"
            caption = (
                "💻 <b>Xoni AI Code</b>\n"
                f"Language: {html.escape(language)}\n"
                f"⚡ {elapsed:.2f}s"
            )
        else:
            content = answer
            filename = "xoni_response.txt"
            caption = (
                "📄 <b>Xoni AI Response</b>\n"
                f"⚡ {elapsed:.2f}s"
            )

        result = send_document(
            chat_id,
            content,
            filename,
            caption,
            reply_to
        )

        if result and result.get("ok"):
            return

        send_message(
            chat_id,
            "⚠️ File ပို့မရလို့ chat ထဲမှာပဲ ပြန်ပို့ပေးထားပါတယ်။",
            reply_to
        )

    # Long code automatically becomes source file.
    if code:
        content = extract_code(answer)

        if len(content) > MESSAGE_LIMIT:
            language = detect_code_language(answer)
            ext = EXT.get(language, "txt")

            result = send_document(
                chat_id,
                content,
                f"xoni_code.{ext}",
                (
                    "💻 <b>Xoni AI Code</b>\n"
                    f"Language: {html.escape(language)}\n"
                    f"⚡ {elapsed:.2f}s"
                ),
                reply_to
            )

            if result and result.get("ok"):
                return

        return send_message(
            chat_id,
            "<pre>" + html.escape(content) + "</pre>\n\n"
            f"⚡ Xoni AI • {elapsed:.2f}s",
            reply_to
        )

    # Long text automatically becomes TXT.
    if len(answer) > MESSAGE_LIMIT:
        result = send_document(
            chat_id,
            answer,
            "xoni_response.txt",
            f"📄 <b>Xoni AI Response</b> • ⚡ {elapsed:.2f}s",
            reply_to
        )

        if result and result.get("ok"):
            return

    return send_message(
        chat_id,
        format_response(answer)
        + f"\n\n<code>⚡ Xoni AI • {elapsed:.2f}s</code>",
        reply_to
    )


def process_ai(chat_id, user_id, question, reply_to=None):
    last_question[user_id] = question

    if is_image_request(question):
        prompt = extract_image_prompt(question)
        create_image(chat_id, prompt, reply_to)
        return

    code_mode = is_code_request(question)
    file_requested = is_file_request(question)

    status_id = status_message(
        chat_id,
        code_mode
    )

    typing(chat_id)

    animate_status(
        chat_id,
        status_id,
        code_mode
    )

    answer, elapsed = ask_ai(
        user_id,
        question
    )

    if status_id:
        delete_message(chat_id, status_id)

    if not answer:
        send_message(
            chat_id,
            "❌ <b>Xoni AI Error</b>\n\n"
            "AI server က response ပြန်မလာပါဘူး။ ခဏနေပြီး ပြန်စမ်းကြည့်ပါ။",
            reply_to
        )
        return

    send_answer(
        chat_id,
        answer,
        elapsed,
        file_requested,
        reply_to
    )


def handle_command(message, chat_id, user_id):
    text = message.get("text", "").strip()
    msg_id = message.get("message_id")

    if text.startswith("/start"):
        send_message(
            chat_id,
            "👋 <b>Welcome to Xoni AI</b>\n\n"
            "🧠 Gemini AI\n"
            "👤 Xoni Profile\n"
            "💻 Writing code\n"
            "📁 Send as file\n"
            "🎨 AI Image Creator\n"
            "📋 Copy-friendly code\n"
            "💬 Memory\n\n"
            "/help  /clear  /again"
        )
        return True

    if text.startswith("/image") or text.startswith("/img"):
        prompt = extract_image_prompt(text)
        create_image(chat_id, prompt, msg_id)
        return True

    if text.startswith("/help"):
        send_message(
            chat_id,
            "🛠 <b>Xoni AI Help</b>\n\n"
            "/start — Start\n"
            "/help — Help\n"
            "/image <prompt> — Create image\n"
            "/clear — Clear memory\n"
            "/again — Ask again\n\n"
            "🧠 Normal question → Thinking\n"
            "💻 Coding request → Writing code\n"
            "📁 send as file → File\n"
            "📋 Short code → Copy-friendly\n"
            "📁 Long code → Source file\n"
            "📄 Long text → TXT"
        )
        return True

    if text.startswith("/clear"):
        user_history.pop(user_id, None)
        last_question.pop(user_id, None)
        send_message(chat_id, "🧹 <b>Conversation cleared.</b>")
        return True

    if text.startswith("/again"):
        q = last_question.get(user_id)
        if not q:
            send_message(chat_id, "❌ No previous question found.")
        else:
            process_ai(chat_id, user_id, q, msg_id)
        return True

    return False


def group_text(message, text):
    chat_type = message.get("chat", {}).get("type")

    if chat_type == "private":
        return text

    if chat_type not in ("group", "supergroup"):
        return None

    mentioned = (
        BOT_USERNAME != "@YOUR_BOT_USERNAME"
        and BOT_USERNAME.lower() in text.lower()
    )

    reply = message.get("reply_to_message", {})
    sender = reply.get("from", {})

    replied_to_bot = (
        BOT_USERNAME != "@YOUR_BOT_USERNAME"
        and sender.get("username", "").lower()
        == BOT_USERNAME.replace("@", "").lower()
    )

    if not mentioned and not replied_to_bot:
        return None

    if BOT_USERNAME != "@YOUR_BOT_USERNAME":
        text = re.sub(
            re.escape(BOT_USERNAME),
            "",
            text,
            flags=re.IGNORECASE
        )

    return text.strip()


def get_updates(offset=None):
    params = {
        "timeout": 30,
        "limit": 100
    }

    if offset is not None:
        params["offset"] = offset

    try:
        return requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params=params,
            timeout=40
        ).json()
    except Exception as e:
        print("[Update Error]", e)
        return {"ok": False, "result": []}


def main():
    print("""
╔══════════════════════════════════════╗
║          XONI AI TELEGRAM BOT       ║
║                GEMINI               ║
╠══════════════════════════════════════╣
║ 🧠 Thinking                         ║
║ 💻 Writing code                     ║
║ 📁 Send as file                     ║
║ 🎨 AI Image Creator                 ║
║ 📋 Copy-friendly code               ║
║ 📄 Long text → TXT                  ║
║ 👤 Xoni profile                     ║
║ 💬 Conversation memory              ║
╚══════════════════════════════════════╝
""")

    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("❌ Set BOT_TOKEN first.")
        return

    offset = None

    while True:
        try:
            data = get_updates(offset)

            if not data.get("ok"):
                time.sleep(3)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")
                if not message:
                    continue

                chat_id = message.get("chat", {}).get("id")
                user_id = message.get("from", {}).get("id")
                text = message.get("text", "").strip()

                if not chat_id or not user_id or not text:
                    continue

                if text.startswith("/"):
                    if handle_command(message, chat_id, user_id):
                        continue

                text = group_text(message, text)

                if not text:
                    continue

                process_ai(
                    chat_id,
                    user_id,
                    text,
                    message.get("message_id")
                )

        except KeyboardInterrupt:
            print("\n🛑 Bot stopped.")
            break

        except Exception as e:
            print("[MAIN ERROR]", e)
            time.sleep(3)


if __name__ == "__main__":
    main()
