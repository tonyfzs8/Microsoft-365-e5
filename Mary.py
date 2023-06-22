__author__ = 'marble_xu'

import os
import json
import pygame as pg
from .. import setup, tools
from .. import constants as c
from ..components import powerup

class Player(pg.sprite.Sprite):
 def __init__(self, player_name):
  pg.sprite.Sprite.__init__(self)
  self.player_name = player_name
  self.load_data()
  self.setup_timer()
  self.setup_state()
  self.setup_speed()
  self.load_images()
  
  if c.DEBUG:
   self.right_frames = self.big_fire_frames[0]
   self.left_frames = self.big_fire_frames[1]
   self.big = True
   self.fire = True
   
  self.frame_index = 0
  self.state = c.WALK
  self.image = self.right_frames[self.frame_index]
  self.rect = self.image.get_rect()

 def restart(self):
  '''restart after player is dead or go to next level'''
  if self.dead:
   self.dead = False
   self.big = False
   self.fire = False
   self.set_player_image(self.small_normal_frames, 0)
   self.right_frames = self.small_normal_frames[0]
   self.left_frames = self.small_normal_frames[1]
  self.state = c.STAND

 def load_data(self):
  player_file = str(self.player_name) + '.json'
  file_path = os.path.join('source', 'data', 'player', player_file)
  f = open(file_path)
  self.player_data = json.load(f)

 def setup_timer(self):
  self.walking_timer = 0
  self.death_timer = 0
  self.flagpole_timer = 0
  self.transition_timer = 0
  self.hurt_invincible_timer = 0
  self.invincible_timer = 0
  self.last_fireball_time = 0

 def setup_state(self):
  self.facing_right = True
  self.allow_jump = True
  self.allow_fireball = True
  self.dead = False
  self.big = False
  self.fire = False
  self.hurt_invincible = False
  self.invincible = False
  self.crouching = False

 def setup_speed(self):
  speed = self.player_data[c.PLAYER_SPEED]
  self.x_vel = 0
  self.y_vel = 0
  
  self.max_walk_vel = speed[c.MAX_WALK_SPEED]
  self.max_run_vel = speed[c.MAX_RUN_SPEED]
  self.max_y_vel = speed[c.MAX_Y_VEL]
  self.walk_accel = speed[c.WALK_ACCEL]
  self.run_accel = speed[c.RUN_ACCEL]
  self.jump_vel = speed[c.JUMP_VEL]
  
  self.gravity = c.GRAVITY
  self.max_x_vel = self.max_walk_vel
  self.x_accel = self.walk_accel

 def load_images(self):
  sheet = setup.GFX['mario_bros']
  frames_list = self.player_data[c.PLAYER_FRAMES]

  self.right_frames = []
  self.left_frames = []

  self.right_small_normal_frames = []
  self.left_small_normal_frames = []
  self.right_big_normal_frames = []
  self.left_big_normal_frames = []
  self.right_big_fire_frames = []
  self.left_big_fire_frames = []
  
  for name, frames in frames_list.items():
   for frame in frames:
    image = tools.get_image(sheet, frame['x'], frame['y'], 
         frame['width'], frame['height'],
         c.BLACK, c.SIZE_MULTIPLIER)
    left_image = pg.transform.flip(image, True, False)

    if name == c.RIGHT_SMALL_NORMAL:
     self.right_small_normal_frames.append(image)
     self.left_small_normal_frames.append(left_image)
    elif name == c.RIGHT_BIG_NORMAL:
     self.right_big_normal_frames.append(image)
     self.left_big_normal_frames.append(left_image)
    elif name == c.RIGHT_BIG_FIRE:
     self.right_big_fire_frames.append(image)
     self.left_big_fire_frames.append(left_image)
  
  self.small_normal_frames = [self.right_small_normal_frames,
         self.left_small_normal_frames]
  self.big_normal_frames = [self.right_big_normal_frames,
         self.left_big_normal_frames]
  self.big_fire_frames = [self.right_big_fire_frames,
         self.left_big_fire_frames]
         
  self.all_images = [self.right_small_normal_frames,
       self.left_small_normal_frames,
       self.right_big_normal_frames,
       self.left_big_normal_frames,
       self.right_big_fire_frames,
       self.left_big_fire_frames]
  
  self.right_frames = self.small_normal_frames[0]
  self.left_frames = self.small_normal_frames[1]

 def update(self, keys, game_info, fire_group):
  self.current_time = game_info[c.CURRENT_TIME]
  self.handle_state(keys, fire_group)
  self.check_if_hurt_invincible()
  self.check_if_invincible()
  self.animation()

 def handle_state(self, keys, fire_group):
  if self.state == c.STAND:
   self.standing(keys, fire_group)
  elif self.state == c.WALK:
   self.walking(keys, fire_group)
  elif self.state == c.JUMP:
   self.jumping(keys, fire_group)
  elif self.state == c.FALL:
   self.falling(keys, fire_group)
  elif self.state == c.DEATH_JUMP:
   self.jumping_to_death()
  elif self.state == c.FLAGPOLE:
   self.flag_pole_sliding()
  elif self.state == c.WALK_AUTO:
   self.walking_auto()
  elif self.state == c.END_OF_LEVEL_FALL:
   self.y_vel += self.gravity
  elif self.state == c.IN_CASTLE:
   self.frame_index = 0
  elif self.state == c.SMALL_TO_BIG:
   self.changing_to_big()
  elif self.state == c.BIG_TO_SMALL:
   self.changing_to_small()
  elif self.state == c.BIG_TO_FIRE:
   self.changing_to_fire()
  elif self.state == c.DOWN_TO_PIPE:
   self.y_vel = 1
   self.rect.y += self.y_vel
  elif self.state == c.UP_OUT_PIPE:
   self.y_vel = -1
   self.rect.y += self.y_vel
   if self.rect.bottom < self.up_pipe_y:
    self.state = c.STAND

 def check_to_allow_jump(self, keys):
  if not keys[tools.keybinding['jump']]:
   self.allow_jump = True
 
 def check_to_allow_fireball(self, keys):
  if not keys[tools.keybinding['action']]:
   self.allow_fireball = True

 def standing(self, keys, fire_group):
  self.check_to_allow_jump(keys)
  self.check_to_allow_fireball(keys)
  
  self.frame_index = 0
  self.x_vel = 0
  self.y_vel = 0
  
  if keys[tools.keybinding['action']]:
   if self.fire and self.allow_fireball:
    self.shoot_fireball(fire_group)

  if keys[tools.keybinding['down']]:
   self.update_crouch_or_not(True)

  if keys[tools.keybinding['left']]:
   self.facing_right = False
   self.update_crouch_or_not()
   self.state = c.WALK
  elif keys[tools.keybinding['right']]:
   self.facing_right = True
   self.update_crouch_or_not()
   self.state = c.WALK
  elif keys[tools.keybinding['jump']]:
   if self.allow_jump:
    self.state = c.JUMP
    self.y_vel = self.jump_vel
  
  if not keys[tools.keybinding['down']]:
   self.update_crouch_or_not()

 def update_crouch_or_not(self, isDown=False):
  if not self.big:
   self.crouching = True if isDown else False
   return
  if not isDown and not self.crouching:
   return
  
  self.crouching = True if isDown else False
  frame_index = 7 if isDown else 0 
  bottom = self.rect.bottom
  left = self.rect.x
  if self.facing_right:
   self.image = self.right_frames[frame_index]
  else:
   self.image = self.left_frames[frame_index]
  self.rect = self.image.get_rect()
  self.rect.bottom = bottom
  self.rect.x = left
  self.frame_index = frame_index

 def walking(self, keys, fire_group):
  self.check_to_allow_jump(keys)
  self.check_to_allow_fireball(keys)

  if self.frame_index == 0:
   self.frame_index += 1
   self.walking_timer = self.current_time
  elif (self.current_time - self.walking_timer >
     self.calculate_animation_speed()):
   if self.frame_index < 3:
    self.frame_index += 1
   else:
    self.frame_index = 1
   self.walking_timer = self.current_time
  
  if keys[tools.keybinding['action']]:
   self.max_x_vel = self.max_run_vel
   self.x_accel = self.run_accel
   if self.fire and self.allow_fireball:
    self.shoot_fireball(fire_group)
  else:
   self.max_x_vel = self.max_walk_vel
   self.x_accel = self.walk_accel
  
  if keys[tools.keybinding['jump']]:
   if self.allow_jump:
    self.state = c.JUMP
    if abs(self.x_vel) > 4:
     self.y_vel = self.jump_vel - .5
    else:
     self.y_vel = self.jump_vel
    

  if keys[tools.keybinding['left']]:
   self.facing_right = False
   if self.x_vel > 0:
    self.frame_index = 5
    self.x_accel = c.SMALL_TURNAROUND
   
   self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel, True)
  elif keys[tools.keybinding['right']]:
   self.facing_right = True
   if self.x_vel < 0:
    self.frame_index = 5
    self.x_accel = c.SMALL_TURNAROUND
   
   self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
  else:
   if self.facing_right:
    if self.x_vel > 0:
     self.x_vel -= self.x_accel
    else:
     self.x_vel = 0
     self.state = c.STAND
   else:
    if self.x_vel < 0:
     self.x_vel += self.x_accel
    else:
     self.x_vel = 0
     self.state = c.STAND

 def jumping(self, keys, fire_group):
  """ y_vel value: positive is down, negative is up """
  self.check_to_allow_fireball(keys)
  
  self.allow_jump = False
  self.frame_index = 4
  self.gravity = c.JUMP_GRAVITY
  self.y_vel += self.gravity
  
  if self.y_vel >= 0 and self.y_vel < self.max_y_vel:
   self.gravity = c.GRAVITY
   self.state = c.FALL

  if keys[tools.keybinding['right']]:
   self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
  elif keys[tools.keybinding['left']]:
   self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel, True)
  
  if not keys[tools.keybinding['jump']]:
   self.gravity = c.GRAVITY
   self.state = c.FALL
  
  if keys[tools.keybinding['action']]:
   if self.fire and self.allow_fireball:
    self.shoot_fireball(fire_group)

 def falling(self, keys, fire_group):
  self.check_to_allow_fireball(keys)
  self.y_vel = self.cal_vel(self.y_vel, self.max_y_vel, self.gravity)
  
  if keys[tools.keybinding['right']]:
   self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
  elif keys[tools.keybinding['left']]:
   self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel, True)
  
  if keys[tools.keybinding['action']]:
   if self.fire and self.allow_fireball:
    self.shoot_fireball(fire_group)
 
 def jumping_to_death(self):
  if self.death_timer == 0:
   self.death_timer = self.current_time
  elif (self.current_time - self.death_timer) > 500:
   self.rect.y += self.y_vel
   self.y_vel += self.gravity

 def cal_vel(self, vel, max_vel, accel, isNegative=False):
  """ max_vel and accel must > 0 """
  if isNegative:
   new_vel = vel * -1
  else:
   new_vel = vel
  if (new_vel + accel) < max_vel:
   new_vel += accel
  else:
   new_vel = max_vel
  if isNegative:
   return new_vel * -1
  else:
   return new_vel

 def calculate_animation_speed(self):
  if self.x_vel == 0:
   animation_speed = 130
  elif self.x_vel > 0:
   animation_speed = 130 - (self.x_vel * 13)
  else:
   animation_speed = 130 - (self.x_vel * 13 * -1)
  return animation_speed

 def shoot_fireball(self, powerup_group):
  if (self.current_time - self.last_fireball_time) > 500:
   self.allow_fireball = False
   powerup_group.add(powerup.FireBall(self.rect.right, 
       self.rect.y, self.facing_right))
   self.last_fireball_time = self.current_time
   self.frame_index = 6

 def flag_pole_sliding(self):
  self.state = c.FLAGPOLE
  self.x_vel = 0
  self.y_vel = 5

  if self.flagpole_timer == 0:
   self.flagpole_timer = self.current_time
  elif self.rect.bottom < 493:
   if (self.current_time - self.flagpole_timer) < 65:
    self.frame_index = 9
   elif (self.current_time - self.flagpole_timer) < 130:
    self.frame_index = 10
   else:
    self.flagpole_timer = self.current_time
  elif self.rect.bottom >= 493:
   self.frame_index = 10

 def walking_auto(self):
  self.max_x_vel = 5
  self.x_accel = self.walk_accel
  
  self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
  
  if (self.walking_timer == 0 or (self.current_time - self.walking_timer) > 200):
   self.walking_timer = self.current_time
  elif (self.current_time - self.walking_timer >
     self.calculate_animation_speed()):
   if self.frame_index < 3:
    self.frame_index += 1
   else:
    self.frame_index = 1
   self.walking_timer = self.current_time

 def changing_to_big(self):
  timer_list = [135, 200, 365, 430, 495, 560, 625, 690, 755, 820, 885]
  # size value 0:small, 1:middle, 2:big
  size_list = [1, 0, 1, 0, 1, 2, 0, 1, 2, 0, 2]
  frames = [(self.small_normal_frames, 0), (self.small_normal_frames, 7),
     (self.big_normal_frames, 0)]
  if self.transition_timer == 0:
   self.big = True
   self.change_index = 0
   self.transition_timer = self.current_time
  elif (self.current_time - self.transition_timer) > timer_list[self.change_index]:
   if (self.change_index + 1) >= len(timer_list):
    # player becomes big
    self.transition_timer = 0
    self.set_player_image(self.big_normal_frames, 0)
    self.state = c.WALK
    self.right_frames = self.right_big_normal_frames
    self.left_frames = self.left_big_normal_frames
   else:
    frame, frame_index = frames[size_list[self.change_index]]
    self.set_player_image(frame, frame_index)
   self.change_index += 1

 def changing_to_small(self):
  timer_list = [265, 330, 395, 460, 525, 590, 655, 720, 785, 850, 915]
  # size value 0:big, 1:middle, 2:small
  size_list = [0, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
  frames = [(self.big_normal_frames, 4), (self.big_normal_frames, 8),
     (self.small_normal_frames, 8)]

  if self.transition_timer == 0:
   self.change_index = 0
   self.transition_timer = self.current_time
  elif (self.current_time - self.transition_timer) > timer_list[self.change_index]:
   if (self.change_index + 1) >= len(timer_list):
    # player becomes small
    self.transition_timer = 0
    self.set_player_image(self.small_normal_frames, 0)
    self.state = c.WALK
    self.big = False
    self.fire = False
    self.hurt_invincible = True
    self.right_frames = self.right_small_normal_frames
    self.left_frames = self.left_small_normal_frames
   else:
    frame, frame_index = frames[size_list[self.change_index]]
    self.set_player_image(frame, frame_index)
   self.change_index += 1

 def changing_to_fire(self):
  timer_list = [65, 195, 260, 325, 390, 455, 520, 585, 650, 715, 780, 845, 910, 975]
  # size value 0:fire, 1:big green, 2:big red, 3:big black
  size_list = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
  frames = [(self.big_fire_frames, 3), (self.big_normal_frames, 3),
     (self.big_fire_frames, 3), (self.big_normal_frames, 3)]
     
  if self.transition_timer == 0:
   self.change_index = 0
   self.transition_timer = self.current_time
  elif (self.current_time - self.transition_timer) > timer_list[self.change_index]:
   if (self.change_index + 1) >= len(timer_list):
    # player becomes fire
    self.transition_timer = 0
    self.set_player_image(self.big_fire_frames, 3)
    self.fire = True
    self.state = c.WALK
    self.right_frames = self.right_big_fire_frames
    self.left_frames = self.left_big_fire_frames
   else:
    frame, frame_index = frames[size_list[self.change_index]]
    self.set_player_image(frame, frame_index)
   self.change_index += 1

 def set_player_image(self, frames, frame_index):
  self.frame_index = frame_index
  if self.facing_right:
   self.right_frames = frames[0]
   self.image = frames[0][frame_index]
  else:
   self.left_frames = frames[1]
   self.image = frames[1][frame_index]
  bottom = self.rect.bottom
  centerx = self.rect.centerx
  self.rect = self.image.get_rect()
  self.rect.bottom = bottom
  self.rect.centerx = centerx

 def check_if_hurt_invincible(self):
  if self.hurt_invincible:
   if self.hurt_invincible_timer == 0:
    self.hurt_invincible_timer = self.current_time
    self.hurt_invincible_timer2 = self.current_time
   elif (self.current_time - self.hurt_invincible_timer) < 2000:
    if (self.current_time - self.hurt_invincible_timer2) < 35:
     self.image.set_alpha(0)
    elif (self.current_time - self.hurt_invincible_timer2) < 70:
     self.image.set_alpha(255)
     self.hurt_invincible_timer2 = self.current_time
   else:
    self.hurt_invincible = False
    self.hurt_invincible_timer = 0
    for frames in self.all_images:
     for image in frames:
      image.set_alpha(255)

 def check_if_invincible(self):
  if self.invincible:
   if self.invincible_timer == 0:
    self.invincible_timer = self.current_time
    self.invincible_timer2 = self.current_time
   elif (self.current_time - self.invincible_timer) < 10000:
    if (self.current_time - self.invincible_timer2) < 35:
     self.image.set_alpha(0)
    elif (self.current_time - self.invincible_timer2) < 70:
     self.image.set_alpha(255)
     self.invincible_timer2 = self.current_time
   elif (self.current_time - self.invincible_timer) < 12000:
    if (self.current_time - self.invincible_timer2) < 100:
     self.image.set_alpha(0)
    elif (self.current_time - self.invincible_timer2) < 200:
     self.image.set_alpha(255)
     self.invincible_timer2 = self.current_time
   else:
    self.invincible = False
    self.invincible_timer = 0
    for frames in self.all_images:
     for image in frames:
      image.set_alpha(255)

 def animation(self):
  if self.facing_right:
   self.image = self.right_frames[self.frame_index]
  else:
   self.image = self.left_frames[self.frame_index]

 def start_death_jump(self, game_info):
  self.dead = True
  self.y_vel = -11
  self.gravity = .5
  self.frame_index = 6
  self.state = c.DEATH_JUMP
敌人

__author__ = 'marble_xu'

import math
import pygame as pg
from .. import setup, tools
from .. import constants as c

ENEMY_SPEED = 1

def create_enemy(item, level):
 dir = c.LEFT if item['direction'] == 0 else c.RIGHT
 color = item[c.COLOR]
 if c.ENEMY_RANGE in item:
  in_range = item[c.ENEMY_RANGE]
  range_start = item['range_start']
  range_end = item['range_end']
 else:
  in_range = False
  range_start = range_end = 0

 if item['type'] == c.ENEMY_TYPE_GOOMBA:
  sprite = Goomba(item['x'], item['y'], dir, color,
   in_range, range_start, range_end)
 elif item['type'] == c.ENEMY_TYPE_KOOPA:
  sprite = Koopa(item['x'], item['y'], dir, color,
   in_range, range_start, range_end)
 elif item['type'] == c.ENEMY_TYPE_FLY_KOOPA:
  isVertical = False if item['is_vertical'] == 0 else True
  sprite = FlyKoopa(item['x'], item['y'], dir, color,
   in_range, range_start, range_end, isVertical)
 elif item['type'] == c.ENEMY_TYPE_PIRANHA:
  sprite = Piranha(item['x'], item['y'], dir, color,
   in_range, range_start, range_end)
 elif item['type'] == c.ENEMY_TYPE_FIRE_KOOPA:
  sprite = FireKoopa(item['x'], item['y'], dir, color,
   in_range, range_start, range_end, level)
 elif item['type'] == c.ENEMY_TYPE_FIRESTICK:
  '''use a number of fireballs to stimulate a firestick'''
  sprite = []
  num = item['num']
  center_x, center_y = item['x'], item['y']
  for i in range(num):
   radius = i * 21 # 8 * 2.69 = 21
   sprite.append(FireStick(center_x, center_y, dir, color,
    radius))
 return sprite
 
class Enemy(pg.sprite.Sprite):
 def __init__(self):
  pg.sprite.Sprite.__init__(self)
 
 def setup_enemy(self, x, y, direction, name, sheet, frame_rect_list,
      in_range, range_start, range_end, isVertical=False):
  self.frames = []
  self.frame_index = 0
  self.animate_timer = 0
  self.gravity = 1.5
  self.state = c.WALK
  
  self.name = name
  self.direction = direction
  self.load_frames(sheet, frame_rect_list)
  self.image = self.frames[self.frame_index]
  self.rect = self.image.get_rect()
  self.rect.x = x
  self.rect.bottom = y
  self.in_range = in_range
  self.range_start = range_start
  self.range_end = range_end
  self.isVertical = isVertical
  self.set_velocity()
  self.death_timer = 0
 
 def load_frames(self, sheet, frame_rect_list):
  for frame_rect in frame_rect_list:
   self.frames.append(tools.get_image(sheet, *frame_rect, 
       c.BLACK, c.SIZE_MULTIPLIER))

 def set_velocity(self):
  if self.isVertical:
   self.x_vel = 0
   self.y_vel = ENEMY_SPEED
  else:
   self.x_vel = ENEMY_SPEED *-1 if self.direction == c.LEFT else ENEMY_SPEED
   self.y_vel = 0
 
 def update(self, game_info, level):
  self.current_time = game_info[c.CURRENT_TIME]
  self.handle_state()
  self.animation()
  self.update_position(level)

 def handle_state(self):
  if (self.state == c.WALK or
   self.state == c.FLY):
   self.walking()
  elif self.state == c.FALL:
   self.falling()
  elif self.state == c.JUMPED_ON:
   self.jumped_on()
  elif self.state == c.DEATH_JUMP:
   self.death_jumping()
  elif self.state == c.SHELL_SLIDE:
   self.shell_sliding()
  elif self.state == c.REVEAL:
   self.revealing()
 
 def walking(self):
  if (self.current_time - self.animate_timer) > 125:
   if self.direction == c.RIGHT:
    if self.frame_index == 4:
     self.frame_index += 1
    elif self.frame_index == 5:
     self.frame_index = 4
   else:
    if self.frame_index == 0:
     self.frame_index += 1
    elif self.frame_index == 1:
     self.frame_index = 0
   self.animate_timer = self.current_time
 
 def falling(self):
  if self.y_vel < 10:
   self.y_vel += self.gravity
 
 def jumped_on(self):
  pass

 def death_jumping(self):
  self.rect.y += self.y_vel
  self.rect.x += self.x_vel
  self.y_vel += self.gravity
  if self.rect.y > c.SCREEN_HEIGHT:
   self.kill()

 def shell_sliding(self):
  if self.direction == c.RIGHT:
   self.x_vel = 10
  else:
   self.x_vel = -10

 def revealing(self):
  pass

 def start_death_jump(self, direction):
  self.y_vel = -8
  self.x_vel = 2 if direction == c.RIGHT else -2
  self.gravity = .5
  self.frame_index = 3
  self.state = c.DEATH_JUMP

 def animation(self):
  self.image = self.frames[self.frame_index]
 
 def update_position(self, level):
  self.rect.x += self.x_vel
  self.check_x_collisions(level)

  if self.in_range and self.isVertical:
   if self.rect.y < self.range_start:
    self.rect.y = self.range_start
    self.y_vel = ENEMY_SPEED
   elif self.rect.bottom > self.range_end:
    self.rect.bottom = self.range_end
    self.y_vel = -1 * ENEMY_SPEED

  self.rect.y += self.y_vel
  if (self.state != c.DEATH_JUMP and 
   self.state != c.FLY):
   self.check_y_collisions(level)
  
  if self.rect.x <= 0:
   self.kill()
  elif self.rect.y > (level.viewport.bottom):
   self.kill()
 
 def check_x_collisions(self, level):
  if self.in_range and not self.isVertical:
   if self.rect.x < self.range_start:
    self.rect.x = self.range_start
    self.change_direction(c.RIGHT)
   elif self.rect.right > self.range_end:
    self.rect.right = self.range_end
    self.change_direction(c.LEFT)
  else:
   collider = pg.sprite.spritecollideany(self, level.ground_step_pipe_group)
   if collider:
    if self.direction == c.RIGHT:
     self.rect.right = collider.rect.left
     self.change_direction(c.LEFT)
    elif self.direction == c.LEFT:
     self.rect.left = collider.rect.right
     self.change_direction(c.RIGHT)

  if self.state == c.SHELL_SLIDE:
   enemy = pg.sprite.spritecollideany(self, level.enemy_group)
   if enemy:
    level.update_score(100, enemy, 0)
    level.move_to_dying_group(level.enemy_group, enemy)
    enemy.start_death_jump(self.direction)

 def change_direction(self, direction):
  self.direction = direction
  if self.direction == c.RIGHT:
   self.x_vel = ENEMY_SPEED
   if self.state == c.WALK or self.state == c.FLY:
    self.frame_index = 4
  else:
   self.x_vel = ENEMY_SPEED * -1
   if self.state == c.WALK or self.state == c.FLY:
    self.frame_index = 0

 def check_y_collisions(self, level):
  # decrease runtime delay: when enemey is on the ground, don't check brick and box
  if self.rect.bottom >= c.GROUND_HEIGHT:
   sprite_group = level.ground_step_pipe_group
  else:
   sprite_group = pg.sprite.Group(level.ground_step_pipe_group,
       level.brick_group, level.box_group)
  sprite = pg.sprite.spritecollideany(self, sprite_group)
  if sprite and sprite.name != c.MAP_SLIDER:
   if self.rect.top <= sprite.rect.top:
    self.rect.bottom = sprite.rect.y
    self.y_vel = 0
    self.state = c.WALK
  level.check_is_falling(self)

class Goomba(Enemy):
 def __init__(self, x, y, direction, color, in_range,
    range_start, range_end, name=c.GOOMBA):
  Enemy.__init__(self)
  frame_rect_list = self.get_frame_rect(color)
  self.setup_enemy(x, y, direction, name, setup.GFX[c.ENEMY_SHEET],
     frame_rect_list, in_range, range_start, range_end)
  # dead jump image
  self.frames.append(pg.transform.flip(self.frames[2], False, True))
  # right walk images
  self.frames.append(pg.transform.flip(self.frames[0], True, False))
  self.frames.append(pg.transform.flip(self.frames[1], True, False))

 def get_frame_rect(self, color):
  if color == c.COLOR_TYPE_GREEN:
   frame_rect_list = [(0, 34, 16, 16), (30, 34, 16, 16), 
      (61, 30, 16, 16)]
  else:
   frame_rect_list = [(0, 4, 16, 16), (30, 4, 16, 16), 
      (61, 0, 16, 16)]
  return frame_rect_list

 def jumped_on(self):
  self.x_vel = 0
  self.frame_index = 2
  if self.death_timer == 0:
   self.death_timer = self.current_time
  elif (self.current_time - self.death_timer) > 500:
   self.kill()

class Koopa(Enemy):
 def __init__(self, x, y, direction, color, in_range,
    range_start, range_end, name=c.KOOPA):
  Enemy.__init__(self)
  frame_rect_list = self.get_frame_rect(color)
  self.setup_enemy(x, y, direction, name, setup.GFX[c.ENEMY_SHEET],
     frame_rect_list, in_range, range_start, range_end)
  # dead jump image
  self.frames.append(pg.transform.flip(self.frames[2], False, True))
  # right walk images
  self.frames.append(pg.transform.flip(self.frames[0], True, False))
  self.frames.append(pg.transform.flip(self.frames[1], True, False))

 def get_frame_rect(self, color):
  if color == c.COLOR_TYPE_GREEN:
   frame_rect_list = [(150, 0, 16, 24), (180, 0, 16, 24),
      (360, 5, 16, 15)]
  elif color == c.COLOR_TYPE_RED:
   frame_rect_list = [(150, 30, 16, 24), (180, 30, 16, 24),
      (360, 35, 16, 15)]
  else:
   frame_rect_list = [(150, 60, 16, 24), (180, 60, 16, 24),
      (360, 65, 16, 15)]
  return frame_rect_list

 def jumped_on(self):
  self.x_vel = 0
  self.frame_index = 2
  x = self.rect.x
  bottom = self.rect.bottom
  self.rect = self.frames[self.frame_index].get_rect()
  self.rect.x = x
  self.rect.bottom = bottom
  self.in_range = False

class FlyKoopa(Enemy):
 def __init__(self, x, y, direction, color, in_range, 
    range_start, range_end, isVertical, name=c.FLY_KOOPA):
  Enemy.__init__(self)
  frame_rect_list = self.get_frame_rect(color)
  self.setup_enemy(x, y, direction, name, setup.GFX[c.ENEMY_SHEET], 
     frame_rect_list, in_range, range_start, range_end, isVertical)
  # dead jump image
  self.frames.append(pg.transform.flip(self.frames[2], False, True))
  # right walk images
  self.frames.append(pg.transform.flip(self.frames[0], True, False))
  self.frames.append(pg.transform.flip(self.frames[1], True, False))
  self.state = c.FLY

 def get_frame_rect(self, color):
  if color == c.COLOR_TYPE_GREEN:
   frame_rect_list = [(90, 0, 16, 24), (120, 0, 16, 24), 
      (330, 5, 16, 15)]
  else:
   frame_rect_list = [(90, 30, 16, 24), (120, 30, 16, 24), 
      (330, 35, 16, 15)]
  return frame_rect_list

 def jumped_on(self):
  self.x_vel = 0
  self.frame_index = 2
  x = self.rect.x
  bottom = self.rect.bottom
  self.rect = self.frames[self.frame_index].get_rect()
  self.rect.x = x
  self.rect.bottom = bottom
  self.in_range = False
  self.isVertical = False

class FireKoopa(Enemy):
 def __init__(self, x, y, direction, color, in_range,
    range_start, range_end, level, name=c.FIRE_KOOPA):
  Enemy.__init__(self)
  frame_rect_list = [(2, 210, 32, 32), (42, 210, 32, 32),
       (82, 210, 32, 32), (122, 210, 32, 32)]
  self.setup_enemy(x, y, direction, name, setup.GFX[c.ENEMY_SHEET], 
     frame_rect_list, in_range, range_start, range_end)
  # right walk images
  self.frames.append(pg.transform.flip(self.frames[0], True, False))
  self.frames.append(pg.transform.flip(self.frames[1], True, False))
  self.frames.append(pg.transform.flip(self.frames[2], True, False))
  self.frames.append(pg.transform.flip(self.frames[3], True, False))
  self.x_vel = 0
  self.gravity = 0.3
  self.level = level
  self.fire_timer = 0
  self.jump_timer = 0

 def load_frames(self, sheet, frame_rect_list):
  for frame_rect in frame_rect_list:
   self.frames.append(tools.get_image(sheet, *frame_rect,
       c.BLACK, c.BRICK_SIZE_MULTIPLIER))

 def walking(self):
  if (self.current_time - self.animate_timer) > 250:
   if self.direction == c.RIGHT:
    self.frame_index += 1
    if self.frame_index > 7:
     self.frame_index = 4
   else:
    self.frame_index += 1
    if self.frame_index > 3:
     self.frame_index = 0
   self.animate_timer = self.current_time

  self.shoot_fire()
  if self.should_jump():
   self.y_vel = -7

 def falling(self):
  if self.y_vel < 7:
   self.y_vel += self.gravity
  self.shoot_fire()

 def should_jump(self):
  if (self.rect.x - self.level.player.rect.x) < 400:
   if (self.current_time - self.jump_timer) > 2500:
    self.jump_timer = self.current_time
    return True
  return False

 def shoot_fire(self):
  if (self.current_time - self.fire_timer) > 3000:
   self.fire_timer = self.current_time
   self.level.enemy_group.add(Fire(self.rect.x, self.rect.bottom-20, self.direction))

class Fire(Enemy):
 def __init__(self, x, y, direction, name=c.FIRE):
  Enemy.__init__(self)
  frame_rect_list = [(101, 253, 23, 8), (131, 253, 23, 8)]
  in_range, range_start, range_end = False, 0, 0
  self.setup_enemy(x, y, direction, name, setup.GFX[c.ENEMY_SHEET], 
     frame_rect_list, in_range, range_start, range_end)
  # right images
  self.frames.append(pg.transform.flip(self.frames[0], True, False))
  self.frames.append(pg.transform.flip(self.frames[1], True, False))
  self.state = c.FLY
  self.x_vel = 5 if self.direction == c.RIGHT else -5

 def check_x_collisions(self, level):
  sprite_group = pg.sprite.Group(level.ground_step_pipe_group,
       level.brick_group, level.box_group)
  sprite = pg.sprite.spritecollideany(self, sprite_group)
  if sprite:
   self.kill()

 def start_death_jump(self, direction):
  self.kill()

class Piranha(Enemy):
 def __init__(self, x, y, direction, color, in_range, 
    range_start, range_end, name=c.PIRANHA):
  Enemy.__init__(self)
  frame_rect_list = self.get_frame_rect(color)
  self.setup_enemy(x, y, direction, name, setup.GFX[c.ENEMY_SHEET], 
     frame_rect_list, in_range, range_start, range_end)
  self.state = c.REVEAL
  self.y_vel = 1
  self.wait_timer = 0
  self.group = pg.sprite.Group()
  self.group.add(self)
  
 def get_frame_rect(self, color):
  if color == c.COLOR_TYPE_GREEN:
   frame_rect_list = [(390, 30, 16, 24), (420, 30, 16, 24)]
  else:
   frame_rect_list = [(390, 60, 16, 24), (420, 60, 16, 24)]
  return frame_rect_list

 def revealing(self):
  if (self.current_time - self.animate_timer) > 250:
   if self.frame_index == 0:
    self.frame_index += 1
   elif self.frame_index == 1:
    self.frame_index = 0
   self.animate_timer = self.current_time

 def update_position(self, level):
  if self.check_player_is_on(level):
   pass
  else:
   if self.rect.y < self.range_start:
    self.rect.y = self.range_start
    self.y_vel = 1
   elif self.rect.bottom > self.range_end:
    if self.wait_timer == 0:
     self.wait_timer = self.current_time
    elif (self.current_time - self.wait_timer) < 3000:
     return
    else:
     self.wait_timer = 0
     self.rect.bottom = self.range_end
     self.y_vel = -1
   self.rect.y += self.y_vel

 def check_player_is_on(self, level):
  result = False
  self.rect.y -= 5
  sprite = pg.sprite.spritecollideany(level.player, self.group)
  if sprite:
   result = True
  self.rect.y += 5
  return result

 def start_death_jump(self, direction):
  self.kill()

class FireStick(pg.sprite.Sprite):
 def __init__(self, center_x, center_y, direction, color, radius, name=c.FIRESTICK):
  '''the firestick will rotate around the center of a circle'''
  pg.sprite.Sprite.__init__(self)

  self.frames = []
  self.frame_index = 0
  self.animate_timer = 0
  self.name = name
  rect_list = [(96, 144, 8, 8), (104, 144, 8, 8),
     (96, 152, 8, 8), (104, 152, 8, 8)]
  self.load_frames(setup.GFX[c.ITEM_SHEET], rect_list)
  self.animate_timer = 0
  self.image = self.frames[self.frame_index]
  self.rect = self.image.get_rect()
  self.rect.x = center_x - radius
  self.rect.y = center_y
  self.center_x = center_x
  self.center_y = center_y
  self.radius = radius
  self.angle = 0

 def load_frames(self, sheet, frame_rect_list):
  for frame_rect in frame_rect_list:
   self.frames.append(tools.get_image(sheet, *frame_rect, 
       c.BLACK, c.BRICK_SIZE_MULTIPLIER))

 def update(self, game_info, level):
  self.current_time = game_info[c.CURRENT_TIME]
  if (self.current_time - self.animate_timer) > 100:
   if self.frame_index < 3:
    self.frame_index += 1
   else:
    self.frame_index = 0
   self.animate_timer = self.current_time
  self.image = self.frames[self.frame_index]

  self.angle += 1
  if self.angle == 360:
   self.angle = 0
  radian = math.radians(self.angle)
  self.rect.x = self.center_x + math.sin(radian) * self.radius
  self.rect.y = self.center_y + math.cos(radian) * self.radius
