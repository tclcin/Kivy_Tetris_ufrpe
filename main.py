from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from game import *
from kivy.lang import Builder
from kivy.uix.label import Label 
from kivy.uix.slider import Slider
from kivy.core.audio import SoundLoader

### Comentários descrevem adições ou alterações sobre o código original

class GameScreen(Screen): # janela onde o jogo em si acontece
    def __init__(self, diff,**kwargs):
        super(GameScreen, self).__init__(**kwargs)         
        
        self.diff = diff
        gamebox = GameBox(dificuldade=self.diff)
        self.add_widget(gamebox)
        
                

class MenuScreen(Screen): # Tela de Menu do jogo                     
   pass

class SplashScreen(Screen): # Splash Screen 
    pass

class AppManager(ScreenManager): # Gerenciador de janelas por trás do app
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
   
    def change_to_menu(self, dt):
        self.current = 'ms'
   
    def change_to_game(self):
        self.current = 'game'
    
    def create_gamescreen(self, dificuldade):
        self.add_widget(GameScreen(name='game', diff=dificuldade))
        self.change_to_game()

      

class MainApp(App): # definição do loop principal do app
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sm = Builder.load_file('janelas.kv')
    def build(self):
        return self.sm
    
    def on_start(self):
        Clock.schedule_once(self.sm.change_to_menu, 4)




class GameBox(BoxLayout): ## Mudança de nome de GameScreen para GameBox para melhor refletir o que a classe representa                    
    board = ObjectProperty(None)
    sidebar = ObjectProperty(None)


    def __init__(self, dificuldade, **kwargs):
        super(GameBox, self).__init__(**kwargs)
        self.game_state = GameState()
        self.board.set_game_state(self.game_state)
        self.sidebar.set_game_state(self.game_state)
        self.bind(pos=self.redraw)
        self.bind(size=self.redraw)
        self.diff = dificuldade
        self.collision_sfx_count = 0
        self.sound_fx_player = SoundEffectLoader()
        self.musicloader = MusicLoader()
        self.music = self.musicloader.choose_music(self.diff)
        self.music.loop = True
        self.music.volume = 0.3
        

    def start_game(self, *args):
        Clock.unschedule(self.tick)
        self.music.play()
        self.game_state.reset()
        self.game_state.start()
        self.tick()
        self.collision_sfx_count = 0 

    def tick(self, *args):
        if not self.game_state.is_game_over():
            self.game_state.tick()
            delay = max(10 - (self.diff+self.game_state.level), 1) * .05
            Clock.schedule_once(self.tick, delay)
        else:
            self.music.stop()
        if self.collisions_difference_calc():
            self.sound_fx_player.choose_sound_effect('fall').play()
            self.collision_sfx_count += 1
        self.redraw()

    def redraw(self, *args):
        self.sidebar.refresh(self.game_state)
        self.board.redraw()
        

    def calculate_board_size(self):
        height = self.board.height - 20
        width = height / 2
        if width > self.board.width:
            width = self.board.width - 20
            height = self.board.width * 2
            x = 0
            y = (self.board.height - height) / 2

        x = (self.board.width - width) / 2
        y = (self.board.height - height) / 2
        return x, y, width, height

    def block_size(self):
        board_x, board_y, board_width, board_height = \
            self.calculate_board_size()
        block_width = board_width / GRID_WIDTH - 1
        block_height = board_height / (GRID_HEIGHT - 2) - 1
        return block_width, block_height

    def collisions_difference_calc(self):
        if abs(self.collision_sfx_count - self.game_state.collisions) > 0:    
         return True
        else:
            return False
        

class MusicLoader(SoundLoader):
    def __init__(self) -> None:
        super().__init__()


    def choose_music(self, diff):
        if diff <= 2:
            music = self.load("./assets/music/easytheme.mp3")
        elif 3 <= diff <= 6:
            music = self.load("./assets/music/medio-theme.mp3")
        elif 7 <= diff <= 9:
            music = self.load("./assets/music/hard-7-9-theme.mp3")
        else:
            music = self.load("./assets/music/lvl-10-theme.mp3")
        
        return music

class SoundEffectLoader(SoundLoader):
    def __init__(self) -> None:
        super().__init__()
    
    def choose_sound_effect(self, event):
        sound_fx = self.load(f'./assets/sounds/{event}.wav')
        if sound_fx:
            return sound_fx

class Board(Widget):
    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self.on_touch_down)
        self.bind(pos=self.redraw)
        self.bind(size=self.redraw)
        self.game_state = None
        self.sound_fx_player = SoundEffectLoader()

    def set_game_state(self, game_state):
        self.game_state = game_state

    def on_touch_down(self, keyboard, keycode, text, modifiers):
        if not self.game_state or self.game_state.status != GameStatus.ACTIVE:
            return
        # if event.x > self.width * .75:
        if keycode[1] == "right":
            self.game_state.move_right()
        # elif event.x < self.width * .25:
        elif keycode[1] == "left":
            self.game_state.move_left()
        # elif event.y < self.height * .25:
        elif keycode[1] == "down":
            self.game_state.move_down()
        elif keycode[1] == "up":
            self.game_state.rotate()
        self.redraw()
        

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None



    def redraw(self, *args):
        self.canvas.before.clear()
        self.canvas.clear()
        board_x, board_y, board_width, board_height = self.parent.calculate_board_size()
        block_width, block_height = self.parent.block_size()

        with self.canvas.before:
            Color(0.5, 0.5, 0.5, 1)
            Line(width=2.,
                 rectangle=(board_x - 2, board_y - 2, board_width + 3,
                            board_height + 3))

        if not self.game_state:
            return

        with self.canvas:
            cur_y = board_y + (GRID_HEIGHT - 3) * (block_height + 1)
            for row in self.game_state.grid[2:]:
                cur_x = board_x
                for col in row:
                    Color(*BlockColor.to_color(col))
                    Rectangle(pos=(cur_x, cur_y),
                              size=(block_width, block_height))
                    cur_x += block_width + 1
                cur_y -= block_height + 1

            current_piece = self.game_state.current_piece
            if not current_piece:
                return
            squares = current_piece.shape()
            Color(*BlockColor.to_color(current_piece.piece_type))
            for square in squares:
                row, col = square
                if row < 2:
                    continue
                Rectangle(pos=(board_x + col * (block_width + 1),
                               board_y + (GRID_HEIGHT - row - 1) * (block_height + 1)),
                          size=(block_width, block_height))

        if self.game_state.status == GameStatus.GAME_OVER:
            self.sound_fx_player.choose_sound_effect("gameover").play()
            with self.canvas:
                Color(0, 0, 0, 0.5)
                Rectangle(pos=(board_x, board_y),
                          size=(board_width, board_height))
        

class Sidebar(BoxLayout):
    score = ObjectProperty()
    level = ObjectProperty(None)
    lines_cleared = ObjectProperty(None)
    next_piece = ObjectProperty(None)
    start_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Sidebar, self).__init__(**kwargs)
        self.bind(pos=self.refresh)
        self.bind(size=self.refresh)
        self.game_state = None

    def set_game_state(self, game_state):
        self.game_state = game_state

    def refresh(self, *args):
        self.score.text = str(self.game_state.score)
        self.level.text = str(self.game_state.level)
        self.lines_cleared.text = str(self.game_state.lines_cleared)
        self.render_next_piece()
        if self.game_state.status == GameStatus.ACTIVE:
            self.start_button.disabled = True
        else:
            self.start_button.disabled = False
       
    def render_next_piece(self):
        next_piece = self.next_piece
        next_piece.canvas.before.clear()
        next_piece.canvas.clear()
        if not self.game_state or self.game_state.status != GameStatus.ACTIVE:
            return
        block_width, block_height = self.parent.block_size()

        # A little smaller to fit in the sidebar
        block_width *= .7
        block_height *= .7

        # Dimensions of the preview box (not using the full widget space)
        width = (block_width + 1) * 4
        height = (block_height + 1) * 3
        x = next_piece.x + (next_piece.width - width) / 2
        y = next_piece.y + next_piece.height - height


        with next_piece.canvas.before:
            Color(0.5, 0.5, 0.5, 1)
            Line(width=2., rectangle=(x - 2, y - 2, width + 4, height + 4))
            Color(0., 0., 0., 1)
            Rectangle(pos=(x, y), size=(width, height))

        with next_piece.canvas:
            next_piece_type = self.game_state.piece_generator.next_piece_type()
            Color(*BlockColor.to_color(next_piece_type))
            for square in PIECE_GEOMETRY[next_piece_type][0]:
                row, col = square[0] + 1, square[1] + 1
                Rectangle(pos=(x + col * (block_width + 1),
                               y + (2 - row) * (block_height + 1)),
                          size=(block_width, block_height))
        




if __name__ == '__main__':
    MainApp().run()
