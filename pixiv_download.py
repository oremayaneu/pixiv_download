import sys
from pixivpy3 import AppPixivAPI
import time
from time import sleep
from PIL import Image
import os, glob
from tqdm import tqdm
import shutil
import datetime

USER_ID = 12345 #あなたのIDへ書き換え

# 保存先フォルダの作成
if not os.path.exists("./pixiv_images"):
    os.mkdir("./pixiv_images")

# login
api = AppPixivAPI()
api.auth(refresh_token='あなたのtokenへ書き換え')

# ブックマークした画像のjsonを取得
users_data = api.user_bookmarks_illust(USER_ID, restrict='public')
# なぜかAPIが30枚分の情報しかとってこないので30枚ごとを確認する変数
count = 1
# 全体の画像の枚数をカウントする変数
count_i = 1



def downloadImage(users_data, count, count_i):
    # イラストの数だけ繰り返す
    ilustNum = len(users_data.illusts)
    for illust in users_data.illusts[:ilustNum]:
        author = illust.user.name.replace("/", "-")

        # 履歴の中に重複があれば以降も重複するため終了
        with open('./pixiv_done.txt', 'r', newline='') as f:
            lines = f.readlines()
            for line in lines:
                if line.find(str(illust.image_urls.large)) >= 0:
                    print("以降保存済")
                    sys.exit()

        # 削除された作品を避ける
        if ("limit_unknown_360" in str(illust.image_urls.large)) == True:
            count += 1
        # 非公開に変更された作品を避ける
        elif ("limit_mypixiv_360" in str(illust.image_urls.large)) == True:
            count += 1
        else:
            #画像かうごイラか判定

            #ここから画像
            if illust.type == "illust":

                # ダウンロードフォルダなかったら作る
                if not os.path.exists("./pixiv_images/" + author):
                    os.mkdir("./pixiv_images/" + author)

                # 保存先の指定
                savepath = "./pixiv_images/" + author

                # 保存
                print(str(count_i) + "枚目: 画像 " + str(author)+"  " + str(illust.title))

                # 1枚のイラスト
                if illust.page_count == 1:
                    api.download(illust.image_urls.large, path = savepath)
                    sleep(1)
                # 複数枚のイラスト
                else:
                    for page in tqdm(illust.meta_pages):
                        # 開始
                        start_time = time.perf_counter()

                        api.download(page.image_urls.original, path = savepath)
                        # 終了
                        end_time = time.perf_counter()
                        # 経過時間を出力(秒)
                        elapsed_time = end_time - start_time
                        # 1sに満たないループはグレーゾーンなので足りない時間だけ待機
                        if elapsed_time < 1.05:
                            t = 1.05 - elapsed_time
                            sleep(t)
                count += 1
                count_i += 1

            # ここから漫画
            if illust.type == "manga":

                # ダウンロードフォルダなかったら作る
                if not os.path.exists("./pixiv_images/" + author):
                    os.mkdir("./pixiv_images/" + author)

                # 保存先の指定
                savepath = "./pixiv_images/" + author

                # 保存
                print(str(count_i) + "枚目: 画像 " + str(author)+"  " + str(illust.title))
    
                for page in tqdm(illust.meta_pages):
                        # 開始
                        start_time = time.perf_counter()

                        api.download(page.image_urls.original, path = savepath)
                        # 終了
                        end_time = time.perf_counter()
                        # 経過時間を出力(秒)
                        elapsed_time = end_time - start_time
                        if elapsed_time < 1.05:
                            t = 1.05 - elapsed_time
                            sleep(t)
                count += 1
                count_i += 1

            # ここからうごイラ
            elif illust.type == "ugoira":
                # うごイラのリンクを取得
                u = str(illust.image_urls.large)
                # 余計な部分を省いてイラストIDを数値で取得
                u = u.replace('https://i.pximg.net/c/600x1200_90_webp/img-master/img/', '')
                u = u.replace('_master1200.jpg', '')
                ugoira_id = int(u[20:])

                illust_u = api.illust_detail(ugoira_id)
                ugoira_url = illust_u.illust.meta_single_page.original_image_url.rsplit('0', 1)
                ugoira = api.ugoira_metadata(ugoira_id)
                ugoira_frames = len(ugoira.ugoira_metadata.frames)
                ugoira_delay = ugoira.ugoira_metadata.frames[0].delay
                ugoira_picture = './pixiv_ugoira/pictures'

                # うごイラの画像を保存するフォルダの作成
                if not os.path.isdir(ugoira_picture):
                    os.mkdir(ugoira_picture)

                # ダウンロードフォルダなかったら作る
                if not os.path.exists("./pixiv_ugoira/" + author):
                    os.mkdir("./pixiv_ugoira/" + author)

                print(str(count_i)+"枚目: うごイラ "+ str(author)+"  " + str(illust_u.illust.title))

                # ダウンロードした画像を格納する配列
                images = []

                #うごイラに使われているすべての画像のダウンロード
                for frame in tqdm(range(ugoira_frames)):
                    # 開始
                    start_time = time.perf_counter()

                    frame_url = ugoira_url[0] + str(frame) + ugoira_url[1]
                    api.download(frame_url, path=ugoira_picture)
                    # 終了
                    end_time = time.perf_counter()
                    # 経過時間を出力(秒)
                    elapsed_time = end_time - start_time
                    if elapsed_time < 1.05:
                        t = 1.05 - elapsed_time
                        sleep(t)

                    # 格納
                    im = Image.open(ugoira_picture + '/' + str(ugoira_id) + '_ugoira' + str(frame) + ugoira_url[1])
                    images.append(im)

                # 保存先の指定
                savepath = "./pixiv_ugoira/" + author

                # 保存
                images[0].save(savepath+'/'+str(ugoira_id)+'.gif' , save_all = True , append_images = images[1:] , optimize=False , duration = ugoira_delay , loop = 0)
                
                # gifが生成できたら画像は不要なのでフォルダごと削除
                shutil.rmtree(ugoira_picture)

                count += 1
                count_i += 1


            # 履歴に追加
            f = open('./pixiv_done.txt','a')
            f.write(str(illust.image_urls.large) + " \n")
            f.close()

        # 30回目以降
        if count > 30:
            next_url = users_data.next_url
            next_qs = api.parse_qs(next_url)
            # users_dataに30以降のjsonデータを再代入
            users_data = api.user_bookmarks_illust(**next_qs)
            count = 1
            downloadImage(users_data, count, count_i)


# 古い履歴の削除
with open('./pixiv_done.txt') as f:
    lines = f.readlines()
lines_strip = [line.strip() for line in lines]
x = [i for i, line in enumerate(lines_strip) if '年' in line]
n = len(x)
if n>3:
    content = lines[x[n-3]:]
    with open('./pixiv_done.txt', 'w') as f:
        for i in range(len(content)):
            f.write(str(content[i]))


# 現在時刻
dt_now = datetime.datetime.now()
# 履歴に追加
f = open('./pixiv_done.txt','a')
f.write(str(dt_now.strftime('%Y年%m月%d日 %H:%M:%S')) + " \n")
f.close()


downloadImage(users_data, count, count_i)


print("ダウンロード終了")