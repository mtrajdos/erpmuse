"""Manages all UI elements and their visibility"""
import os
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.logger import Logger

class TouchableFloatLayout(FloatLayout):
    """Float layout that handles touch events"""
    def on_touch_down(self, touch):
        if hasattr(self, 'touch_handler'):
            self.touch_handler(touch)
        return super().on_touch_down(touch)

class UIController:
    def __init__(self, config, param_controller):
        self.config = config
        self.param_controller = param_controller
        
        # Main layout
        self.layout = None
        
        # UI elements
        self.background_image = None
        self.fixation_cross = None
        self.instruction_label = None
        self.interruption_label = None
        self.squares = {}
        
        # Background rectangle
        self.rect = None
        
        self.create_ui()
        
    def create_ui(self):
        """Create all UI elements"""
        self.layout = TouchableFloatLayout()
        
        # Gray background
        with self.layout.canvas.before:
            Color(*self.config.BACKGROUND_COLOR)
            self.rect = Rectangle(size=Window.size, pos=(0, 0))
        
        # Create UI elements
        self._create_instruction_label()
        self._create_background_image()
        self._create_fixation_cross()
        self._create_squares()
        self._create_interruption_label()
        
        # Add widgets to layout
        self.layout.add_widget(self.background_image)
        for square in self.squares.values():
            self.layout.add_widget(square)
        self.layout.add_widget(self.fixation_cross)
        self.layout.add_widget(self.interruption_label)
        self.layout.add_widget(self.instruction_label)
        
        # Bind resize handler
        Window.bind(on_resize=self.on_window_resize)
    
    def _create_instruction_label(self):
        """Create instruction label"""
        self.instruction_label = Label(
            font_size=self.config.INSTRUCTION_FONT_SIZE,
            text_size=(Window.width * self.config.INSTRUCTION_TEXT_WIDTH_RATIO, None),
            halign='center',
            valign='middle',
            color=(1, 1, 1, 1),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0
        )
    
    def _create_background_image(self):
        """Create main stimulus image widget"""
        self.background_image = KivyImage(
            source=os.path.join(self.config.SPRITES_FOLDER, "background.png"),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=False,
            opacity=0
        )
    
    def _create_fixation_cross(self):
        """Create fixation cross"""
        self.fixation_cross = KivyImage(
            source=os.path.join(self.config.SPRITES_FOLDER, "fixation_cross.png"),
            size_hint=(None, None),
            size=(Window.width * self.config.FIXATION_SIZE_RATIO, 
                  Window.height * self.config.FIXATION_SIZE_RATIO),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=False,
            keep_ratio=True,
            opacity=0
        )
    
    def _create_squares(self):
        """Create brightness square widgets"""
        # Find all square images
        square_values = self._find_square_values()
        
        for value in square_values:
            square_name = f'square_{value}'
            square_path = os.path.join(self.config.SPRITES_FOLDER, f"{value}_square.png")
            
            widget = KivyImage(
                source=square_path,
                size_hint=(None, None),
                size=self.config.SQUARE_SIZE,
                pos=(Window.width - self.config.SQUARE_SIZE[0], 0),
                allow_stretch=False,
                keep_ratio=True,
                opacity=0
            )
            
            self.squares[square_name] = widget
    
    def _find_square_values(self):
        """Find all brightness square values from files"""
        if not os.path.exists(self.config.SPRITES_FOLDER):
            Logger.error(f"Sprites folder not found: {self.config.SPRITES_FOLDER}")
            return []
        
        all_files = os.listdir(self.config.SPRITES_FOLDER)
        square_files = [f for f in all_files if f.endswith('_square.png')]
        
        square_values = []
        for filename in square_files:
            try:
                value = int(filename.split('_')[0])
                square_values.append(value)
            except (ValueError, IndexError):
                Logger.warning(f"Could not extract value from: {filename}")
        
        square_values.sort()
        Logger.info(f"Found square values: {square_values}")
        return square_values
    
    def _create_interruption_label(self):
        """Create connection interruption label"""
        self.interruption_label = Label(
            font_size=self.config.INSTRUCTION_FONT_SIZE,
            text_size=(Window.width * self.config.INSTRUCTION_TEXT_WIDTH_RATIO, None),
            halign='center',
            valign='middle',
            color=(1, 1, 1, 1),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0
        )
        self.interruption_label.text = self.param_controller.get_text('disconnect')
    
    def preload_square_images(self, preloaded_dict):
        """Update squares with preloaded textures"""
        for square_name, widget in self.squares.items():
            if square_name in preloaded_dict:
                widget.texture = preloaded_dict[square_name].texture
    
    def show_instructions(self):
        """Show instruction screen"""
        self.instruction_label.text = self.param_controller.get_wrapped_text('instructions')
        self.instruction_label.opacity = 1
    
    def hide_instructions(self):
        """Hide instruction screen"""
        self.instruction_label.opacity = 0
    
    def show_fixation_cross(self):
        """Show fixation cross"""
        self.fixation_cross.opacity = 1
    
    def hide_fixation_cross(self):
        """Hide fixation cross"""
        self.fixation_cross.opacity = 0
    
    def show_stimulus(self, texture, square_widget):
        """Show stimulus image and brightness square"""
        self.background_image.texture = texture
        self.background_image.opacity = 1
        if square_widget:
            square_widget.opacity = 1
    
    def hide_stimulus(self, square_widget):
        """Hide stimulus and square"""
        self.background_image.opacity = 0
        if square_widget:
            square_widget.opacity = 0
    
    def show_connection_lost_screen(self):
        """Show connection lost screen"""
        self.interruption_label.opacity = 1
    
    def hide_connection_lost_screen(self):
        """Hide connection lost screen"""
        self.interruption_label.opacity = 0
    
    def hide_all_experiment_elements(self):
        """Hide all experiment UI elements"""
        self.background_image.opacity = 0
        self.fixation_cross.opacity = 0
        for square in self.squares.values():
            square.opacity = 0
    
    def get_square_widget(self, square_name):
        """Get a square widget by name"""
        return self.squares.get(square_name)
    
    def set_touch_handler(self, handler):
        """Set touch event handler"""
        self.layout.touch_handler = handler
    
    def on_window_resize(self, window, width, height):
        """Handle window resize events"""
        self.rect.size = (width, height)
        self.fixation_cross.size = (width * self.config.FIXATION_SIZE_RATIO, 
                                    height * self.config.FIXATION_SIZE_RATIO)
        self.background_image.size = (width, height)
        
        # Update square positions
        for square in self.squares.values():
            square.pos = (width - square.width, 0)
        
        # Update text sizes
        self.interruption_label.text_size = (width * self.config.INSTRUCTION_TEXT_WIDTH_RATIO, None)
        self.instruction_label.text_size = (width * self.config.INSTRUCTION_TEXT_WIDTH_RATIO, None)