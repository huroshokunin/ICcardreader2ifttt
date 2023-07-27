from __future__ import print_function  # プリント関数を使用するためのimport文
import json  # JSON形式でデータを扱うためのimport文
import urllib.request  # URLからデータを取得するためのimport文
import datetime  # 日付・時刻を扱うためのimport文
import time  # 時間を扱うためのimport文
from ctypes import *  # C言語とPythonを接続するためのimport文

# iftttのwebhookキー
KEY = 'hoge'

# FeliCaカードのIDmの値
# 0xffff全て探索
FELICA_POLLING_ANY = 0xffff

# FelicaBlockInfo構造体の定義
# C言語のstructと同等の役割
class FelicaBlockInfo(Structure):
    _fields_ = [
        ("service", c_uint16),
        ("mode", c_uint8),
        ("block", c_uint16)
    ]

# IFTTTにPOSTリクエストを送信するための関数
def sendifttt(balance: int) -> None:
    dt_now = datetime.datetime.now()  # 現在時刻を取得
    value1 = balance  # POSTするデータのvalue1に残高を代入
    value2 = dt_now.strftime('%Y/%m/%d %H:%M:%S')  # POSTするデータのvalue2に現在時刻を代入
    url = f'https://maker.ifttt.com/trigger/RP-posted/with/key/{KEY}'  # IFTTTのURL
    data = {'value1': value1, 'value2': value2}  # POSTするデータ
    headers = {'Content-Type': 'application/json'}  # ヘッダー情報
    rq = urllib.request.Request(url, json.dumps(data).encode(), headers)
    
    try:
        with urllib.request.urlopen(rq) as rs:
            body = rs.read()
    # iftttに送信失敗した際のエラーコード送信
    except urllib.error.HTTPError as err:
        print('HTTP Error', err.code)
    except urllib.error.URLError as err:
        print('URL Error', err.reason)


# main関数
# https://github.com/rfujita/libpafe by rfujita
if __name__ == '__main__':
    libpafe = cdll.LoadLibrary("/usr/local/lib/libpafe.so")  # pafeライブラリを読み込む
    libpafe.pasori_open.restype = c_void_p  # pasori_open()関数の戻り値がvoidポインタ型であることを設定
    pasori = libpafe.pasori_open()  # PaSoRiをオープン
    libpafe.pasori_init(pasori)  # PaSoRiの初期化
    times = 0
    
    while True:
        # felica_polling()関数の戻り値がvoidポインタ型であることを設定
        libpafe.felica_polling.restype = c_void_p
        felica = libpafe.felica_polling(
            pasori, FELICA_POLLING_ANY, 0, 0)  # Felicaカードを検索
        time.sleep(1)  # 1秒待機
        times += 1
        if times == 5:  # 5回検索してもカードが見つからない場合は終了
            break
        if not felica:
            continue
        break

    int_array16 = c_uint8 * 16  # 16個の8bit整数型の配列を作成
    data = int_array16()  # 配列dataを初期化
    info = FelicaBlockInfo(
        c_uint16(0x090f),
        c_uint8(0),
        c_uint16(0))  # FeliCaブロック情報を設定

    for i in range(32):
        c_i = c_int(i)
        libpafe.felica_read(
            felica, byref(c_i), byref(info), byref(data))  # Felicaカードのデータを読み込む
        if data[1] > 0 or data[2] > 0:  # 残高データが存在する場合
            ICbalance = (data[11] << 8) + data[10]  # 残高データを計算
            print(f"Balance: {ICbalance} yen")  # 残高データを表示
            sendifttt(ICbalance)  # IFTTTにPOSTリクエストを送信
            break

    libpafe.free(felica)  # Felicaカードのメモリを解放
    libpafe.pasori_close(pasori)  # PaSoRiをクローズ
