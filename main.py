import pygame
import sys
from typing import List, Dict
import math

# Initialisation de Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

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
                        
                        # Appliquer le mouvement
                        pos.x += real_dx
                        pos.y += real_dy

class RenderSystem:
    def __init__(self, screen):
        self.screen = screen

    def update(self, entities: List[Entity]):
        for entity in entities:
            if 'position' in entity.components:
                pos = entity.components['position']
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
                    rotor_x = pos.x + sprite.image.get_width()/2 - rotor.image.get_width()/2
                    rotor_y = pos.y + sprite.image.get_height()/4 - rotor.image.get_height()/2 + 20
                    self.screen.blit(rotor.image, (rotor_x, rotor_y))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hélicoptère Exploration")
        self.clock = pygame.time.Clock()
        self.entities: List[Entity] = []
        self.running = True
        self.in_menu = True
        self.in_intro_animation = False
        self.animation_timer = 0
        self.fade_alpha = 0
        self.boat = None
        self.game_timer = 0  # Timer commence à 0
        self.timer_font = pygame.font.Font(None, 36)
        self.last_time = 0

        # Systèmes
        self.movement_system = MovementSystem()
        self.render_system = RenderSystem(self.screen)
        self.input_system = InputSystem()

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
        heli_width, heli_height = 52, 104
        heli_x = boat_pos.x + (103 - heli_width) / 2
        heli_y = boat_pos.y + heli_height - 30
        
        helicopter.components['position'] = PositionComponent(heli_x, heli_y)
        helicopter.components['velocity'] = VelocityComponent()
        helicopter.components['sprite'] = SpriteComponent("./assets/images/heli-sprite.png", heli_width, heli_height)
        # Ajout du rotor
        helicopter.components['rotor'] = RotorComponent("./assets/images/rotor-sprite.png", 92, 92, heli_width)
        self.entities.append(helicopter)

    def draw_menu(self):
        self.screen.fill(BLACK)
        # Créer le bouton "BEGIN"
        font = pygame.font.Font(None, 74)
        text = font.render('BEGIN', True, WHITE)
        text_rect = text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
        self.screen.blit(text, text_rect)
        pygame.display.flip()

    def start_intro_animation(self):
        self.in_menu = False
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
                elif event.type == pygame.MOUSEBUTTONDOWN and self.in_menu:
                    self.start_intro_animation()

            if self.in_menu:
                self.draw_menu()
            elif self.in_intro_animation:
                self.screen.fill(BLUE)
                self.render_system.update(self.entities)
                self.update_intro_animation()
                
                # Appliquer le fondu au noir si nécessaire
                if self.fade_alpha > 0:
                    fade_surface.set_alpha(self.fade_alpha)
                    self.screen.blit(fade_surface, (0, 0))
                
                pygame.display.flip()
            else:
                # Jeu normal
                self.screen.fill(BLUE)
                self.input_system.update(self.entities)
                self.movement_system.update(self.entities)
                self.render_system.update(self.entities)
                self.update_timer()  # Mettre à jour le timer
                self.draw_timer()    # Afficher le timer
                pygame.display.flip()

            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
