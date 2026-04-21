import discord
import requests
import json
import os

# ================= 설정 =================
TOKEN = "MTQ5NTE5NTA0MDMwNDMzNzAwNg.Go8UFn.Wa1_hJiq6weQv9HZKtiYYFP4lVmcVweewm7res"
API_KEY = "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"
OWNER_ID = 1328903687330070653  # 👈 너 ID

FILTER_FILE = "filter_words.json"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# ================= 금지어 =================
def load_filter():
    if not os.path.exists(FILTER_FILE):
        return []
    with open(FILTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_filter(words):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

filter_words = load_filter()

# ================= AI =================
def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    models = [
        "google/gemma-4-31b-it:free",
        "qwen/qwen3-coder:free",
        "minimax/minimax-m2.5:free",
        "nvidia/nemotron-3-nano-30b-a3b:freefh"
    ]

    last_error = None

    for model in models:
        try:
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            res = requests.post(url, headers=headers, json=data, timeout=20)

            if res.status_code != 200:
                last_error = res.text
                continue

            result = res.json()

            if "choices" in result:
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            last_error = str(e)
            continue

    return f"❌ 모든 모델 실패 / 마지막 오류: {last_error}"

# ================= 이벤트 =================
@client.event
async def on_ready():
    print(f"로그인됨: {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    global filter_words

    print("감지:", message.author, message.content)

    # ===== 금지어 추가 (너만 가능) =====
    if message.content.startswith("!금지어추가"):
        if message.author.id != OWNER_ID:
            await message.channel.send("❌ 너는 못함")
            return

        word = message.content.replace("!금지어추가", "").strip()

        if not word:
            await message.channel.send("단어 써")
            return

        if word not in filter_words:
            filter_words.append(word)
            save_filter(filter_words)
            await message.channel.send(f"'{word}' 추가됨")
        else:
            await message.channel.send("이미 있음")
        return

    # ===== 금지어 목록 =====
    if message.content.startswith("!금지어목록"):
        if message.author.id != OWNER_ID:
            return

        if filter_words:
            await message.channel.send(", ".join(filter_words))
        else:
            await message.channel.send("없음")
        return

    # ===== 멘션 or 답장 감지 =====
    is_mention = client.user.mentioned_in(message)
    is_reply = False

    if message.reference:
        try:
            ref_msg = await message.channel.fetch_message(message.reference.message_id)
            if ref_msg.author == client.user:
                is_reply = True
        except:
            pass

    if is_mention or is_reply:
        user_input = message.content

        # 멘션 제거
        user_input = user_input.replace(f"<@{client.user.id}>", "")
        user_input = user_input.replace(f"<@!{client.user.id}>", "")
        user_input = user_input.strip()

        # ===== 금지어 필터 =====
        for word in filter_words:
            if word in user_input:
                return  # 무음 처리

        if not user_input:
            await message.channel.send("질문 써")
            return

        reply = ask_ai(user_input)
        await message.channel.send(reply[:1900])

# ================= 실행 =================
client.run(TOKEN)