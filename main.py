import requests
from bs4 import BeautifulSoup as bs4
import pyaudio
import pyopenjtalk
import numpy as np
from scipy.io import wavfile
import json

def get_history():
        # 西之表市防災ラジオ配信履歴のURL
        url = "http://www.city.nishinoomote.lg.jp/cgi-bin/smart_alert.php/2/list"
        # ページの内容を取得
        response = requests.get(url)
        # ページの内容をBeautiful Soupで解析
        soup = bs4(response.text, 'html.parser')
        [tag.extract() for tag in soup(string='n')]
        # class="alert-history-list"の要素を取得
        history_div = soup.find_all(class_="alert-history-list")
        # alert-history-listの中のli要素を取得
        history_page = history_div[0].find_all(class_="page")
        # 配信履歴のリストを作成
        history_list = []
        # history_liの中のa要素からタイトルとURLを取得
        for li in history_page:
                a = li.find("a")
                history_list.append({"title": a.get_text(), "url": a.get("href")})

        return history_list

def get_content(history):
        # 配信内容のリストを作成
        content_list = []
        # リスト内の配信履歴のURLから配信内容を取得
        for h in history:
                # ページの内容を取得
                response = requests.get(h["url"])
                # ページの内容をBeautiful Soupで解析
                soup = bs4(response.text, 'html.parser')
                # class="detail-main"の要素を取得
                content = soup.find(class_="detail-main")
                # 配信内容を取得
                content_list.append({"id": h["url"], "content": content.get_text().lstrip('　 、')}) # type: ignore
        return content_list

def read_text(text, data):
        for t in text:
                if t["id"] in data["id"]:
                        continue
                # 読み上げ済みの配信内容を保存
                data = update_data(data, t["id"])
                print("読み上げ中: " + t["content"])
                # pyopenjtalkの音声合成
                x, sr = pyopenjtalk.tts(t["content"])
                # 音声を再生
                p = pyaudio.PyAudio()
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=sr, output=True)
                stream.write(x.astype(np.int16).tobytes())
                stream.close()
                p.terminate()
                # 音声を保存
                wavfile.write("latest.wav", sr, x.astype(np.int16))

def load_data(filename):
        try:
                with open(filename, 'r') as file:
                        return json.load(file)
        except FileNotFoundError:
                return {}  # ファイルがない場合は空の辞書を返す
        except json.JSONDecodeError:
                return {}  # JSONのパースエラーがあった場合も空の辞書を返す

def update_data(data, item_id):
        if 'id' not in data:
                data['id'] = []
        
        if item_id not in data['id']:
                data['id'].append(item_id)
        return data

def save_data(data, filename):
        with open(filename, 'w') as file:
                json.dump(data, file, indent=4)

def main():
        # 読み上げ済みの配信内容を保存するファイルを読み込み
        read_list = load_data("read.json")
        # 配信履歴を取得
        history = get_history()
        # 配信内容を取得
        contents = get_content(history)
        # 未読の配信内容を読み上げ
        read_text(contents, read_list)
        # 読み上げた配信内容を保存
        save_data(read_list, "read.json")

if __name__ == "__main__":
        main()