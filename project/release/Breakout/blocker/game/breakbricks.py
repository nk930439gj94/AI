import random
from datetime import datetime, timedelta

import sys
import os
import time
with open(os.devnull, 'w') as f:
    # disable stdout
    oldstdout = sys.stdout
    sys.stdout = f

    import pygame

    # enable stdout
    sys.stdout = oldstdout
from pygame.rect import Rect

import config as c
from ball import Ball
from brick import Brick
from button import Button
from game import Game
from paddle import Paddle
from text_object import TextObject
import colors

import copy
import math
import select

from threading import Thread
from queue import Queue, Empty, LifoQueue

special_effects = dict(
    long_paddle=(colors.ORANGE,
                 lambda g: g.change_paddle(4),
                 lambda g: None),
    slow_ball=(colors.AQUAMARINE2,
               lambda g: g.change_ball_speed(1.5),
               lambda g: None),
    fast_ball=(colors.BROWN,
               lambda g: g.change_ball_speed(2),
               lambda g: None),
    short_paddle=(colors.DARKSEAGREEN4,
                    lambda g: g.change_paddle(2),
                    lambda g: g.change_paddle(0)),
    slow_paddle=(colors.CORAL,
                lambda g: g.slow_paddle(1),
                lambda g: g.slow_paddle(-1)),
    tricky_life=(colors.BLACK,
                lambda g: g.tricky_life(),
                lambda g: None))

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def color2index( color ):
    return {
        colors.ORANGE: 1,
        colors.AQUAMARINE2: 2,
        colors.BROWN: 3,
        colors.DARKSEAGREEN4: 4,
        colors.CORAL: 5,
        colors.BLACK: 6
    }.get(color, 0)


def intersect(obj, ball):
    edges = dict(left=Rect(obj.left, obj.top, 1, obj.height), #left
                    right=Rect(obj.right-1, obj.top, 1, obj.height), #right
                    top=Rect(obj.left, obj.top, obj.width, 1), #top
                    bottom=Rect(obj.left, obj.bottom-1, obj.width, 1)) #bottom
    number = dict(left=1, #left
                    right=2, #right
                    top=3, #top
                    bottom=6) #bottom

    collisions = set(edge for edge, rect in edges.items() if ball.bounds.colliderect(rect))
    if not collisions:
        return 0

    
    return sum( [ number[item] for item in collisions ] )

    

class Breakout(Game):
    def __init__(self):
        Game.__init__(self, 'Breakout', c.screen_width, c.screen_height, os.path.abspath(c.background_image), c.frame_rate)
        self.reset_effect = None
        self.effect_start_time = None
        self.score = 0
        self.lives = c.initial_lives
        self.start_level = False
        self.paddle = None
        self.bricks = None
        self.ball = None
        self.menu_buttons = []
        self.is_game_running = False
        self.create_objects()
        self.points_per_brick = 1
        self.fo = open( os.path.abspath("../score.txt") , "w")
        
        self.q = LifoQueue()
        self.t = Thread(target=enqueue_output, args=(sys.stdin, self.q))
        self.t.daemon = True # thread dies with the program
        self.t.start()

        self.padhit = False
        self.wallhit = False

    def tricky_life(self):
        if self.score < c.row_count * c.screen_width // (c.brick_width + 1) // 4:
            if self.lives > 1:
                self.lives -= 1
        elif self.score > 3 * c.row_count * c.screen_width // (c.brick_width + 1) // 4:
            self.lives += 1
    
    def change_paddle(self, rate):
        if rate is not 0:
            self.paddle.bounds.inflate_ip(-self.paddle.width // rate , 0)
        else:
            self.paddle.bounds.inflate_ip(self.paddle.width , 0)
            
    def slow_paddle(self, indicator):
        if indicator > 0:
            self.paddle.offset = self.paddle.offset * 3 // 4
        else:
            self.paddle.offset = c.paddle_speed

    def set_points_per_brick(self, points):
        self.points_per_brick = points

    def change_ball_speed(self, dy):
        self.ball.speed = (self.ball.speed[0], int( self.ball.speed[1] * dy ))

    def create_menu(self):

        self.is_game_running = True
        self.start_level = True


    def create_objects(self):
        self.create_bricks()
        self.create_labels()
        self.create_menu()
        self.create_paddle()
        self.create_ball(c.screen_width//2)

    def create_labels(self):
        self.score_label = TextObject(c.score_offset,
                                      c.status_offset_y,
                                      lambda: 'SCORE: {0}'.format(self.score),
                                      c.text_color,
                                      c.font_name,
                                      c.font_size)
        self.objects.append(self.score_label)
        self.lives_label = TextObject(c.lives_offset,
                                      c.status_offset_y,
                                      lambda: 'LIVES: {0}'.format(self.lives),
                                      c.text_color,
                                      c.font_name,
                                      c.font_size)
        self.objects.append(self.lives_label)

    def create_ball(self, x):
        speed = (4 if random.random() > 0.5 else -4,  c.ball_speed)
        self.ball = Ball(x,
                         c.screen_height // 2,
                         c.ball_radius,
                         c.ball_color,
                         speed)
        self.objects.append(self.ball)

    def create_paddle(self):
        paddle = Paddle((c.screen_width - c.paddle_width) // 2,
                        c.screen_height - c.paddle_height * 2,
                        c.paddle_width,
                        c.paddle_height,
                        c.paddle_color,
                        c.paddle_speed)
        self.keydown_handlers[pygame.K_LEFT].append(paddle.handle)
        self.keydown_handlers[pygame.K_RIGHT].append(paddle.handle)
        self.keyup_handlers[pygame.K_LEFT].append(paddle.handle)
        self.keyup_handlers[pygame.K_RIGHT].append(paddle.handle)
        self.paddle = paddle
        self.objects.append(self.paddle)

    def create_bricks(self):
        w = c.brick_width
        h = c.brick_height
        brick_count = c.screen_width // (w + 1)
        offset_x = (c.screen_width - brick_count * (w + 1)) // 2

        bricks = []
        effects = random.sample([i for i in range(c.row_count * brick_count)], 24)
        random.shuffle(effects)
        for row in range(c.row_count):
            for col in range(brick_count):
                index = row * brick_count + col
                effect = None
                brick_color = c.brick_color
                if index in effects:
                    brick_color, start_effect_func, reset_effect_func = list(special_effects.values())[effects.index(index)//4]
                    effect = start_effect_func, reset_effect_func

                brick = Brick(offset_x + col * (w + 1),
                              c.offset_y + row * (h + 1),
                              w,
                              h,
                              brick_color,
                              effect)
                bricks.append(brick)
                self.objects.append(brick)
        self.bricks = bricks

    def handle_ball_collisions(self):
        # Hit paddle
        s = self.ball.speed
        edge = intersect(self.paddle, self.ball)
        if edge != 0:
            speedy = int(math.copysign(s[1], -1)) if edge // 3 == 1 else s[1]
            speedx = -s[0] if edge % 3 != 0 or ( edge // 3 == 1 and (self.paddle.moving_left or self.paddle.moving_right) ) else s[0]
            self.ball.speed = ( speedx, speedy)
        

        # Hit floor
        if self.ball.top >= c.screen_height:
            x = self.ball.centerx
            self.lives -= 1
            if self.reset_effect is not None:
                self.reset_effect(self)
                self.reset_effect = None
            if self.lives <= 0:
                self.game_over = True
            else:
                self.objects.remove(self.ball) # Delete old ball
                self.create_ball(x)

        
        # Hit brick
        for brick in self.bricks:
            edge = intersect(brick, self.ball)
            if not edge:
                continue

            self.bricks.remove(brick)
            self.objects.remove(brick)
            self.score += self.points_per_brick
            
            self.ball.speed = ( -s[0] if edge % 3 != 0 and ( (edge % 3) - 1.5 ) * s[0] < 0 else s[0], -s[1] if edge // 3 != 0 and ( edge // 3 - 1.5 ) * s[1] < 0 else s[1])

           
            if brick.special_effect is not None:
                # Reset previous effect if any
                if self.reset_effect is not None:
                    self.reset_effect(self)

                # Trigger special effect
                self.effect_start_time = datetime.now()
                brick.special_effect[0](self)
                # Set current reset effect function
                self.reset_effect = brick.special_effect[1]
        # Hit ceiling
        if self.ball.top <= 0:
            self.ball.speed = (s[0], -s[1] if s[1] <0 else s[1])

        # Hit wall
        if self.ball.left <= 0:
            self.ball.speed = (-s[0] if s[0] <0 else s[0], s[1]) 
        
        if self.ball.right >= c.screen_width:
            self.ball.speed = (-s[0] if s[0] >0 else s[0], s[1])
        
    def update(self):

        if not self.is_game_running:
            return

        if self.start_level:
            self.start_level = False
            self.show_message('GET READY!', centralized=True)

        if not self.bricks:
            print("{0} {1}".format(self.score,self.lives))
            self.is_game_running = False
            self.game_over = True
            return

        # Reset special effect if needed
        if self.reset_effect:
            if datetime.now() - self.effect_start_time >= timedelta(seconds=c.effect_duration):
                self.reset_effect(self)
                self.reset_effect = None

        self.handle_ball_collisions()

        # Return location information to agent
        infor = " ".join( (str(self.ball.centerx), str(self.ball.centery), str(self.paddle.centerx), str(self.paddle.width), str(self.lives), str(self.score)) )
        for brick in self.bricks:
            infor += " " + str(brick.centerx)
            infor += " " + str(brick.centery)
            infor += " " + str(color2index(brick.color))
        print(infor)
        
        sys.stdout.flush()
        
        
        # Pre-Update paddle
        self.paddle.moving_left = 0
        self.paddle.moving_right = 0

        try:  line = self.q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            line = []
        
        for i in range(len(line)):
            if line[i] == "R":
                self.paddle.moving_left = 0
                self.paddle.moving_right = 1
            elif line[i] == "L":
                self.paddle.moving_left = 1
                self.paddle.moving_right = 0

        if self.paddle.moving_left:
            dx = -(min(self.paddle.offset, self.paddle.left))
            if dx == 0:
                self.paddle.moving_left = 0
        elif self.paddle.moving_right:
            dx = min(self.paddle.offset, c.screen_width - self.paddle.right)
            if dx == 0:
                self.paddle.moving_right = 0    
        else:
            dx = 0

        #Update paddle and ball(truncated)
        speedx, speedy = self.objects[-1].speed[0], self.objects[-1].speed[1]  
        n_step = max( abs( speedx ), abs( speedy ) )
        n_start = min( abs( speedx ), abs( speedy ) )
        tmp_ball = copy.deepcopy( self.ball )
        tmp_paddle = copy.deepcopy( self.paddle )
        end = False
        hit = False
        wall = False
        for i in range( 1, n_step + 1):
            if end:
                break
            tmp_ball = copy.deepcopy( self.ball )
            tmp_paddle = copy.deepcopy( self.paddle )
            if math.copysign(i * abs(speedy) // n_step, speedy) == 0:
                continue
            tmp_ball.move(  math.copysign( i * abs(speedx) // n_step, speedx) , math.copysign(i * abs(speedy) // n_step, speedy)  )
            tmp_paddle.move( math.copysign(i * abs(dx) // n_step, dx) , 0 )
            if tmp_ball.top >= c.screen_height or\
                    tmp_ball.top <= 0:
                end = True
            if tmp_ball.left <= 0 or\
                    tmp_ball.right >= c.screen_width:
                if self.wallhit == True:
                    continue
                end = True
                wall = True
            for brick in self.bricks:
                if intersect(brick, tmp_ball) != 0:
                    end = True
                    break
            if intersect(tmp_paddle, tmp_ball) != 0:
                if self.padhit == True:
                    continue
                end = True
                self.padhit = True
                hit = True
        self.padhit = hit
        self.wallhit = wall
        self.ball = copy.deepcopy( tmp_ball )
        self.objects[-1] = self.ball
        self.paddle = copy.deepcopy( tmp_paddle )
        self.objects[-2] = self.paddle
        super().update()

        

        if self.game_over:
            self.fo.write( "{0} {1}\n".format(self.score,self.lives));
            self.fo.close()
            
            return
    def show_message(self, text, color=colors.WHITE, font_name='Arial', font_size=20, centralized=False):
        message = TextObject(c.screen_width // 2, c.screen_height // 2, lambda: text, color, font_name, font_size)
        self.draw()
        message.draw(self.surface, centralized)
        pygame.display.update()
        time.sleep(c.message_duration)

   
    
def main():
    Breakout().run()


if __name__ == '__main__':
    main()
