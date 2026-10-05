"""
浮岛记 (Float) - MVP 原型 v0.1
核心循环: 出岛 -> 探索 -> 采集 -> 回岛 -> 存资源
"""
import pygame
import random
import math
import sys

# ===== 配置 =====
TILE = 32
MAP_W = 40
MAP_H = 40
VIEW_W = 800
VIEW_H = 600
VISION_RADIUS = 5  # 近视野格数
FAR_VISION = 9     # 远视野格数（模糊）

# 颜色
COLORS = {
    'water': (30, 80, 120),
    'water_far': (20, 50, 80),
    'grass': (60, 130, 70),
    'grass_far': (40, 90, 50),
    'sand': (200, 180, 120),
    'rock': (120, 110, 100),
    'tree': (30, 80, 40),
    'fog': (10, 12, 18),
    'memory': (30, 35, 45),
    'player': (255, 140, 60),
    'home': (200, 60, 60),
    'resource': (120, 200, 255),
    'resource_far': (60, 100, 120),
    'ui_bg': (20, 25, 30),
    'ui_text': (230, 230, 230),
    'hunger_bar': (220, 160, 40),
    'hunger_low': (200, 60, 40),
}

# 瓦片类型
WATER, GRASS, SAND, ROCK, TREE, HOME = range(6)


class Island:
    """程序化生成一个浮岛"""
    def __init__(self, seed=42):
        random.seed(seed)
        self.tiles = [[WATER] * MAP_W for _ in range(MAP_H)]
        self.resources = {}  # (x,y) -> type
        self.memory = [[False] * MAP_W for _ in range(MAP_H)]  # 玩家记忆
        self._generate()

    def _generate(self):
        # 用圆形+噪声生成岛屿
        cx, cy = MAP_W // 2, MAP_H // 2
        base_r = 14
        for y in range(MAP_H):
            for x in range(MAP_W):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                noise = random.uniform(-3, 3)
                r = base_r + noise
                if dist < r - 2:
                    self.tiles[y][x] = GRASS
                elif dist < r:
                    self.tiles[y][x] = SAND
                elif dist < r + 1:
                    self.tiles[y][x] = WATER

        # 撒树和石头
        for y in range(MAP_H):
            for x in range(MAP_W):
                if self.tiles[y][x] == GRASS:
                    r = random.random()
                    if r < 0.08:
                        self.tiles[y][x] = TREE
                    elif r < 0.11:
                        self.tiles[y][x] = ROCK

        # 放资源点（水晶、兽皮等）
        for _ in range(15):
            x = random.randint(3, MAP_W - 3)
            y = random.randint(3, MAP_H - 3)
            if self.tiles[y][x] in (GRASS, SAND):
                self.resources[(x, y)] = random.choice(['crystal', 'hide', 'wood'])

        # 家（营地）放在岛中心附近的草地
        self.home = (cx, cy)
        self.tiles[cy][cx] = HOME


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hunger = 100
        self.inventory = {'crystal': 0, 'hide': 0, 'wood': 0}
        self.home_storage = {'crystal': 0, 'hide': 0, 'wood': 0}

    def move(self, dx, dy, island):
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
            t = island.tiles[ny][nx]
            if t not in (WATER, TREE, ROCK):  # 不能走水、树、石头
                self.x, self.y = nx, ny
                self.hunger = max(0, self.hunger - 0.15)  # 移动消耗
                return True
        return False

    def collect(self, island):
        pos = (self.x, self.y)
        if pos in island.resources:
            res = island.resources.pop(pos)
            self.inventory[res] += 1
            return res
        return None

    def deposit(self):
        for k in self.inventory:
            self.home_storage[k] += self.inventory[k]
            self.inventory[k] = 0


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((VIEW_W, VIEW_H))
        pygame.display.set_caption("浮岛记 (Float) - MVP 原型")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.big_font = pygame.font.Font(None, 28)

        self.island = Island(seed=random.randint(1, 9999))
        self.player = Player(self.island.home[0], self.island.home[1])
        self.cam_x, self.cam_y = 0, 0
        self.message = ""
        self.message_timer = 0
        self.day_time = 0  # 0-100, 白天到黑夜
        self.running = True

    def _show_msg(self, text):
        self.message = text
        self.message_timer = 90

    def _update_camera(self):
        self.cam_x = self.player.x * TILE - VIEW_W // 2
        self.cam_y = self.player.y * TILE - VIEW_H // 2

    def _is_visible(self, tx, ty):
        """判断瓦片是否在视野内"""
        dist = math.sqrt((tx - self.player.x) ** 2 + (ty - self.player.y) ** 2)
        if dist <= VISION_RADIUS:
            return 'near'
        elif dist <= FAR_VISION:
            return 'far'
        return None

    def _update_memory(self):
        """更新记忆：看过的地方记住地形"""
        for dy in range(-FAR_VISION, FAR_VISION + 1):
            for dx in range(-FAR_VISION, FAR_VISION + 1):
                tx, ty = self.player.x + dx, self.player.y + dy
                if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
                    self.island.memory[ty][tx] = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key in (pygame.K_SPACE, pygame.K_e):
                    # 采集
                    res = self.player.collect(self.island)
                    if res:
                        names = {'crystal': '水晶', 'hide': '兽皮', 'wood': '木材'}
                        self._show_msg(f"采集到 {names[res]}!")
                    else:
                        self._show_msg("这里没有资源")
                elif event.key == pygame.K_f:
                    # 回家存资源
                    if (self.player.x, self.player.y) == self.island.home:
                        self.player.deposit()
                        self._show_msg("资源已存入营地!")
                    else:
                        self._show_msg("需要回到营地(红色)才能存资源")
                elif event.key == pygame.K_r:
                    # 吃食物（简化：兽皮当食物）
                    if self.player.inventory['hide'] > 0:
                        self.player.inventory['hide'] -= 1
                        self.player.hunger = min(100, self.player.hunger + 30)
                        self._show_msg("吃了兽皮, 饱腹+30")
                    elif self.player.home_storage['hide'] > 0:
                        self.player.home_storage['hide'] -= 1
                        self.player.hunger = min(100, self.player.hunger + 30)
                        self._show_msg("从营地吃了兽皮, 饱腹+30")
                    else:
                        self._show_msg("没有食物了!")

        # 持续移动
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if dx or dy:
            if self.player.move(dx, dy, self.island):
                pass

    def update(self):
        self._update_camera()
        self._update_memory()
        # 时间流逝
        self.day_time = (self.day_time + 0.05) % 100
        # 饥饿随时间下降
        self.player.hunger = max(0, self.player.hunger - 0.02)
        if self.message_timer > 0:
            self.message_timer -= 1

    def draw(self):
        self.screen.fill(COLORS['fog'])

        # 计算可见瓦片范围
        start_x = max(0, int(self.cam_x // TILE) - 1)
        end_x = min(MAP_W, start_x + VIEW_W // TILE + 3)
        start_y = max(0, int(self.cam_y // TILE) - 1)
        end_y = min(MAP_H, start_y + VIEW_H // TILE + 3)

        # 昼夜因子
        night = abs(self.day_time - 50) / 50  # 0=白天, 1=黑夜

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                sx = x * TILE - self.cam_x
                sy = y * TILE - self.cam_y
                vis = self._is_visible(x, y)
                t = self.island.tiles[y][x]
                remembered = self.island.memory[y][x]

                if vis == 'near':
                    color = self._tile_color(t, 'near')
                elif vis == 'far':
                    color = self._tile_color(t, 'far')
                elif remembered:
                    color = COLORS['memory']
                else:
                    color = COLORS['fog']

                pygame.draw.rect(self.screen, color, (sx, sy, TILE, TILE))

                # 资源点（只有近视野能看清是什么）
                if vis == 'near' and (x, y) in self.island.resources:
                    pygame.draw.circle(self.screen, COLORS['resource'],
                                       (sx + TILE // 2, sy + TILE // 2), 6)
                elif vis == 'far' and (x, y) in self.island.resources:
                    pygame.draw.circle(self.screen, COLORS['resource_far'],
                                       (sx + TILE // 2, sy + TILE // 2), 4)

        # 营地标记
        hx = self.island.home[0] * TILE - self.cam_x
        hy = self.island.home[1] * TILE - self.cam_y
        pygame.draw.rect(self.screen, COLORS['home'],
                         (hx + 4, hy + 4, TILE - 8, TILE - 8), 2)

        # 玩家
        px = self.player.x * TILE - self.cam_x + TILE // 2
        py = self.player.y * TILE - self.cam_y + TILE // 2
        pygame.draw.circle(self.screen, COLORS['player'], (px, py), 10)
        pygame.draw.circle(self.screen, (255, 255, 255), (px, py), 10, 2)

        # 夜晚覆盖
        if night > 0.3:
            overlay = pygame.Surface((VIEW_W, VIEW_H))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(int((night - 0.3) / 0.7 * 120))
            self.screen.blit(overlay, (0, 0))

        # UI
        self._draw_ui()

        pygame.display.flip()

    def _tile_color(self, t, dist):
        base = {
            WATER: ('water', 'water_far'),
            GRASS: ('grass', 'grass_far'),
            SAND: ('sand', 'sand'),
            ROCK: ('rock', 'rock'),
            TREE: ('tree', 'tree'),
            HOME: ('home', 'home'),
        }
        key = base[t][0 if dist == 'near' else 1]
        return COLORS[key]

    def _draw_ui(self):
        # 背景条
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (0, 0, VIEW_W, 70))

        # 饥饱度
        hx, hy, hw, hh = 15, 15, 200, 16
        pygame.draw.rect(self.screen, (60, 60, 60), (hx, hy, hw, hh))
        hunger_color = COLORS['hunger_low'] if self.player.hunger < 30 else COLORS['hunger_bar']
        pygame.draw.rect(self.screen, hunger_color,
                         (hx, hy, int(hw * self.player.hunger / 100), hh))
        text = self.font.render(f"饥饱度: {int(self.player.hunger)}", True, COLORS['ui_text'])
        self.screen.blit(text, (hx, hy + hh + 2))

        # 背包
        inv = self.player.inventory
        inv_text = f"背包: 水晶{inv['crystal']} 兽皮{inv['hide']} 木材{inv['wood']}"
        self.screen.blit(self.font.render(inv_text, True, COLORS['ui_text']), (240, 18))

        # 营地仓库
        sto = self.player.home_storage
        sto_text = f"营地: 水晶{sto['crystal']} 兽皮{sto['hide']} 木材{sto['wood']}"
        self.screen.blit(self.font.render(sto_text, True, COLORS['ui_text']), (240, 40))

        # 操作提示
        hints = "WASD移动 | 空格采集 | F存资源(回营地) | R吃食物"
        self.screen.blit(self.font.render(hints, True, (150, 150, 150)), (15, 52))

        # 消息
        if self.message_timer > 0:
            msg_surf = self.big_font.render(self.message, True, (255, 255, 200))
            self.screen.blit(msg_surf, (VIEW_W // 2 - msg_surf.get_width() // 2, VIEW_H - 60))

        # 时间
        period = "白天" if self.day_time < 50 else "黑夜"
        self.screen.blit(self.font.render(period, True, COLORS['ui_text']), (VIEW_W - 60, 18))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()


if __name__ == '__main__':
    Game().run()
