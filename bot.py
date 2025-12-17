# ----------------------------------------------------
# ⚠️ Render/本番環境向け修正 ⚠️
# Colabの 'google.colab' から標準の 'os.getenv' に戻します。
# ----------------------------------------------------

import discord
import os
import json
import requests
# Colabで使用した from google.colab import userdata は削除またはコメントアウト
from dotenv import load_dotenv # .envファイル（ローカルテスト用）の読み込みに必要

import aiohttp
import asyncio
# import nest_asyncio は Renderでは不要なので削除 (Colabのループ競合回避用だったため)

# --- 1. 環境変数の読み込み (Renderの環境変数設定を使用) ---
# load_dotenv() # Renderは環境変数を直接読み込むため、これも不要だが残していても問題なし
TOKEN = os.getenv('DISCORD_BOT_TOKEN') # ★★★ 修正箇所 ★★★
GAS_URL = os.getenv('GAS_WEBHOOK_URL') # ★★★ 修正箇所 ★★★

# ... (中略：Botの定義、on_ready, on_message関数はそのまま) ...

# ----------------------------------------------------
# ⚠️ Render/本番環境向け修正 ⚠️
# Colabの nest_asyncio と try/except ブロックはすべて削除
# ----------------------------------------------------


# --- 1.5. トークン設定のチェック ---
if TOKEN is None or GAS_URL is None:
    print("❌ 致命的なエラー: DISCORD_BOT_TOKEN または GAS_WEBHOOK_URL が Colab の Secret に設定されていません。")
    # 設定がなければ、ここでプログラムを停止します。
    raise ValueError("トークンまたはGAS URLが未設定です。ColabのSecretを確認してください。")

# --- 2. Discord Client の設定 ---
intents = discord.Intents.default()
# サーバーでメッセージ内容を読み取るために必須の設定です。
# Discord Developer Portalで「MESSAGE CONTENT INTENT」をオンにしている必要があります。
intents.message_content = True 

# ★★★ 最適化箇所1: シンプルなクライアント初期化 ★★★
# Crostiniでのネットワーク回避策（aiohttp.TCPConnector, CustomSession）は全て削除
client = discord.Client(intents=intents)


# Botが起動したとき
@client.event
async def on_ready():
    print(f'✅ ログインしました: {client.user} (ID: {client.user.id})')
    print(f'GAS送信先URL: {GAS_URL}')
    print('--- Bot稼働開始 ---')

# Botがメッセージを受け取ったとき
@client.event
async def on_message(message):
    # Bot自身の発言は無視する（無限ループ防止）
    if message.author == client.user:
        return

    # 1. GASに送信するデータ（ペイロード）を作成
    payload = {
        "username": message.author.display_name,
        "channel_name": message.channel.name,
        "content": message.content
    }

    # 2. ヘッダーを設定
    headers = {
        "Content-Type": "application/json"
    }

    print(f"GASへデータを送信中: {payload['content']}")

    # 3. GASのURLへPOSTリクエストを送信
    try:
        # Colab環境ではSSL検証は正常に機能するため、verify=Trueに戻すか、省略します。
        response = requests.post(GAS_URL, 
                                 data=json.dumps(payload), 
                                 headers=headers) # verify=True は省略可
        
        # GASからの応答を確認
        if response.status_code == 200:
            print("✅ データはGAS経由でスプレッドシートに正常に記録されました。")
        else:
            print(f"❌ GASへの送信失敗。ステータスコード: {response.status_code}")
            print(f"応答内容: {response.text}")

    except Exception as e:
        print(f"💣 データ送信中にエラーが発生しました: {e}")


# ----------------------------------------------------
# ★★★ 最適化箇所2: Colab/Jupyter環境での実行用設定 ★★★
# ----------------------------------------------------
# 既存のイベントループとの競合（RuntimeError）を回避するために必須です。

import nest_asyncio
# nest_asyncio のインポートは、最初にpip installしている必要があります。
# !pip install nest_asyncio を実行していない場合は、最初に行ってください。
nest_asyncio.apply() 

print("Botを実行します。停止するにはこのセルの実行を中断してください (■ボタン)。")

try:
    # Colab環境では run() を使います。
    client.run(TOKEN)
except KeyboardInterrupt:
    print("Botを停止しました。")
except Exception as e:
    print(f"致命的なエラーが発生しました: {e}")
