import math  
import os  
import random  
import sys  
import time  
import pygame as pg  


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
GROUND_Y = int(HEIGHT * 0.8)  #地面の高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:  
    """  
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数  
    引数：こうかとんや爆弾，ビームなどのRect  
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）  
    """  
    yoko, tate = True, True  
    if obj_rct.left < 0 or WIDTH < obj_rct.right:  
        yoko = False  
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:  
        tate = False  
    return yoko, tate  


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:  
    """  
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す  
    引数1 org：爆弾SurfaceのRect  
    引数2 dst：こうかとんSurfaceのRect  
    戻り値：orgから見たdstの方向ベクトルを表すタプル  
    """  
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery  
    norm = math.sqrt(x_diff**2+y_diff**2)  
    return x_diff/norm, y_diff/norm  


class Bird(pg.sprite.Sprite):  
    """  
    ゲームキャラクター（こうかとん）に関するクラス  
    """  
    delta = {  # 押下キーと移動量の辞書  
        pg.K_UP: (0, -1),  
        pg.K_DOWN: (0, +1),  
        pg.K_LEFT: (-1, 0),  
        pg.K_RIGHT: (+1, 0),  
    }  

    def __init__(self, num: int, xy: tuple[int, int]):  
        """  
        こうかとん画像Surfaceを生成する  
        引数1 num：こうかとん画像ファイル名の番号  
        引数2 xy：こうかとん画像の位置座標タプル  
        """  
        super().__init__()  
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)  
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん  
        self.imgs = {  
            (+1, 0): img,  # 右  
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上  
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上  
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上  
            (-1, 0): img0,  # 左  
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下  
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下  
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下  
        }  
        self.dire = (+1, 0)  
        self.image = self.imgs[self.dire]  
        self.rect = self.image.get_rect()  
        self.rect.center = xy  
        self.speed = 10  
        # --- 追加ここから ---
        self.is_invincible = False  # 無敵状態かどうかのフラグ
        self.invincible_timer = 0    # 無敵時間のタイマー
        # --- 追加ここまで ---

        self.vx = 0  # 横方向速度
        self.vy = 0  # 縦方向速度（ジャンプや重力）
        self.on_ground = False #接地フラグ
        self.jump_requested = False  # ジャンプリクエスト
        self.gravity = 1  # 重力加速度
        self.jump_power = -20  # ジャンプ時の初速
        self.on_ground = False  # 地面に接しているかどうかのフラグ

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        # 横移動
        self.vx = 0
        if key_lst[pg.K_LEFT]:
            self.vx = -self.speed
            self.dire = (-1, 0)
        if key_lst[pg.K_RIGHT]:
            self.vx = +self.speed
            self.dire = (+1, 0)

        # ジャンプ（地面にいる時のみ）
        if self.jump_requested and self.on_ground:
            self.vy = -15  # 上向きジャンプ
            self.on_ground = False
        self.jump_requested = False  # リクエストは使い切る

        # 重力適用
        self.vy += 1  # 重力
        self.rect.y += self.vy


        # 位置更新
        self.rect.x += self.vx
        self.rect.y += self.vy

        # 地面との接地判定
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vy = 0
            self.on_ground = True

        # 画面外制限（左右のみ）
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

        self.image = self.imgs.get(self.dire, self.image)
        # screen.blit(self.image, self.rect) 
        
        # --- 追加ここから ---
        # 無敵時間の処理
        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False
                # 無敵解除時の画像に戻す（任意で元の方向の画像に戻しても良い）
                self.image.set_alpha(255) # 不透明に戻す
            else:
                # 無敵中の点滅表現 (任意)
                if self.invincible_timer % 10 < 5: # 10フレームごとに半透明と不透明を切り替え
                    self.image.set_alpha(100) # 半透明にする
                else:
                    self.image.set_alpha(255) # 元に戻す
        else:
            self.image.set_alpha(255) # 無敵でないときは常に不透明
        # --- 追加ここまで ---

        screen.blit(self.image, self.rect)  


class Bomb(pg.sprite.Sprite):  
    """  
    爆弾に関するクラス  
    """  
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]  

    def __init__(self, emy: "Enemy", bird: Bird, large = False):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = 70 if large else random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = (255, 0, 0)
        # self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx  
        self.rect.centery = emy.rect.centery+emy.rect.height//2  
        self.speed = 6  

    def update(self):  
        """  
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる  
        引数 screen：画面Surface  
        """  
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)  
        if check_bound(self.rect) != (True, True):  
            self.kill()  

class Flame(pg.sprite.Sprite):
    """
    Flameクラス：
    ・警告（半透明赤) → 一時的に非表示  → 攻撃（不透明赤） → 消える
    """
    def __init__(self, x: int):
        super().__init__()
        self.image = pg.Surface((20, HEIGHT), pg.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = 0
        self.mode = "warning"
        self.warn_timer = 90  # 各状態表示時間
        self.pause_timer = 30
        self.attack_timer = 120

    def update(self):
        if self.mode == "warning":  # 警告状態
            self.image.fill((255, 0, 0, 100))  # 半透明赤
            self.warn_timer -= 1
            if self.warn_timer <= 0:
                self.mode = "pause"

        elif self.mode == "pause":  #　攻撃前状態
            self.image.fill((0, 0, 0, 0))  # 完全に透明
            self.pause_timer -= 1
            if self.pause_timer <= 0:
                self.mode = "attack"

        elif self.mode == "attack":  # 攻撃状態
            self.image.fill((255, 0, 0, 255))  # 不透明赤
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.kill()

    @property
    def active(self):
        return self.mode == "attack"


class Beam(pg.sprite.Sprite):  
    """  
    ビームに関するクラス  
    """  
    def __init__(self, bird: Bird):  
        """  
        ビーム画像Surfaceを生成する  
        引数 bird：ビームを放つこうかとん  
        """  
        super().__init__()  
        self.vx, self.vy = bird.dire  
        angle = math.degrees(math.atan2(-self.vy, self.vx))  
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)  
        self.vx = math.cos(math.radians(angle))  
        self.vy = -math.sin(math.radians(angle))  
        self.rect = self.image.get_rect()  
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy  
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx  
        self.speed = 10  

    def update(self):  
        """  
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる  
        引数 screen：画面Surface  
        """  
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)  
        if check_bound(self.rect) != (True, True):  
            self.kill()  


class Explosion(pg.sprite.Sprite):  
    """  
    爆発に関するクラス  
    """  
    def __init__(self, obj: "Bomb|Enemy", life: int):  
        """  
        爆弾が爆発するエフェクトを生成する  
        引数1 obj：爆発するBombまたは敵機インスタンス  
        引数2 life：爆発時間  
        """  
        super().__init__()  
        img = pg.image.load(f"fig/explosion.gif")  
        self.imgs = [img, pg.transform.flip(img, 1, 1)]  
        self.image = self.imgs[0]  
        self.rect = self.image.get_rect(center=obj.rect.center)  
        self.life = life  

    def update(self):  
        """  
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで  
        爆発エフェクトを表現する  
        """  
        self.life -= 1  
        self.image = self.imgs[self.life//10%2]  
        if self.life < 0:  
            self.kill()  

    
class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    地面に接地した状態で画面右側から出現
    """
    enemy_imgs = [
        pg.image.load(f"fig/devil1.png"),
        pg.image.load(f"fig/devil4.png")
    ]
    imgs = [
        pg.transform.scale(img, (int(img.get_width() * 0.3), int(img.get_height() * 0.3)))
        for img in enemy_imgs
    ]

    def __init__(self):
        super().__init__()
        self.image = random.choice(Enemy.imgs)
        self.rect = self.image.get_rect()

        # 画面右端から出現、地面と接地
        self.rect.right = WIDTH
        self.rect.bottom = GROUND_Y

        self.vx, self.vy = -5, 0  # 左向きに移動（右から左へ）
        self.target_x = random.randint(WIDTH // 2, WIDTH - 100)  # 停止するX座標
        self.state = "move"  # 移動中か停止中かの状態
        self.interval = random.randint(50, 300)  # 爆弾投下間隔
        self.frame = 0

    def update(self):
        self.frame += 1

        # アニメーション
        old_pos = self.rect.topleft  # 現在の位置を保持
        self.image = Enemy.imgs[(self.frame // 15) % 2]
        self.rect = self.image.get_rect(topleft=old_pos)  # 同じ位置に画像を差し替え

        # 停止条件
        if self.rect.left <= self.target_x:
            self.vx = 0
            self.state = "stop"

        self.rect.move_ip(self.vx, self.vy)



class Result:
    """
    リザルト画面を表示するクラスです
    """
    def __init__(self, player_hp, boss_hp):
        """
        プレイヤーのhpとボスのhpを初期化します。
        引数 player_hp, boss_hp: プレイヤーのhpとボスのhp(リアルタイム)
        """
        self.bg_black = pg.Surface((WIDTH, HEIGHT))
        self.bg_black.set_alpha(100)
        self.player_hp = player_hp
        self.boss_hp = boss_hp
        
    def update(self, screen, bird, score):
        """
        毎フレームhpを確認します。
        引数 screen:画面のsurface, bird:主人公のクラス, score:スコアを表示するクラス
        戻り値:Trueならゲーム終了。Falseならばゲーム続行。
        """
        if self.player_hp<=0:
            screen.blit(self.bg_black, [0,0])#背景　ブラックスクリーン描画_New
            # self.screen.blit(self.bg_black, [0,0])#背景　ブラックスクリーン描画
            # ゲームオーバー時に，こうかとん画像を切り替え，5秒間表示させる
            bird.change_img(8, screen)
            #ゲームオーバー文字列を表示。フォントを怖いのにする
            fonto = pg.font.SysFont("hg正楷書体pro",200)

            # fonto = pg.font.Font(None, 80)
            txt1 = fonto.render("Score:"+str(score.value), True, (255, 0, 0))
            txt2 = fonto.render("Game Over", True, (255, 0, 0))
            screen.blit(txt1, [WIDTH//2-450, HEIGHT//2])
            screen.blit(txt2, [WIDTH//2-550, HEIGHT//2-200])
            pg.display.update()
            time.sleep(5)  #5秒間主人公泣いてる result用。
            return True
        
        

        elif self.boss_hp<=0:
            screen.blit(self.bg_black, [0,0])#背景　ブラックスクリーン描画
            #　ボス撃破時に,主人公画像を切り替え、5秒間表示させる
            bird.change_img(6, screen)
            #勝利文字列を表示するためにフォントをかっこいいのにする
            fonto = pg.font.SysFont("AdobeGothicStdKalin",200)


            #一行で勝利後の結果を表示する場合
            # txt = fonto.render("Congratulations!! You win!! Yourscore:"+str(score.value), True, (255, 255, 0))
            # screen.blit(txt, [WIDTH//2-550, HEIGHT//2])
        

            #3行使って勝利後の結果を表示する場合。
            txt1 =fonto.render("Congratulations", True, (255, 255, 0))
            txt2 = fonto.render("You win!! " ,True, (255, 255, 0))
            txt3 = fonto.render("Yourscore :  "+str(score.value),True, (255, 255, 0))
            screen.blit(txt1, [WIDTH//2-550, HEIGHT//2-100])
            screen.blit(txt2, [WIDTH//2-550, HEIGHT//2+50])
            screen.blit(txt3, [WIDTH//2-550, HEIGHT//2+200])

            pg.display.update()
            time.sleep(5)  #5秒間主人公喜んでる result
            return True
        return False
        

class Boss(pg.sprite.Sprite):
    """
    ボスキャラクターのクラス。
    """
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/BOSS.png"), 0, 0.2)
        self.rect = self.image.get_rect(center=(WIDTH//2, -100))
        self.maxhp = 50  # ボスHP
        self.hp = self.maxhp
        self.attack_timer = 0
        self.state = "enter"  # 画面外から登場。初期状態
        self.attack_pattern = random.choice(["bombing", "flame", "cannon"])  # ボスの攻撃パターん
        self.direction = 1  # 横移動方向
        self.bomb_cooldown = 0  # 爆弾のタイマー
        self.flame_timer = 0
        self.flame = []  # flameの攻撃座標リスト
        self.ascending = True  # boming攻撃上昇中か確認
        self.repeat_bomb= 0

    def update(self, bird: Bird, bombs: pg.sprite.Group, flames: pg.sprite.Group):
        if self.state == "enter":
            if self.rect.right <= WIDTH:
                self.rect.center = (WIDTH - 100, HEIGHT // 2 + 50)  # 画面右側座標
                self.state = "idle"
        elif self.state == "idle":  # 攻撃のクールダウン
            self.attack_timer += 1
            if self.attack_timer > 100:  # idle移行後100フレームたったら
                self.attack_pattern = random.choice(["bombing", "flame", "cannon"])  # ３種の攻撃からランダムに選択
                self.attack_timer = 0
                self.bomb_cooldown = 0
                self.state = self.attack_pattern
        elif self.state == "bombing":  # 一定上昇後、横移動しながら一定間隔でbombを落とす
            if self.ascending:  # 上昇
                self.rect.centery -= 2
                if self.rect.centery < HEIGHT // 4:
                    self.ascending = False
            else:
                if self.bomb_cooldown % 50 == 0 and self.repeat_bomb < 5:  # 50フレームごとに爆弾
                    bombs.add(Bomb(self, bird))
                    self.repeat_bomb += 1
                self.bomb_cooldown += 1
                self.rect.move_ip(-4 * self.direction, 0)
                if self.rect.left <= 0 or self.rect.right >= WIDTH:  # 左端に届いたら元に戻る
                    self.direction *= -1
                    self.state = "return"
        elif self.state == "flame":  # ３か所に警告後数秒後にflameクラスの攻撃
            if not self.flame:
                for _ in range(3):
                    x = random.randint(0, WIDTH - 20)
                    self.flame.append(x)  #　ランダムなx座標を選択リストに追加
                self.flame_warn_timer = 60  #　警告時間
            elif self.flame_warn_timer > 0:
                self.flame_warn_timer -= 1
            else:
                for x in self.flame:
                    flames.add(Flame(x))
                self.state = "return"
        elif self.state == "cannon":  # 大きなbombをプレイヤー方向に１つ発射
            b = Bomb(self, bird, large = True)  # 爆弾サイズをTrueの攻撃だけ固定化
            b.rect.center = (self.rect.centerx, self.rect.centery)
            bombs.add(b)
            self.state = "return"
        elif self.state == "return":  # 初期位置に戻る
            self.rect.center = (WIDTH - 100,HEIGHT // 2 + 50)
            self.state = "idle"  #　攻撃大気に移行
            self.flame = []  #　攻撃座標のリセット
            self.ascending = True  # 上昇状態を初期化
            self.repeat_bomb = 0  # boming攻撃のリセット

    def draw_hp(self, screen):  # bossのhp表記
        bar_width = 400  # 横幅
        hp = self.hp / self.maxhp
        pg.draw.rect(screen, (0, 0, 0),(298, 8, bar_width+4, 24))  #黒い枠
        pg.draw.rect(screen, (255, 0, 0), (300, 10, bar_width*hp, 20))
        font = pg.font.Font(None, 36)
        label = font.render("BOSS", True, (255, 0, 0))
        screen.blit(label, ( 220, 10))



class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):  
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)  
        screen.blit(self.image, self.rect)  





def main():
    pg.display.set_caption("HeroShooter")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.transform.rotozoom(pg.image.load(f"fig/22823124.jpg"),0, 1.1)
    screen.blit(bg_img, [0, 0])
    score = Score()

   


    bird = Bird(3, (900, GROUND_Y - 50))

    # 編集必須
    result = Result(player_hp=1, boss_hp=1)

    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    bosses = pg.sprite.Group()
    flames = pg.sprite.Group()


    #仮です。result画面用です。
     #ゲームオーバー画面用画像の追加(簡単に呼び出せるように)
    # crying_kk_img = pg.image.load("fig/8.png")
    
    # screen.blit(crying_kk_img, [300, 200])
    #仮です。result画面用です。
    


    tmr = 0
    clock = pg.time.Clock()
    boss_mode = False
    boss_spawned = False
     
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                if event.key == pg.K_UP:
                    bird.jump_requested = True  #ジャンプリクエストは押された瞬間のみ
                # --- 追加ここから ---
                if event.key == pg.K_RETURN:  # エンターキーが押されたら
                    # スコアが100以上、かつ無敵状態ではない場合のみ発動
                    if score.value >= 100 and not bird.is_invincible:
                        score.value -= 100  # 100ポイント消費
                        bird.is_invincible = True  # 無敵状態にする
                        bird.invincible_timer = 300 # 無敵時間を300フレームに設定 (約6秒)
                # --- 追加ここまで ---

        screen.blit(bg_img, [0, 0])

        if tmr == 500 and not boss_spawned:  # tmrフレーム後に赤い警告をだし、ボス登場
            red_overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
            red_overlay.fill((255, 0, 0, 100))  #赤画面
            bg_img = pg.transform.rotozoom(pg.image.load(f"fig/22828803.jpg"),0, 1.1)  # 背景の切り替え
            for _ in range(10):
                screen.blit(bg_img, [0, 0])
                screen.blit(red_overlay, [0, 0])
                pg.display.update()
                time.sleep(0.1)
            emys.empty()
            boss = Boss()
            bosses.add(boss)
            boss_mode = True
            boss_spawned = True

        if not boss_mode and tmr % 200 == 0:
            emys.add(Enemy())

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる  
            emys.add(Enemy())  

        for emy in emys:  
            if emy.state == "stop" and tmr%emy.interval == 0:  
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下  
                bombs.add(Bomb(emy, bird))  

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト  
            exps.add(Explosion(emy, 100))  # 爆発エフェクト  
            score.value += 10  # 10点アップ  
            bird.change_img(6, screen)  # こうかとん喜びエフェクト 

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト  
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト  
            score.value += 1  # 1点アップ  

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        # --- 変更ここから ---
        # こうかとんと爆弾の衝突判定
        if not bird.is_invincible:  # 無敵状態でない場合のみ衝突判定を行う
            for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト  
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト  
                score.update(screen)  
                pg.display.update()  
                time.sleep(2)  
                return  
        # --- 変更ここまで --- 

        
        






      


        for flame in flames:  # 炎柱攻撃との衝突判定
            if flame.active and bird.rect.colliderect(flame.rect):
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(2)
                return
        
        for boss in pg.sprite.groupcollide(bosses, beams, False, True):  #ビームがボスに当たる処理
            boss.hp -= 1
            if boss.hp <= 0:
                boss.kill()
                score.value += 100


        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        flames.update()
        flames.draw(screen)
        exps.update()
        exps.draw(screen)
        if boss_mode:
            bosses.draw(screen)
            for boss in bosses:
                boss.draw_hp(screen)
                bosses.update(bird, bombs, flames)
        score.update(screen)

        if result.update(screen, bird, score):
            return

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":  
    pg.init()  
    main()  
    pg.quit()  
    sys.exit()