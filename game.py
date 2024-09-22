import pygame
import random
import os
import sys


# Инициализация Pygame
pygame.init()

# Константы для игры
WIDTH, HEIGHT = 800, 400
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -10
PLAYER_SPEED = 5
SCROLL_SPEED = 3  # Скорость прокрутки уровня

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)

# Инициализация экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Petrulio, the game")

# Загрузка ассетов
ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
PLAYER_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'player.png')).convert_alpha()

# Спрайты для анимации прыжка
PLAYER_JUMP_SPRITES = [
    pygame.image.load(os.path.join(ASSET_DIR, 'player_jump1.png')).convert_alpha(),
    pygame.image.load(os.path.join(ASSET_DIR, 'player_jump2.png')).convert_alpha()
]
PLATFORM_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'platform.png')).convert_alpha()
PLATFORM_MOVE_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'platform_move.png')).convert_alpha()
COIN_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'coin.png')).convert_alpha()
ENEMY_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'enemy.png')).convert_alpha()
FAST_ENEMY_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'enemy_fast.png')).convert_alpha()
FLYING_ENEMY_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'enemy_fly.png')).convert_alpha()
POWERUP_JUMP_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'powerup_jump.png')).convert_alpha()
POWERUP_SPEED_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'powerup_speed.png')).convert_alpha()
POWERUP_INVINCIBLE_IMG = pygame.image.load(os.path.join(ASSET_DIR, 'powerup_invincible.png')).convert_alpha()

# Шрифт для текста
font = pygame.font.SysFont("Roboto", 32)
small_font = pygame.font.SysFont("Roboto", 24)

# Класс игрока с анимацией прыжка
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = PLAYER_IMG
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT - 100)
        self.velocity_y = 0
        self.is_jumping = False
        self.is_in_air = False
        self.health = 3  # Игрок имеет 3 очка здоровья
        self.coins_collected = 0
        self.enemy_kills = 0
        self.speed_boost = 1
        self.jump_boost = 1
        self.invincible = False
        self.powerup_time = 0  # Время действия улучшения
        self.collect_text = None  # Текст для отображения при сборе
        self.collect_timer = 0  # Таймер для отображения текста

        # Инициализация анимации прыжка
        self.jump_animation_timer = 0  # Таймер для переключения кадров анимации
        self.jump_animation_frame = 0  # Индекс текущего кадра анимации

    def update(self):
        # Применение улучшений
        if self.powerup_time > 0:
            self.powerup_time -= 1
            if self.powerup_time == 0:  # Завершение эффекта
                self.speed_boost = 1
                self.jump_boost = 1
                self.invincible = False

        # Гравитация
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        # Управление игроком
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED * self.speed_boost
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED * self.speed_boost
        if keys[pygame.K_SPACE] and not self.is_jumping:
            self.velocity_y = JUMP_STRENGTH * self.jump_boost
            self.is_jumping = True
            self.is_in_air = True

        # Анимация прыжка, если игрок в воздухе
        if self.is_in_air:
            self.animate_jump()

        # Граничные условия
        if self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.is_jumping = False
            self.is_in_air = False
            self.image = PLAYER_IMG  # Возвращаем стандартный спрайт

        # Отображение текста при сборе улучшений или монет
        if self.collect_timer > 0:
            self.collect_timer -= 1
        else:
            self.collect_text = None

    # Анимация прыжка
    def animate_jump(self):
        self.jump_animation_timer += 1
        if self.jump_animation_timer > 5:  # Меняем кадр каждые 5 кадров
            self.jump_animation_timer = 0
            self.jump_animation_frame += 1
            if self.jump_animation_frame >= len(PLAYER_JUMP_SPRITES):
                self.jump_animation_frame = 0
        self.image = PLAYER_JUMP_SPRITES[self.jump_animation_frame]

    # Метод для проверки столкновения с врагами
    def collide_with_enemies(self, enemies):
        hits = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in hits:
            if self.velocity_y > 0:  # Если игрок падает на врага
                self.velocity_y = JUMP_STRENGTH  # Подпрыгиваем после удара по врагу
                enemy.kill()  # Уничтожаем врага
                self.enemy_kills += 1  # Увеличиваем счётчик убийств
            else:  # Если игрок сталкивается с врагом сбоку
                if not self.invincible:  # Если не под действием неуязвимости
                    self.health -= 1  # Враг наносит 1 урон
                    self.health = max(self.health, 0)  # Убедимся, что здоровье не падает ниже 0
                    if self.health <= 0:
                        return True  # Игра окончена
        return False

    # Функция для проверки столкновения с монетами
    def collect_coins(self, coins):
        hits = pygame.sprite.spritecollide(self, coins, True)
        if hits:
            self.coins_collected += len(hits)
            self.collect_text = "+1 кроси"
            self.collect_timer = 60  # Показываем текст в течение 1 секунды (60 кадров)
            
   # Отображение текста при сборе предметов
    def display_collect_text(self, screen):
        if self.collect_text:
            collect_surface = small_font.render(self.collect_text, True, DARK_GREEN)
            screen.blit(collect_surface, (self.rect.x + 50, self.rect.y - 30))

    # Метод для проверки столкновения с платформами
    def collide_with_platforms(self, platforms):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits:
            if self.velocity_y > 0:  # Проверяем, что игрок падает сверху
                self.rect.bottom = hits[0].rect.top  # Останавливаем игрока на платформе
                self.velocity_y = 0  # Обнуляем вертикальную скорость
                self.is_jumping = False  # Сбрасываем состояние прыжка
                self.is_in_air = False
                self.image = PLAYER_IMG  # Возвращаем стандартный спрайт после приземления


# Класс платформы с вариативной шириной
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        platform_width = random.randint(100, 200)
        self.image = pygame.transform.scale(PLATFORM_IMG, (platform_width, 20))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.kill()

# Класс движущейся платформы
class MovingPlatform(Platform):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.transform.scale(PLATFORM_MOVE_IMG, (random.randint(100, 200), 20))
        self.direction = 1

    def update(self):
        self.rect.x -= SCROLL_SPEED
        self.rect.y += self.direction
        if self.rect.y > HEIGHT - 50 or self.rect.y < HEIGHT - 150:
            self.direction *= -1
        if self.rect.right < 0:
            self.kill()

# Класс врагов
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type='normal'):
        super().__init__()
        if enemy_type == 'fast':
            self.image = pygame.image.load(os.path.join(ASSET_DIR, 'enemy_fast.png')).convert_alpha()
            self.speed = SCROLL_SPEED * 2
        elif enemy_type == 'flying':
            self.image = pygame.image.load(os.path.join(ASSET_DIR, 'enemy_fly.png')).convert_alpha()
            self.speed = SCROLL_SPEED
            self.direction = random.choice([-1, 1])
        else:
            self.image = pygame.transform.scale(ENEMY_IMG, (32, 32))
            self.speed = SCROLL_SPEED

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= self.speed
        if hasattr(self, 'direction'):
            self.rect.y += self.direction
            if self.rect.y > HEIGHT - 50 or self.rect.y < HEIGHT - 150:
                self.direction *= -1
        if self.rect.right < 0:
            self.kill()

# Класс монет
class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(COIN_IMG, (32, 32))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.kill()

# Класс улучшений (power-ups)
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type):
        super().__init__()
        if power_type == "jump":
            self.image = POWERUP_JUMP_IMG
        elif power_type == "speed":
            self.image = POWERUP_SPEED_IMG
        elif power_type == "invincible":
            self.image = POWERUP_INVINCIBLE_IMG

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.type = power_type  # jump, speed, invincible

    def update(self):
        self.rect.x -= SCROLL_SPEED
        if self.rect.right < 0:
            self.kill()
        
# Новый класс Lava
class Lava(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Загрузка спрайта лавы
        self.image = pygame.image.load(os.path.join(ASSET_DIR, 'lava.png')).convert_alpha()
        self.image = pygame.transform.scale(self.image, (WIDTH, 20))  # Масштабирование изображения по ширине экрана
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = HEIGHT - 20  # Лава находится в самом низу экрана

    def update(self):
        pass  # Лава статична, она не двигается


# Класс параллакса для слоя фона с учётом времени суток
class ParallaxLayer:
    def __init__(self, day_image, evening_image, night_image, speed):
        self.day_image = pygame.image.load(os.path.join(ASSET_DIR, day_image)).convert_alpha()
        self.evening_image = pygame.image.load(os.path.join(ASSET_DIR, evening_image)).convert_alpha()
        self.night_image = pygame.image.load(os.path.join(ASSET_DIR, night_image)).convert_alpha()

        self.speed = speed
        self.current_image = self.day_image  # Начальный фон - день
        self.x1 = 0  # Первое изображение
        self.x2 = self.current_image.get_rect().width  # Второе изображение для плавного скролла

    def update(self):
        # Двигаем оба изображения влево
        self.x1 -= self.speed
        self.x2 -= self.speed

        # Если первое изображение ушло за экран, перемещаем его вправо, за второе
        if self.x1 <= -self.current_image.get_rect().width:
            self.x1 = self.current_image.get_rect().width
        if self.x2 <= -self.current_image.get_rect().width:
            self.x2 = self.current_image.get_rect().width

    def draw(self, screen):
        # Отрисовываем два изображения для бесшовного эффекта
        screen.blit(self.current_image, (self.x1, 0))
        screen.blit(self.current_image, (self.x2, 0))

    def change_time_of_day(self, time_of_day):
        # Меняем изображение в зависимости от времени суток
        if time_of_day == 'day':
            self.current_image = self.day_image
        elif time_of_day == 'evening':
            self.current_image = self.evening_image
        elif time_of_day == 'night':
            self.current_image = self.night_image

# Класс для управления сменой времени суток
class DayNightCycle:
    def __init__(self, far_layer, near_layer):
        self.cycle_time = 0
        self.time_of_day = "day"
        self.far_layer = far_layer
        self.near_layer = near_layer

    def update(self):
        self.cycle_time += 1
        if self.cycle_time < 1000:
            self.time_of_day = "day"
        elif 1000 <= self.cycle_time < 2000:
            self.time_of_day = "evening"
        elif 2000 <= self.cycle_time < 3000:
            self.time_of_day = "night"
        else:
            self.cycle_time = 0  # Сброс цикла

        # Обновляем слои параллакса в зависимости от времени суток
        self.far_layer.change_time_of_day(self.time_of_day)
        self.near_layer.change_time_of_day(self.time_of_day)

    def get_time_of_day_text(self):
        if self.time_of_day == "day":
            return "щя день"
        elif self.time_of_day == "evening":
            return "щя вечер"
        else:
            return "щя ноч"

# Основной игровой цикл
def main():
    clock = pygame.time.Clock()
    running = True

    # Создаём слои параллакса с изображениями для каждого времени суток
    background_far = ParallaxLayer(
        'background_far_day.png', 'background_far_evening.png', 'background_far_night.png', 1
    )
    background_near = ParallaxLayer(
        'background_near_day.png', 'background_near_evening.png', 'background_near_night.png', 2
    )

    day_night_cycle = DayNightCycle(background_far, background_near)

    # Создание игрока и других объектов
    player = Player()
    platforms = pygame.sprite.Group()
    moving_platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()

    # Начальные платформы
    platform1 = Platform(100, HEIGHT - 50)
    platform2 = Platform(300, HEIGHT - 150)
    platform3 = MovingPlatform(500, HEIGHT - 100)
    platforms.add(platform1, platform2)
    moving_platforms.add(platform3)
    all_sprites.add(platform1, platform2, platform3, player)

    # Таймеры для генерации платформ, врагов и монет
    platform_timer = 70
    enemy_timer = 0
    coin_timer = 0
    powerup_timer = 0

    game_over = False

    while running:
        clock.tick(FPS)
        screen.fill(WHITE)

        # Обновление фонов для эффекта параллакса
        background_far.update()
        background_near.update()

        # Отрисовка фонов
        background_far.draw(screen)
        background_near.draw(screen)

        # Обновляем цикл смены дня/ночи
        day_night_cycle.update()

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Обновление таймеров для генерации
        platform_timer += 1
        enemy_timer += 1
        coin_timer += 1
        powerup_timer += 1

        # Генерация платформ
        if platform_timer > 100:
            platform_y = random.randint(HEIGHT - 120, HEIGHT - 50)
            new_platform = Platform(WIDTH, platform_y)
            platforms.add(new_platform)
            all_sprites.add(new_platform)
            platform_timer = 0

        # Генерация врагов
        if enemy_timer > 150:
            enemy_y = random.randint(HEIGHT - 150, HEIGHT - 50)
            while any(p.rect.colliderect(pygame.Rect(WIDTH, enemy_y, 32, 32)) for p in platforms):
                enemy_y = random.randint(HEIGHT - 150, HEIGHT - 50)
            enemy_type = random.choice(['normal', 'fast', 'flying'])
            new_enemy = Enemy(WIDTH, enemy_y, enemy_type)
            enemies.add(new_enemy)
            all_sprites.add(new_enemy)
            enemy_timer = 0

        # Генерация монет
        if coin_timer > 120:
            coin_y = random.randint(HEIGHT - 200, HEIGHT - 100)
            while any(p.rect.colliderect(pygame.Rect(WIDTH, coin_y, 32, 32)) for p in platforms):
                coin_y = random.randint(HEIGHT - 200, HEIGHT - 100)
            new_coin = Coin(WIDTH, coin_y)
            coins.add(new_coin)
            all_sprites.add(new_coin)
            coin_timer = 0

        # Генерация улучшений (power-ups)
        if powerup_timer > 500:
            powerup_y = random.randint(HEIGHT - 200, HEIGHT - 50)
            powerup_type = random.choice(["jump", "speed", "invincible"])
            new_powerup = PowerUp(WIDTH, powerup_y, powerup_type)
            powerups.add(new_powerup)
            all_sprites.add(new_powerup)
            powerup_timer = 0

        # Обновление всех спрайтов
        all_sprites.update()

        # Коллизии игрока с платформами
        player.collide_with_platforms(platforms)
        player.collide_with_platforms(moving_platforms)

        # Коллизии игрока с врагами
        if player.collide_with_enemies(enemies):
            game_over = True

        # Сбор монет
        player.collect_coins(coins)

        # Сбор улучшений
        collect_powerups(player, powerups)

        # Отрисовка всех спрайтов
        all_sprites.draw(screen)

        # Отображение количества монет и здоровья
        draw_text(f"Кроси: {player.coins_collected}", font, BLACK, screen, 10, 10)
        draw_text(f"Жизи: {player.health}", font, BLACK, screen, 10, 40)
        draw_text(f"Убито катовцев: {player.enemy_kills}", font, BLACK, screen, 10, 70)

        # Добавление горизонтальной черты и текста времени дня
        pygame.draw.line(screen, BLACK, (10, 100), (WIDTH - 650, 100), 2)
        draw_text(day_night_cycle.get_time_of_day_text(), font, BLACK, screen, 10, 110)

        # Показ текста при сборе предметов
        player.display_collect_text(screen)

        # Проверка на проигрыш
        if game_over or player.rect.bottom >= HEIGHT:
            darken_screen()
            draw_text("Игра окончена! Нажмите R для рестарта", font, RED, screen, WIDTH // 2 - 200, HEIGHT // 2)
            pygame.display.flip()
            wait_for_restart()

        # Обновление дисплея
        pygame.display.flip()

    pygame.quit()


# Функция затемнения экрана
def darken_screen():
    dark_overlay = pygame.Surface((WIDTH, HEIGHT))
    dark_overlay.fill((0, 0, 0))
    dark_overlay.set_alpha(150)  # Полупрозрачный черный слой
    screen.blit(dark_overlay, (0, 0))

# Функция ожидания перезапуска
def wait_for_restart():
    waiting_for_restart = True
    while waiting_for_restart:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting_for_restart = False
                    restart_game()  # Перезапуск игры

# Функция перезапуска игры
def restart_game():
    main()

# Функция отображения текста на экране
def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

# Функция сбора улучшений
def collect_powerups(player, powerups):
    hits = pygame.sprite.spritecollide(player, powerups, True)
    for hit in hits:
        if hit.type == "speed":
            player.speed_boost = 2
            player.collect_text = "СВЕТОФОРСКИЙ РИС"
        elif hit.type == "jump":
            player.jump_boost = 1.5  # Немного уменьшили силу прыжка
            player.collect_text = "Мегапрыжок"
        elif hit.type == "invincible":
            player.invincible = True
            player.collect_text = "Спрятался..."
        player.powerup_time = 300  # Время действия улучшения (например, 5 секунд)
        player.collect_timer = 60

if __name__ == "__main__":
    main()
