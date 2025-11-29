# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window 
from kivy.metrics import dp 
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, ListProperty
from datetime import datetime
import webbrowser
from urllib.parse import quote
import random
import os
import json
import plyer

# Define the number of message slots
NUM_MESSAGES = 5

# --- Default Data ---
DEFAULT_QUOTES = [
    "Every morning we are born again. What we do today is what matters most. — Buddha",
    "The secret of getting ahead is getting started. — Mark Twain",
    "Believe you can and you're halfway there. — Theodore Roosevelt",
    "Happiness is not something ready-made. It comes from your own actions. — Dalai Lama",
    "Success is not final, failure is not fatal: It is the courage to continue that counts. — Winston Churchill",
]

DEFAULT_MESSAGES = [
    {"name": "Good Morning", "time": "07:00 AM", "header": "G O O D ✨ MORNING", "body": "🌼 Happy {day}! ✨\n“{quote}”\n🌿✨", "quote": random.choice(DEFAULT_QUOTES) if DEFAULT_QUOTES else ""},
    {"name": "Good Night", "time": "10:00 PM", "header": "💤 Sweet Dreams", "body": "Time to rest your mind. See you tomorrow, {day}! 🌙", "quote": ""},
    {"name": "Emergency Alert", "time": "08:00 AM", "header": "⚠️ URGENT BROADCAST", "body": "Please check your messages immediately. This is a crucial alert.", "quote": ""},
    {"name": "Weekend Vibe", "time": "09:30 AM", "header": "🎉 WEEKEND VIBES", "body": "Enjoy your {day}! Make today awesome and relax fully. 🥳", "quote": ""},
    {"name": "Inspirational Quote", "time": "12:00 PM", "header": "✨ MIDDAY BOOST", "body": "Remember: The best way to predict the future is to create it. 💪", "quote": ""},
]


class MessageSlot(BoxLayout):
    """Container for a single scheduled message template."""
    index = ObjectProperty(0)
    name = StringProperty("")
    time_text = StringProperty("")
    header_text = StringProperty("")
    body_text = StringProperty("")
    current_quote = StringProperty("")
    app = ObjectProperty(None) # Reference to the main app instance

    def on_time_text(self, instance, value):
        # Placeholder for dynamic UI updates, if needed
        pass
    
    def cycle_quote(self):
        """Cycles to the next random quote from the global list."""
        quotes_list = self.app.config_data.get('quote_list', [])
        if not quotes_list:
            self.current_quote = "No quotes available. Add some in the Quote Manager!"
            return

        # Pick a new random quote (more useful than simple cycling for a large list)
        self.current_quote = random.choice(quotes_list)
    
    def get_full_message(self):
        """Generates the full message using the current input values."""
        header = self.header_text
        body = self.body_text
        day_name = datetime.now().strftime("%A") 

        # Replace placeholders
        formatted_body = body.replace("{day}", day_name).replace("{quote}", self.current_quote)
        
        full_message = f"{header}\n\n{formatted_body}"
        return full_message
    
    def preview_message(self):
        """Generates and logs the full message to the console."""
        print(f"\n--- Message Preview Slot {self.index + 1} ({self.name}) ---")
        print(self.get_full_message())
        print("------------------------------------------\n")

    def send_whatsapp(self):
        """Generates the final message and opens the WhatsApp share sheet."""
        msg = self.get_full_message()
        url = f"https://wa.me/?text={quote(msg)}"
        webbrowser.open(url)

    def open_time_picker(self):
        """Placeholder for native time picker (Plyer implementation)."""
        # For a true native picker, you'd use a callback, but for now, 
        # we focus the TextInput and suggest the format.
        print("💡 Native Time Picker placeholder activated. Use format HH:MM AM/PM.")
        try:
             # Use plyer's dialog for a more native feel, though it returns time via callback
             def time_callback(time):
                 if time:
                     # Update the time_text property from the returned time object
                     self.time_text = time.strftime("%I:%M %p")
             
             # Try to parse current time to set initial value for the picker
             try:
                 initial_time = datetime.strptime(self.time_text.strip(), "%I:%M %p").time()
             except:
                 initial_time = datetime.now().time()
                 
             plyer.time.open_time_picker(callback=time_callback, initial_time=initial_time)
        except Exception as e:
            print(f"Plyer time picker failed (this is common in Colab): {e}")


class QuoteManagerWidget(BoxLayout):
    """Handles adding new quotes to the list."""
    new_quotes_text = StringProperty("")
    app = ObjectProperty(None)
    quote_count_text = StringProperty("Total Quotes: 0")

    def save_new_quotes(self):
        """Processes new input and saves the updated quote list to the main config."""
        new_quotes_text = self.new_quotes_text.strip()
        
        if not new_quotes_text:
            print("No new quotes entered.")
            return

        # Split input by newline, clean up empty lines, and remove duplicates
        new_quotes = [q.strip() for q in new_quotes_text.split('\n') if q.strip()]
        
        # Combine with existing quotes and remove duplicates using a set
        current_quotes = set(self.app.config_data.get('quote_list', []))
        
        # Add all new quotes
        current_quotes.update(new_quotes)
        
        # Convert back to a list and update app config
        self.app.config_data['quote_list'] = list(current_quotes)
        
        # Clear input field and update count label
        self.new_quotes_text = ""
        self.quote_count_text = f"Total Quotes: {len(self.app.config_data['quote_list'])} (SAVED PENDING)"
        print(f"✅ {len(new_quotes)} quotes added! Press SAVE ALL SETTINGS to confirm.")


class MGBroadcastApp(App):
    # Properties for global switches
    vibrate_active = BooleanProperty(True)
    sound_active = BooleanProperty(True)
    
    # List of MessageSlot objects
    message_slots = ListProperty()
    
    # Global save button feedback
    save_button_text = StringProperty("SAVE ALL SETTINGS & SCHEDULE")
    save_button_color = ListProperty([0.1, 0.4, 0.7, 1])

    # --- CRITICAL FIX: Helper method to safely get the config file path ---
    def _get_config_path(self):
        """Helper to get the configuration file path safely."""
        return os.path.join(self.user_data_dir, "mgbroadcast_config.json")
    # ---------------------------------------------------------------------

    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1) # Dark background
        self.config_data = self.load_config() 
        
        # Set global switch states from config
        self.vibrate_active = self.config_data['global']['vibrate']
        self.sound_active = self.config_data['global']['sound']

        # Kivy loads the UI from mgbroadcast.kv
        root = super().build()

        # Initialize MessageSlot properties after the KV has loaded the widgets
        self.initialize_slots()
        
        return root

    def initialize_slots(self):
        # Access the list of MessageSlot widgets defined in KV
        self.message_slots = self.root.ids.slots_container.children[::-1] 

        # Transfer data from config to widget properties
        for i, slot_widget in enumerate(self.message_slots):
            data = self.config_data['messages'][i]
            slot_widget.index = i
            slot_widget.app = self
            slot_widget.name = data['name']
            slot_widget.time_text = data['time']
            slot_widget.header_text = data['header']
            slot_widget.body_text = data['body']
            slot_widget.current_quote = data.get('quote', random.choice(self.config_data.get('quote_list', [""])))
            
        # Update quote manager count
        self.root.ids.quote_manager.quote_count_text = f"Total Quotes: {len(self.config_data.get('quote_list', []))}"


    def load_config(self):
        """Loads configuration from JSON file or returns defaults."""
        default_config = {
            "global": {"sound": True, "vibrate": True},
            "quote_list": DEFAULT_QUOTES, 
            "messages": DEFAULT_MESSAGES
        }
        try:
            # CRITICAL FIX: Use the safe method to get the path
            with open(self._get_config_path(), "r") as f:
                cfg = json.load(f)
                # Ensure the loaded config has all required fields
                if 'messages' not in cfg or len(cfg['messages']) != NUM_MESSAGES or 'quote_list' not in cfg:
                    return default_config
                return cfg
        except:
            return default_config

    def save_all_settings(self):
        """Collects data from all slots and global switches, saves it, and logs the service times."""
        
        # 1. Collect Message Slot Data
        new_messages = []
        is_valid = True
        for slot in self.message_slots:
            display_time = slot.time_text.strip()
            
            # Basic Time Validation
            try:
                dt = datetime.strptime(display_time, "%I:%M %p")
                service_time = dt.strftime("%H:%M") # 24-hour time for service
            except ValueError:
                # Slot has invalid time format
                slot.name = f"🚨 ERROR: Invalid Time! ({slot.index+1})"
                is_valid = False
                break 

            # Collect slot data
            new_messages.append({
                "name": self.config_data['messages'][slot.index]['name'], 
                "time": display_time,
                "service_time": service_time,
                "header": slot.header_text,
                "body": slot.body_text,
                "quote": slot.current_quote 
            })
        
        if not is_valid:
            self.save_button_text = "🚨 SAVE FAILED: FIX TIME FORMATS! 🚨"
            self.save_button_color = [0.9, 0.2, 0.2, 1]
            return

        # 2. Assemble final config data
        self.config_data = {
            "global": {
                "sound": self.sound_active,
                "vibrate": self.vibrate_active
            },
            "quote_list": self.config_data['quote_list'], 
            "messages": new_messages
        }
        
        # 3. Save to the JSON file
        try:
            # CRITICAL FIX: Use the safe method to get the path
            with open(self._get_config_path(), "w") as f:
                json.dump(self.config_data, f, indent=4)
            
            # Success Feedback
            self.save_button_text = "✅ SETTINGS SAVED & SCHEDULE UPDATED! ✅"
            self.save_button_color = [0.1, 0.7, 0.1, 1]

            print("--- ✅ CONFIGURATION SAVED ---")
            for msg in new_messages:
                print(f"Slot '{msg['name']}' scheduled for {msg['service_time']}")
            print("-----------------------------\n")

        except Exception as e:
            self.save_button_text = "🚨 CRITICAL ERROR SAVING CONFIG 🚨"
            self.save_button_color = [1, 0, 0, 1]
            print(f"❌ Error saving config: {e}")

if __name__ == "__main__":
    MGBroadcastApp().run()
