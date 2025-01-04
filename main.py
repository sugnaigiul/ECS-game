import pygame
import sys
from typing import List, Dict, Optional
import math
import random

# Initialisation de Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
TITLE_FONT_SIZE = 100
SUBTITLE_FONT_SIZE = 40
GAME_TITLE = "BERMUDA EXPLORER"
START_TEXT = "press space to start"
MISSION_TITLE = "YOUR MISSION:"
MISSION_TEXT = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation 
ullamco laboris nisi ut aliquip ex ea commodo consequat."""
CONTINUE_TEXT = "Press space to continue"
BACKGROUND_ANIMATION = "./assets/images/back-anim.png"
BACKGROUND_GAME = "./assets/images/back-game.png"
TORNADO_RADIUS = 20
TORNADO_SPEED = 3
TORNADO_SPAWN_RATE_INITIAL = 60  # Taux initial (plus le nombre est bas, plus il y a de tornades)
TORNADO_SPAWN_RATE_MIN = 15      # Taux minimum (spawn le plus rapide)
DIFFICULTY_INCREASE_INTERVAL = 3 # Augmente la difficulté toutes les X secondes
TORNADO_SPRITE = "./assets/images/tornado-sprite.png"  
TORNADO_ROTATION_SPEED = 5  # Vitesse de rotation en degrés par frame

# Couleurs
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)

class Entity:
    def __init__(self):
        self.id = id(self)
        self.components: Dict = {}

class Component:
    pass

class PositionComponent(Component):
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class RenderComponent(Component):
    def __init__(self, width: int, height: int, color: tuple):
        self.width = width
        self.height = height
        self.color = color

class VelocityComponent(Component):
    def __init__(self, dx: float = 0, dy: float = 0, speed: float = 5.0):
        self.dx = dx
        self.dy = dy
        self.speed = speed

class SpriteComponent(Component):
    def __init__(self, image_path: str, width: int = None, height: int = None):
        self.original_image = pygame.image.load(image_path)
        if width is not None and height is not None:
            self.original_image = pygame.transform.scale(self.original_image, (width, height))
        self.image = self.original_image
        self.angle = 0

class RotorComponent(Component):
    def __init__(self, image_path: str, width: int, height: int, parent_width: int):
        self.original_image = pygame.image.load(image_path)
        self.original_image = pygame.transform.scale(self.original_image, (width, height))
        self.image = self.original_image
        self.angle = 0
        self.rotation_speed = 0  # Vitesse de rotation en degrés par frame
        self.parent_width = parent_width  # Largeur de l'hélicoptère pour centrer le rotor

class TornadoComponent(Component):
    def __init__(self, radius: int, speed: float):
        self.radius = radius
        self.speed = speed
        self.angle = 0  # Angle de rotation actuel
        self.original_image = pygame.image.load(TORNADO_SPRITE)
        # Redimensionner l'image pour qu'elle soit un peu plus grande que le cercle de collision
        sprite_size = radius * 2.5  # 2.5 fois la taille du cercle pour un meilleur effet visuel
        self.original_image = pygame.transform.scale(self.original_image, (sprite_size, sprite_size))
        self.image = self.original_image

class InputSystem:
    def update(self, entities: List[Entity]):
        keys = pygame.key.get_pressed()
        for entity in entities:
            if 'velocity' in entity.components:
                vel = entity.components['velocity']
                vel.dx = 0
                vel.dy = 0
                if keys[pygame.K_LEFT]:
                    vel.dx = -vel.speed
                if keys[pygame.K_RIGHT]:
                    vel.dx = vel.speed
                if keys[pygame.K_UP]:
                    vel.dy = -vel.speed
                if keys[pygame.K_DOWN]:
                    vel.dy = vel.speed

class MovementSystem:
    def update(self, entities: List[Entity]):
        for entity in entities:
            if 'position' in entity.components and 'velocity' in entity.components:
                pos = entity.components['position']
                vel = entity.components['velocity']
                
                if 'sprite' in entity.components:
                    sprite = entity.components['sprite']
                    
                    # Rotation du sprite en fonction de la direction
                    if vel.dx != 0 or vel.dy != 0:
                        # Calculer l'angle en fonction de la direction
                        angle = math.degrees(math.atan2(-vel.dy, vel.dx))
                        sprite.angle = angle
                        # -90 degrés pour compenser l'orientation initiale du sprite
                        sprite.image = pygame.transform.rotate(sprite.original_image, sprite.angle - 90)
                        
                        # Transformer la vélocité en fonction de l'angle actuel
                        angle_rad = math.radians(sprite.angle)
                        speed = math.sqrt(vel.dx * vel.dx + vel.dy * vel.dy)
                        real_dx = speed * math.cos(angle_rad)
                        real_dy = -speed * math.sin(angle_rad)
                        
                        # Calculer la nouvelle position
                        new_x = pos.x + real_dx
                        new_y = pos.y + real_dy
                        
                        # Obtenir les dimensions du sprite
                        sprite_width = sprite.image.get_width()
                        sprite_height = sprite.image.get_height()
                        
                        # Vérifier et appliquer les limites
                        new_x = max(0, min(new_x, WINDOW_WIDTH - sprite_width))
                        new_y = max(0, min(new_y, WINDOW_HEIGHT - sprite_height))
                        
                        # Appliquer la position finale
                        pos.x = new_x
                        pos.y = new_y

class RenderSystem:
    def __init__(self, screen):
        self.screen = screen

    def update(self, entities: List[Entity]):
        for entity in entities:
            if 'position' in entity.components:
                pos = entity.components['position']
                
                # Rendu des tornades
                if 'tornado' in entity.components:
                    tornado = entity.components['tornado']
                    # Mettre à jour la rotation
                    tornado.angle = (tornado.angle + TORNADO_ROTATION_SPEED) % 360
                    tornado.image = pygame.transform.rotate(tornado.original_image, tornado.angle)
                    
                    # Calculer la position pour centrer l'image sur le cercle de collision
                    tornado_rect = tornado.image.get_rect(center=(pos.x, pos.y))
                    self.screen.blit(tornado.image, tornado_rect)
                
                # Rendu du sprite principal
                if 'sprite' in entity.components:
                    sprite = entity.components['sprite']
                    self.screen.blit(sprite.image, (pos.x, pos.y))
                    
                # Rendu du rotor
                if 'rotor' in entity.components:
                    rotor = entity.components['rotor']
                    rotor.angle = (rotor.angle + rotor.rotation_speed) % 360
                    rotor.image = pygame.transform.rotate(rotor.original_image, rotor.angle)
                    
                    # Centrer le rotor sur l'hélicoptère
                    sprite = entity.components['sprite']
                    rotor_x = pos.x + (sprite.image.get_width() - rotor.image.get_width()) / 2
                    rotor_y = pos.y + (sprite.image.get_height() - rotor.image.get_height()) / 2
                    self.screen.blit(rotor.image, (rotor_x, rotor_y))

class TornadoSystem:
    def __init__(self):
        self.spawn_counter = 0
        self.current_spawn_rate = TORNADO_SPAWN_RATE_INITIAL
    
    def update(self, entities: List[Entity], game_timer: int) -> Optional[bool]:
        # Ajuster la difficulté en fonction du temps
        self.current_spawn_rate = max(
            TORNADO_SPAWN_RATE_MIN,
            TORNADO_SPAWN_RATE_INITIAL - (game_timer // DIFFICULTY_INCREASE_INTERVAL) * 5
        )
        
        # Déplacer les tornades existantes
        for entity in entities:
            if 'tornado' in entity.components and 'position' in entity.components:
                pos = entity.components['position']
                tornado = entity.components['tornado']
                
                # Déplacer la tornade vers le bas
                pos.y += tornado.speed
                
                # Vérifier les collisions avec l'hélicoptère
                for other in entities:
                    if 'sprite' in other.components and 'position' in other.components:
                        heli_pos = other.components['position']
                        heli_sprite = other.components['sprite']
                        
                        # Calculer le centre de l'hélicoptère
                        heli_center_x = heli_pos.x + heli_sprite.image.get_width() / 2
                        heli_center_y = heli_pos.y + heli_sprite.image.get_height() / 2
                        
                        # Calculer la distance entre la tornade et l'hélicoptère
                        distance = math.sqrt((pos.x - heli_center_x)**2 + (pos.y - heli_center_y)**2)
                        
                        # Si collision, retourner True pour indiquer game over
                        if distance < tornado.radius + min(heli_sprite.image.get_width(), 
                                                         heli_sprite.image.get_height()) / 2:
                            return True
                
                # Supprimer les tornades qui sortent de l'écran
                if pos.y > WINDOW_HEIGHT:
                    entities.remove(entity)
        
        # Spawn de nouvelles tornades avec le taux actualisé
        self.spawn_counter += 1
        if self.spawn_counter >= self.current_spawn_rate:
            self.spawn_counter = 0
            self.spawn_tornado(entities)
        
        return False
    
    def spawn_tornado(self, entities: List[Entity]):
        tornado = Entity()
        # Position aléatoire en haut de l'écran
        x = random.randint(TORNADO_RADIUS, WINDOW_WIDTH - TORNADO_RADIUS)
        tornado.components['position'] = PositionComponent(x, -TORNADO_RADIUS)
        tornado.components['tornado'] = TornadoComponent(TORNADO_RADIUS, TORNADO_SPEED)
        tornado.components['render'] = RenderComponent(TORNADO_RADIUS * 2, TORNADO_RADIUS * 2, BLUE)
        entities.append(tornado)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hélicoptère Exploration")
        self.clock = pygame.time.Clock()
        self.entities: List[Entity] = []
        self.running = True
        self.in_menu = True
        self.in_mission_screen = False
        self.in_intro_animation = False
        self.animation_timer = 0
        self.fade_alpha = 0
        self.boat = None
        self.game_timer = 0  # Timer commence à 0
        self.timer_font = pygame.font.Font(None, 36)
        self.last_time = 0
        self.tornado_system = TornadoSystem()
        self.game_over = False

        # Systèmes
        self.movement_system = MovementSystem()
        self.render_system = RenderSystem(self.screen)
        self.input_system = InputSystem()

        # Chargement des backgrounds
        self.background_animation = pygame.image.load(BACKGROUND_ANIMATION)
        self.background_game = pygame.image.load(BACKGROUND_GAME)
        self.background_animation = pygame.transform.scale(self.background_animation, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background_game = pygame.transform.scale(self.background_game, (WINDOW_WIDTH, WINDOW_HEIGHT))

    def create_boat(self):
        boat = Entity()
        # Centrer le bateau en prenant en compte sa taille
        boat_width, boat_height = 103, 212
        boat_x = (WINDOW_WIDTH - boat_width) / 2
        boat_y = (WINDOW_HEIGHT - boat_height) / 2
        boat.components['position'] = PositionComponent(boat_x, boat_y)
        boat.components['sprite'] = SpriteComponent("./assets/images/boat-sprite.png", boat_width, boat_height)
        self.entities.append(boat)
        self.boat = boat
        return boat

    def create_helicopter(self):
        helicopter = Entity()
        boat_pos = self.boat.components['position']
        heli_size = 104  # Taille unique puisque c'est maintenant carré
        heli_x = boat_pos.x + (103 - heli_size) / 2
        heli_y = boat_pos.y + heli_size - 30
        
        helicopter.components['position'] = PositionComponent(heli_x, heli_y)
        helicopter.components['velocity'] = VelocityComponent()
        helicopter.components['sprite'] = SpriteComponent("./assets/images/heli-sprite.png", heli_size, heli_size)
        # Ajout du rotor avec une taille proportionnelle à l'hélicoptère
        rotor_size = 92  # Taille du rotor
        helicopter.components['rotor'] = RotorComponent("./assets/images/rotor-sprite.png", rotor_size, rotor_size, heli_size)
        self.entities.append(helicopter)

    def draw_menu(self):
        self.screen.fill(BLACK)
        
        # Titre du jeu
        title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        title_text = title_font.render(GAME_TITLE, True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/4))
        
        # Image du menu (à charger et redimensionner)
        menu_image = pygame.image.load("./assets/images/heli-menu.png")  # Créez cette image
        menu_image = pygame.transform.scale(menu_image, (634, 215))  # Ajustez la taille selon vos besoins
        image_rect = menu_image.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
        
        # Texte "press space to start"
        subtitle_font = pygame.font.Font(None, SUBTITLE_FONT_SIZE)
        subtitle_text = subtitle_font.render(START_TEXT, True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT * 3/4))
        
        # Affichage des éléments
        self.screen.blit(title_text, title_rect)
        self.screen.blit(menu_image, image_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        pygame.display.flip()

    def draw_mission_screen(self):
        self.screen.fill(BLACK)
        
        # Titre de la mission
        mission_font = pygame.font.Font(None, 50)
        mission_title = mission_font.render(MISSION_TITLE, True, WHITE)
        title_rect = mission_title.get_rect(topleft=(50, 50))
        
        # Texte principal
        text_font = pygame.font.Font(None, 36)
        # Wrap le texte pour qu'il ne dépasse pas l'écran
        words = MISSION_TEXT.split()
        lines = []
        current_line = []
        current_width = 0
        max_width = WINDOW_WIDTH - 100  # Marge de 50px de chaque côté
        
        for word in words:
            word_surface = text_font.render(word + " ", True, WHITE)
            word_width = word_surface.get_width()
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        lines.append(" ".join(current_line))
        
        # Afficher le texte ligne par ligne
        y_offset = 150
        for line in lines:
            text_surface = text_font.render(line, True, WHITE)
            text_rect = text_surface.get_rect(topleft=(50, y_offset))
            self.screen.blit(text_surface, text_rect)
            y_offset += 40
        
        # Texte "Press space to continue"
        continue_font = pygame.font.Font(None, 40)
        continue_text = continue_font.render(CONTINUE_TEXT, True, WHITE)
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT - 50))
        
        # Affichage des éléments
        self.screen.blit(mission_title, title_rect)
        self.screen.blit(continue_text, continue_rect)
        pygame.display.flip()

    def start_mission_screen(self):
        self.in_menu = False
        self.in_mission_screen = True

    def start_intro_animation(self):
        self.in_mission_screen = False
        self.in_intro_animation = True
        self.animation_timer = 0
        self.create_boat()
        self.create_helicopter()

    def update_intro_animation(self):
        self.animation_timer += 1
        
        helicopter = self.entities[-1]
        heli_pos = helicopter.components['position']
        rotor = helicopter.components['rotor']
        
        if self.animation_timer < 120:  # 2 premières secondes : démarrage du rotor
            rotor.rotation_speed = min(rotor.rotation_speed + 1, 15)  # Accélération progressive
        elif self.animation_timer < 300:  # Décollage vertical
            rotor.rotation_speed = 30  # Vitesse maximale
            heli_pos.y -= 2.3
        elif self.animation_timer < 360:  # Fondu au noir
            self.fade_alpha = min(255, self.fade_alpha + 5)
        else:
            self.in_intro_animation = False
            self.setup_game_world()

    def setup_game_world(self):
        self.entities.clear()
        self.create_helicopter()
        helicopter = self.entities[-1]
        # Définir la vitesse de rotation maximale du rotor pour le jeu
        helicopter.components['rotor'].rotation_speed = 30
        self.game_timer = 0
        self.last_time = pygame.time.get_ticks()
        self.game_over = False

    def update_timer(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time >= 1000:  # 1000ms = 1 seconde
            self.game_timer += 1  # Incrémenter au lieu de décrémenter
            self.last_time = current_time

    def draw_timer(self):
        timer_text = self.timer_font.render(f"Time: {self.game_timer}", True, WHITE)
        timer_rect = timer_text.get_rect(topright=(WINDOW_WIDTH - 20, 20))
        self.screen.blit(timer_text, timer_rect)

    def run(self):
        fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fade_surface.fill((0, 0, 0))

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.in_menu:
                            self.start_mission_screen()
                        elif self.in_mission_screen:
                            self.start_intro_animation()

            if self.in_menu:
                self.draw_menu()
            elif self.in_mission_screen:
                self.draw_mission_screen()
            elif self.in_intro_animation:
                self.screen.blit(self.background_animation, (0, 0))
                self.render_system.update(self.entities)
                self.update_intro_animation()
                
                # Appliquer le fondu au noir si nécessaire
                if self.fade_alpha > 0:
                    fade_surface.set_alpha(self.fade_alpha)
                    self.screen.blit(fade_surface, (0, 0))
                
                pygame.display.flip()
            else:
                # Jeu normal
                self.screen.blit(self.background_game, (0, 0))
                
                if not self.game_over:
                    self.input_system.update(self.entities)
                    self.movement_system.update(self.entities)
                    
                    # Passer le game_timer au tornado_system
                    if self.tornado_system.update(self.entities, self.game_timer):
                        self.game_over = True
                    
                    self.render_system.update(self.entities)
                    self.update_timer()
                    self.draw_timer()
                else:
                    # Afficher l'écran de game over
                    game_over_font = pygame.font.Font(None, 74)
                    game_over_text = game_over_font.render('Game Over', True, WHITE)
                    game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
                    self.screen.blit(game_over_text, game_over_rect)
                
                pygame.display.flip()

            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()