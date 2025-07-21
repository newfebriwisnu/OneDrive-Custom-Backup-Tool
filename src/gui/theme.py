"""
Theme management for OneDrive Custom Backup Tool
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any


class ThemeManager:
    """Manages dark/light theme switching"""

    # Theme definitions - Modern Cyberpunk Style
    THEMES = {
        'dark': {
            'bg': '#0a0a0a',  # Deep black background
            'fg': '#ffffff',
            'accent': '#00ffff',  # Cyan accent
            'accent2': '#ff00ff',  # Magenta accent
            'accent3': '#00ff00',  # Green accent
            'success': '#00ff41',  # Bright green
            'error': '#ff0040',    # Bright red
            'warning': '#ffaa00',  # Orange
            'input_bg': '#1a1a1a',  # Dark gray
            'input_fg': '#00ffff',  # Cyan text
            'button_bg': '#1a1a1a',
            'button_fg': '#00ffff',
            'button_hover': '#262626',
            'button_active': '#00ffff',
            'border': '#333333',
            'select_bg': '#00ffff',
            'select_fg': '#0a0a0a',
            'gradient_start': '#ff00ff',  # Magenta
            'gradient_mid': '#00ffff',    # Cyan
            'gradient_end': '#00ff00',    # Green
            'neon_glow': '#00ffff',
            'secondary_bg': '#1a1a1a',
            'tertiary_bg': '#262626'
        },
        'light': {
            'bg': '#f8f8f8',
            'fg': '#1a1a1a',
            'accent': '#0078d4',
            'accent2': '#7c3aed',
            'accent3': '#059669',
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'input_bg': '#ffffff',
            'input_fg': '#1a1a1a',
            'button_bg': '#e5e7eb',
            'button_fg': '#1a1a1a',
            'button_hover': '#d1d5db',
            'button_active': '#0078d4',
            'border': '#d1d5db',
            'select_bg': '#0078d4',
            'select_fg': '#ffffff',
            'gradient_start': '#7c3aed',
            'gradient_mid': '#0078d4',
            'gradient_end': '#059669',
            'neon_glow': '#0078d4',
            'secondary_bg': '#f3f4f6',
            'tertiary_bg': '#e5e7eb'
        }
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = logging.getLogger(__name__)
        self.current_theme = 'dark'
        self.style = ttk.Style()

        # Initialize style
        self._setup_styles()

    def _setup_styles(self):
        """Setup ttk styles"""
        try:
            # Use a modern theme as base
            available_themes = self.style.theme_names()
            if 'vista' in available_themes:
                self.style.theme_use('vista')
            elif 'clam' in available_themes:
                self.style.theme_use('clam')
            elif 'alt' in available_themes:
                self.style.theme_use('alt')
            else:
                self.style.theme_use('default')

        except Exception as e:
            self.logger.error(f"Error setting up styles: {e}")

    def apply_theme(self, theme_name: str):
        """
        Apply theme to all widgets

        Args:
            theme_name: Theme name ('dark' or 'light')
        """
        try:
            if theme_name not in self.THEMES:
                self.logger.warning(f"Unknown theme: {theme_name}")
                return

            self.current_theme = theme_name
            theme = self.THEMES[theme_name]

            # Configure root window
            self.root.configure(bg=theme['bg'])

            # Configure ttk styles
            self._configure_ttk_styles(theme)

            # Update all existing widgets
            self._update_widget_colors(self.root, theme)

            self.logger.info(f"Applied theme: {theme_name}")

        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")

    def _configure_ttk_styles(self, theme: Dict[str, str]):
        """Configure ttk widget styles"""
        try:
            # Frame styles
            self.style.configure('TFrame', background=theme['bg'])

            # Label styles
            self.style.configure('TLabel',
                                 background=theme['bg'],
                                 foreground=theme['fg'])

            # Button styles
            self.style.configure('TButton',
                                 background=theme['button_bg'],
                                 foreground=theme['button_fg'],
                                 borderwidth=2,
                                 relief='solid',
                                 padding=(12, 8))

            self.style.map('TButton',
                           background=[('active', theme['button_hover']),
                                       ('pressed', theme['accent'])])

            # Entry styles
            self.style.configure('TEntry',
                                 fieldbackground=theme['input_bg'],
                                 foreground=theme['input_fg'],
                                 borderwidth=2,
                                 relief='solid')

            self.style.map('TEntry',
                           focuscolor=[('focus', theme['accent'])])

            # Progressbar styles - Cyberpunk style
            self.style.configure('TProgressbar',
                                 background=theme['accent'],
                                 troughcolor=theme['input_bg'],
                                 borderwidth=2,
                                 relief='solid',
                                 lightcolor=theme['accent2'],
                                 darkcolor=theme['accent3'])

            self.style.map('TProgressbar',
                           background=[('active', theme['accent2'])])

            # Validation styles
            self.style.configure('Valid.TEntry',
                                 fieldbackground=theme['input_bg'],
                                 foreground=theme['fg'],
                                 borderwidth=2,
                                 relief='solid')

            self.style.map('Valid.TEntry',
                           focuscolor=[('focus', theme['success'])])

            self.style.configure('Invalid.TEntry',
                                 fieldbackground=theme['input_bg'],
                                 foreground=theme['fg'],
                                 borderwidth=2,
                                 relief='solid')

            self.style.map('Invalid.TEntry',
                           focuscolor=[('focus', theme['error'])])

        except Exception as e:
            self.logger.error(f"Error configuring ttk styles: {e}")

    def _update_widget_colors(self, widget, theme: Dict[str, str]):
        """Recursively update widget colors"""
        try:
            widget_class = widget.winfo_class()

            # Update tkinter widgets
            if widget_class in ['Tk', 'Toplevel', 'Frame']:
                widget.configure(bg=theme['bg'])
            elif widget_class == 'Label':
                widget.configure(bg=theme['bg'], fg=theme['fg'])
            elif widget_class == 'Button':
                widget.configure(bg=theme['button_bg'],
                                 fg=theme['button_fg'],
                                 activebackground=theme['button_hover'],
                                 activeforeground=theme['button_fg'])
            elif widget_class == 'Entry':
                widget.configure(bg=theme['input_bg'],
                                 fg=theme['input_fg'],
                                 insertbackground=theme['fg'])
            elif widget_class == 'Text':
                widget.configure(bg=theme['input_bg'],
                                 fg=theme['input_fg'],
                                 insertbackground=theme['fg'])
            elif widget_class == 'Listbox':
                widget.configure(bg=theme['input_bg'],
                                 fg=theme['input_fg'],
                                 selectbackground=theme['select_bg'],
                                 selectforeground=theme['select_fg'])

            # Recursively update children
            for child in widget.winfo_children():
                self._update_widget_colors(child, theme)

        except Exception as e:
            # Some widgets might not support certain configurations
            pass

    def get_theme_color(self, color_name: str) -> str:
        """
        Get color value from current theme

        Args:
            color_name: Color name (e.g., 'bg', 'fg', 'accent')

        Returns:
            Color value
        """
        return self.THEMES[self.current_theme].get(color_name, '#000000')

    def create_validation_styles(self):
        """Create validation-specific styles"""
        try:
            theme = self.THEMES[self.current_theme]

            # Success style
            self.style.configure('Success.TEntry',
                                 fieldbackground=theme['input_bg'],
                                 foreground=theme['fg'],
                                 borderwidth=2,
                                 relief='solid')

            self.style.map('Success.TEntry',
                           focuscolor=[('focus', theme['success'])])

            # Error style
            self.style.configure('Error.TEntry',
                                 fieldbackground=theme['input_bg'],
                                 foreground=theme['fg'],
                                 borderwidth=2,
                                 relief='solid')

            self.style.map('Error.TEntry',
                           focuscolor=[('focus', theme['error'])])

            # Warning style
            self.style.configure('Warning.TEntry',
                                 fieldbackground=theme['input_bg'],
                                 foreground=theme['fg'],
                                 borderwidth=2,
                                 relief='solid')

            self.style.map('Warning.TEntry',
                           focuscolor=[('focus', theme['warning'])])

        except Exception as e:
            self.logger.error(f"Error creating validation styles: {e}")

    def apply_validation_style(self, widget, style_name: str):
        """
        Apply validation style to widget

        Args:
            widget: Widget to style
            style_name: Style name ('success', 'error', 'warning', 'normal')
        """
        try:
            if style_name == 'success':
                widget.configure(style='Success.TEntry')
            elif style_name == 'error':
                widget.configure(style='Error.TEntry')
            elif style_name == 'warning':
                widget.configure(style='Warning.TEntry')
            else:
                widget.configure(style='TEntry')

        except Exception as e:
            self.logger.error(f"Error applying validation style: {e}")

    def get_font_config(self, size: int = 10, weight: str = 'normal') -> tuple:
        """
        Get font configuration for Windows

        Args:
            size: Font size
            weight: Font weight ('normal', 'bold')

        Returns:
            Font configuration tuple
        """
        return ('Segoe UI', size, weight)

    def create_gradient_label(self, parent, text: str, font_size: int = 12, font_weight: str = 'bold') -> tk.Label:
        """
        Create a gradient text label with cyberpunk styling

        Args:
            parent: Parent widget
            text: Text to display
            font_size: Font size
            font_weight: Font weight

        Returns:
            Styled label widget
        """
        try:
            theme = self.THEMES[self.current_theme]

            # Create label with special styling
            label = tk.Label(
                parent,
                text=text,
                font=self.get_font_config(font_size, font_weight),
                bg=theme['bg'],
                fg=theme['accent'],
                relief='flat',
                pady=5
            )

            # Add hover effect
            def on_enter(event):
                label.configure(fg=theme['accent2'])

            def on_leave(event):
                label.configure(fg=theme['accent'])

            label.bind('<Enter>', on_enter)
            label.bind('<Leave>', on_leave)

            return label

        except Exception as e:
            self.logger.error(f"Error creating gradient label: {e}")
            # Fallback to regular label
            return tk.Label(parent, text=text, font=self.get_font_config(font_size, font_weight))

    def create_neon_button(self, parent, text: str, command=None, width: int = 20) -> tk.Button:
        """
        Create a neon-styled button with cyberpunk effects

        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            width: Button width

        Returns:
            Styled button widget
        """
        try:
            theme = self.THEMES[self.current_theme]

            # Create button with neon styling
            button = tk.Button(
                parent,
                text=text,
                command=command,
                font=self.get_font_config(11, 'bold'),
                bg=theme['button_bg'],
                fg=theme['button_fg'],
                activebackground=theme['button_active'],
                activeforeground=theme['bg'],
                relief='flat',
                bd=2,
                width=width,
                pady=8,
                cursor='hand2'
            )

            # Add neon glow effect
            def on_enter(event):
                button.configure(
                    bg=theme['button_hover'],
                    fg=theme['neon_glow'],
                    relief='solid',
                    bd=2
                )

            def on_leave(event):
                button.configure(
                    bg=theme['button_bg'],
                    fg=theme['button_fg'],
                    relief='flat',
                    bd=2
                )

            def on_click(event):
                button.configure(
                    bg=theme['neon_glow'],
                    fg=theme['bg']
                )
                button.after(100, lambda: button.configure(
                    bg=theme['button_hover'],
                    fg=theme['neon_glow']
                ))

            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)
            button.bind('<Button-1>', on_click)

            return button

        except Exception as e:
            self.logger.error(f"Error creating neon button: {e}")
            # Fallback to regular button
            return tk.Button(parent, text=text, command=command, width=width)

    def create_cyber_frame(self, parent, padding: int = 20) -> tk.Frame:
        """
        Create a cyberpunk-styled frame

        Args:
            parent: Parent widget
            padding: Frame padding

        Returns:
            Styled frame widget
        """
        try:
            theme = self.THEMES[self.current_theme]

            frame = tk.Frame(
                parent,
                bg=theme['secondary_bg'],
                relief='solid',
                bd=1,
                highlightbackground=theme['accent'],
                highlightcolor=theme['accent2'],
                highlightthickness=1
            )

            return frame

        except Exception as e:
            self.logger.error(f"Error creating cyber frame: {e}")
            # Fallback to regular frame
            return tk.Frame(parent, bg=self.THEMES[self.current_theme]['bg'])

    def apply_neon_entry_style(self, entry: tk.Entry):
        """
        Apply neon styling to entry widget

        Args:
            entry: Entry widget to style
        """
        try:
            theme = self.THEMES[self.current_theme]

            entry.configure(
                bg=theme['input_bg'],
                fg=theme['input_fg'],
                insertbackground=theme['accent'],
                selectbackground=theme['accent'],
                selectforeground=theme['bg'],
                relief='solid',
                bd=2,
                highlightbackground=theme['accent3'],
                highlightcolor=theme['accent'],
                highlightthickness=1,
                font=self.get_font_config(10)
            )

            # Add focus effects
            def on_focus_in(event):
                entry.configure(
                    highlightbackground=theme['neon_glow'],
                    highlightcolor=theme['neon_glow']
                )

            def on_focus_out(event):
                entry.configure(
                    highlightbackground=theme['accent3'],
                    highlightcolor=theme['accent']
                )

            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)

        except Exception as e:
            self.logger.error(f"Error applying neon entry style: {e}")

    def create_glitch_text(self, parent, text: str, font_size: int = 14) -> tk.Label:
        """
        Create glitch-effect text label

        Args:
            parent: Parent widget
            text: Text to display
            font_size: Font size

        Returns:
            Styled label with glitch effect
        """
        try:
            theme = self.THEMES[self.current_theme]

            label = tk.Label(
                parent,
                text=text,
                font=self.get_font_config(font_size, 'bold'),
                bg=theme['bg'],
                fg=theme['accent'],
                relief='flat'
            )

            # Create glitch animation
            colors = [theme['accent'], theme['accent2'], theme['accent3']]
            current_color = 0

            def glitch_effect():
                nonlocal current_color
                label.configure(fg=colors[current_color])
                current_color = (current_color + 1) % len(colors)
                label.after(2000, glitch_effect)  # Change every 2 seconds

            # Start glitch effect
            glitch_effect()

            return label

        except Exception as e:
            self.logger.error(f"Error creating glitch text: {e}")
            return tk.Label(parent, text=text, font=self.get_font_config(font_size, 'bold'))
