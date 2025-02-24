import tkinter as tk
from tkinter import filedialog, ttk
import ffmpeg
import pyaudio
import wave
import threading
import riva.client
import riva.client.audio_io
from trans import RivaArguments, trans

class AudioConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Riva Project")
        self.root.geometry("2400x1800")
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main frames
        control_frame = tk.Frame(root)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.content_frame = tk.Frame(root)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        status_frame = tk.Frame(root)
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Control buttons with tooltips
        self.select_button = ttk.Button(control_frame, text="Select Video", command=self.select_video)
        self.select_button.pack(side="left", padx=5)
        self.create_tooltip(self.select_button, "Select a video file to convert to audio (Ctrl+O)")

        self.record_button = ttk.Button(control_frame, text="Start Recording", command=self.toggle_recording)
        self.record_button.pack(side="left", padx=5)
        self.create_tooltip(self.record_button, "Start/Stop audio recording (Ctrl+R)")

        self.settings_button = ttk.Button(control_frame, text="Settings", command=self.open_settings)
        self.settings_button.pack(side="left", padx=5)
        self.create_tooltip(self.settings_button, "Configure Riva settings (Ctrl+,)")

        # Content area (History) with scrollbar
        history_frame = ttk.Frame(self.content_frame)
        history_frame.pack(fill="both", expand=True)
        
        self.history_tree = ttk.Treeview(history_frame, columns=("File", "Type", "Status", "Time"), show="headings")
        self.history_tree.heading("File", text="File")
        self.history_tree.heading("Type", text="Type")
        self.history_tree.heading("Status", text="Status")
        self.history_tree.heading("Time", text="Time")
        
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enhanced status bar
        status_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ttk.Label(status_frame, text="Ready", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")
        
        self.detail_label = ttk.Label(status_frame, text="", anchor="e")
        self.detail_label.grid(row=0, column=1, padx=(10, 0))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self.progress_bar.grid_remove()
        
        self.is_recording = False
        self.riva_args = RivaArguments()
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()

    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Video...", command=self.select_video, accelerator="Ctrl+O")
        file_menu.add_command(label="Start/Stop Recording", command=self.toggle_recording, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.open_settings, accelerator="Ctrl+,")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)

    def bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda e: self.select_video())
        self.root.bind("<Control-r>", lambda e: self.toggle_recording())
        self.root.bind("<Control-comma>", lambda e: self.open_settings())

    def show_about(self):
        about_text = """Riva Project

A GUI application for audio conversion and recording using NVIDIA Riva ASR.

Features:
• Video to audio conversion
• Real-time audio recording
• Speech recognition
• Multiple language support
• Advanced ASR settings"""
        
        self.show_message(self.root, "About", about_text)

    def show_shortcuts(self):
        shortcuts_text = """Keyboard Shortcuts

Ctrl+O: Open video file
Ctrl+R: Start/Stop recording
Ctrl+,: Open settings
Alt+F4: Exit application"""
        
        self.show_message(self.root, "Keyboard Shortcuts", shortcuts_text)

    def update_status(self, message, detail="", is_error=False):
        self.status_label.config(text=message, foreground="red" if is_error else "black")
        self.detail_label.config(text=detail)
        self.root.update()

    def add_to_history(self, filename, type_, status):
        from datetime import datetime
        self.history_tree.insert("", 0, values=(filename, type_, status, datetime.now().strftime("%H:%M:%S")))

    def select_video(self):
        video_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4;*.avi;*.mov;*.mkv"),
                ("All Files", "*.*")
            ]
        )
        if video_path:
            filename = video_path.split('/')[-1]
            self.update_status("Converting video...", f"File: {filename}")
            self.progress_bar.grid()
            self.progress_bar.start()
            self.root.update()
            
            try:
                output_audio = video_path.rsplit('.', 1)[0] + ".mp3"
                self.convert_to_audio(video_path, output_audio)
                output_filename = output_audio.split('/')[-1]
                self.add_to_history(filename, "Video", "Converted")
                self.update_status("Conversion complete", f"Output: {output_filename}")
            except Exception as e:
                self.add_to_history(filename, "Video", "Failed")
                self.update_status("Conversion failed", str(e), is_error=True)
            finally:
                self.progress_bar.stop()
                self.progress_bar.grid_remove()

    def convert_to_audio(self, video_path, audio_path):
        try:    
            # Show ffmpeg progress in detail label
            self.update_status("Converting video...", "Initializing ffmpeg...")
            ffmpeg.input(video_path).output(audio_path, format='mp3').run(
                capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            raise Exception(f"FFmpeg error: {e.stderr.decode()}")
        except Exception as e:
            raise Exception(f"Conversion error: {str(e)}")

    def toggle_recording(self):
        if not self.is_recording:
            try:
                self.is_recording = True
                self.record_button.configure(text="Stop Recording")
                style = ttk.Style()
                style.configure("Recording.TButton", background="red")
                self.record_button.configure(style="Recording.TButton")
                
                self.update_status("Recording in progress", 
                                 f"Sample rate: {self.riva_args.sample_rate_hz}Hz")
                self.progress_bar.grid()
                self.progress_bar.start()
                self.add_to_history("Microphone", "Recording", "Started")
                threading.Thread(target=self.record_audio).start()
            except Exception as e:
                self.update_status("Recording failed", str(e), is_error=True)
                self.is_recording = False
                self.record_button.configure(text="Start Recording", style="")
                self.progress_bar.stop()
                self.progress_bar.grid_remove()
        else:
            self.is_recording = False
            self.record_button.configure(text="Start Recording", style="")
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.update_status("Recording stopped", "Ready")
            self.add_to_history("Microphone", "Recording", "Stopped")

    def record_audio(self):
        with riva.client.audio_io.MicrophoneStream(
            self.riva_args.sample_rate_hz,
            self.riva_args.file_streaming_chunk,
            device=self.riva_args.input_device,
        ) as audio_chunk_iterator:
            trans(self.riva_args, audio_chunk_iterator)

    def create_labeled_entry(self, parent, row, label_text, tooltip_text, initial_value, validator=None):
        # Create container frame
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Configure grid weights
        frame.grid_columnconfigure(1, weight=1)
        
        # Create and pack label
        label = ttk.Label(frame, text=label_text)
        label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Create and pack entry
        entry = ttk.Entry(frame)
        entry.grid(row=0, column=1, sticky="ew")
        entry.insert(0, str(initial_value))
        
        # Add tooltip
        self.create_tooltip(label, tooltip_text)
        self.create_tooltip(entry, tooltip_text)
        
        # Add validation if provided
        if validator:
            entry.config(validate="key", validatecommand=(parent.register(validator), '%P'))
        
        return entry

    def create_labeled_checkbox(self, parent, row, label_text, tooltip_text, initial_value):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        var = tk.BooleanVar(value=initial_value)
        checkbox = ttk.Checkbutton(frame, text=label_text, variable=var)
        checkbox.grid(row=0, column=0, sticky="w")
        
        self.create_tooltip(checkbox, tooltip_text)
        
        return var

    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, justify='left',
                            relief='solid', borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            tooltip.bind('<Leave>', lambda e: hide_tooltip())

        widget.bind('<Enter>', show_tooltip)

    def validate_int(self, value):
        if value == "": return True
        try:
            int(value)
            return True
        except ValueError:
            return False

    def validate_float(self, value):
        if value == "": return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x800")

        # Add a title and description
        title_frame = ttk.Frame(settings_window)
        title_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = ttk.Label(title_frame, text="Riva Settings", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack()
        
        desc_label = ttk.Label(title_frame, 
                              text="Configure your Riva ASR settings below.\nHover over any setting for more information.",
                              justify="center")
        desc_label.pack(pady=5)

        # Create a notebook with custom style
        style = ttk.Style()
        style.configure("Settings.TNotebook", padding=10)
        style.configure("Settings.TNotebook.Tab", padding=[20, 5])
        
        notebook = ttk.Notebook(settings_window, style="Settings.TNotebook")
        notebook.pack(fill='both', expand=True, padx=10)

        # Server Settings Tab
        server_frame = ttk.Frame(notebook)
        notebook.add(server_frame, text="Server")
        
        # Add section title
        ttk.Label(server_frame, text="Server Configuration", 
                 font=("Helvetica", 12, "bold")).grid(row=0, column=0, 
                 columnspan=2, pady=10, sticky="w", padx=10)

        # Add widgets for server settings with tooltips
        self.server_url_entry = self.create_labeled_entry(
            server_frame, 1, "Server URL:",
            "The URL of your Riva server (e.g., localhost:50051)",
            self.riva_args.server)
        self.server_url_entry.insert(0, self.riva_args.server)
        self.server_url_entry.grid(row=0, column=1, padx=10, pady=10)

        self.ssl_cert_entry = self.create_labeled_entry(
            server_frame, 2, "SSL Certificate:",
            "Path to SSL certificate file for secure connections",
            self.riva_args.ssl_cert)
            
        self.use_ssl_var = self.create_labeled_checkbox(
            server_frame, 3, "Use SSL",
            "Enable SSL/TLS encryption for server communication",
            self.riva_args.use_ssl)
            
        self.metadata_entry = self.create_labeled_entry(
            server_frame, 4, "Metadata:",
            "Additional metadata to send with requests",
            self.riva_args.metadata)

        # General Settings Tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        ttk.Label(general_frame, text="Audio Configuration", 
                 font=("Helvetica", 12, "bold")).grid(row=0, column=0, 
                 columnspan=2, pady=10, sticky="w", padx=10)

        self.sample_rate_entry = self.create_labeled_entry(
            general_frame, 1, "Sample Rate (Hz):",
            "Audio sampling rate in Hertz (e.g., 16000)",
            self.riva_args.sample_rate_hz,
            self.validate_int)
            
        self.language_code_entry = self.create_labeled_entry(
            general_frame, 2, "Language Code:",
            "Primary language code (e.g., en-US)",
            self.riva_args.asr_language_code)
            
        self.target_language_code_entry = self.create_labeled_entry(
            general_frame, 3, "Target Language:",
            "Target language for translation (if needed)",
            self.riva_args.target_language_code)
            
        self.model_name_entry = self.create_labeled_entry(
            general_frame, 4, "Model Name:",
            "Name of the ASR model to use",
            self.riva_args.model_name)
            
        self.input_device_entry = self.create_labeled_entry(
            general_frame, 5, "Input Device:",
            "Audio input device ID (usually 0 for default)",
            self.riva_args.input_device,
            self.validate_int)
            
        self.file_streaming_chunk_entry = self.create_labeled_entry(
            general_frame, 6, "Streaming Chunk Size:",
            "Size of audio chunks for streaming",
            self.riva_args.file_streaming_chunk,
            self.validate_int)
            
        ttk.Label(general_frame, text="Transcription Options", 
                 font=("Helvetica", 12, "bold")).grid(row=7, column=0, 
                 columnspan=2, pady=(20,10), sticky="w", padx=10)
                 
        self.automatic_punctuation_var = self.create_labeled_checkbox(
            general_frame, 8, "Automatic Punctuation",
            "Add punctuation to transcribed text automatically",
            self.riva_args.automatic_punctuation)
            
        self.no_verbatim_transcripts_var = self.create_labeled_checkbox(
            general_frame, 9, "No Verbatim Transcripts",
            "Exclude filler words and hesitations",
            self.riva_args.no_verbatim_transcripts)

        

        # Advanced Settings Tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        
        ttk.Label(advanced_frame, text="Recognition Options", 
                 font=("Helvetica", 12, "bold")).grid(row=0, column=0, 
                 columnspan=2, pady=10, sticky="w", padx=10)

        self.max_alternatives_entry = self.create_labeled_entry(
            advanced_frame, 1, "Max Alternatives:",
            "Maximum number of alternative transcriptions (1-5)",
            self.riva_args.max_alternatives,
            self.validate_int)
            
        self.profanity_filter_var = self.create_labeled_checkbox(
            advanced_frame, 2, "Profanity Filter",
            "Filter out profanity from transcriptions",
            self.riva_args.profanity_filter)
            
        ttk.Label(advanced_frame, text="Language Model Boosting", 
                 font=("Helvetica", 12, "bold")).grid(row=3, column=0, 
                 columnspan=2, pady=(20,10), sticky="w", padx=10)
            
        self.boosted_lm_words_entry = self.create_labeled_entry(
            advanced_frame, 4, "Boosted Words:",
            "Words to boost in language model (comma-separated)",
            self.riva_args.boosted_lm_words)
            
        self.boosted_lm_score_entry = self.create_labeled_entry(
            advanced_frame, 5, "Boost Score:",
            "Score multiplier for boosted words (0.0-20.0)",
            self.riva_args.boosted_lm_score,
            self.validate_float)
            
        ttk.Label(advanced_frame, text="Speaker Diarization", 
                 font=("Helvetica", 12, "bold")).grid(row=6, column=0, 
                 columnspan=2, pady=(20,10), sticky="w", padx=10)
            
        self.speaker_diarization_var = self.create_labeled_checkbox(
            advanced_frame, 7, "Enable Speaker Diarization",
            "Identify and separate different speakers",
            self.riva_args.speaker_diarization)
            
        self.diarization_max_speakers_entry = self.create_labeled_entry(
            advanced_frame, 8, "Max Speakers:",
            "Maximum number of speakers to identify (2-10)",
            self.riva_args.diarization_max_speakers,
            self.validate_int)
            
        self.custom_configuration_entry = self.create_labeled_entry(
            advanced_frame, 9, "Custom Config:",
            "Advanced configuration options (JSON format)",
            self.riva_args.custom_configuration)

        # History Settings Tab
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="History")
        
        ttk.Label(history_frame, text="Voice Activity Detection", 
                 font=("Helvetica", 12, "bold")).grid(row=0, column=0, 
                 columnspan=2, pady=10, sticky="w", padx=10)

        self.start_history_entry = self.create_labeled_entry(
            history_frame, 1, "Start History:",
            "Number of audio frames to keep in history for VAD start",
            self.riva_args.start_history,
            self.validate_int)
            
        self.start_threshold_entry = self.create_labeled_entry(
            history_frame, 2, "Start Threshold:",
            "Threshold for voice activity detection start (0.0-1.0)",
            self.riva_args.start_threshold,
            self.validate_float)
            
        self.stop_history_entry = self.create_labeled_entry(
            history_frame, 3, "Stop History:",
            "Number of audio frames to keep in history for VAD stop",
            self.riva_args.stop_history,
            self.validate_int)
            
        self.stop_threshold_entry = self.create_labeled_entry(
            history_frame, 4, "Stop Threshold:",
            "Threshold for voice activity detection stop (0.0-1.0)",
            self.riva_args.stop_threshold,
            self.validate_float)
            
        ttk.Label(history_frame, text="End of Utterance Detection", 
                 font=("Helvetica", 12, "bold")).grid(row=5, column=0, 
                 columnspan=2, pady=(20,10), sticky="w", padx=10)
            
        self.stop_history_eou_entry = self.create_labeled_entry(
            history_frame, 6, "EOU History:",
            "Number of frames to analyze for end of utterance",
            self.riva_args.stop_history_eou,
            self.validate_int)
            
        self.stop_threshold_eou_entry = self.create_labeled_entry(
            history_frame, 7, "EOU Threshold:",
            "Threshold for end of utterance detection (0.0-1.0)",
            self.riva_args.stop_threshold_eou,
            self.validate_float)

        # Save/Cancel Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(pady=20, padx=10, fill="x")
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                command=settings_window.destroy)
        cancel_button.pack(side="right", padx=5)
        
        save_button = ttk.Button(button_frame, text="Save", 
                              command=lambda: self.save_settings(settings_window))
        save_button.pack(side="right", padx=5)

    def show_message(self, parent, title, message, is_error=False):
        messagebox = tk.Toplevel(parent)
        messagebox.title(title)
        messagebox.geometry("300x150")
        messagebox.transient(parent)
        messagebox.grab_set()
        
        # Center the message box
        messagebox.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()/2 - 150,
            parent.winfo_rooty() + parent.winfo_height()/2 - 75))
        
        ttk.Label(messagebox, text=message, wraplength=250, 
                 justify="center").pack(expand=True, padx=20, pady=20)
        
        ttk.Button(messagebox, text="OK", 
                  command=messagebox.destroy).pack(pady=10)
        
        if not is_error:
            messagebox.after(2000, messagebox.destroy)

    def save_settings(self, settings_window):
        try:
            # Server settings
            self.riva_args.set_server(self.server_url_entry.get())
            self.riva_args.set_ssl_cert(self.ssl_cert_entry.get())
            self.riva_args.set_use_ssl(self.use_ssl_var.get())
            self.riva_args.set_metadata(self.metadata_entry.get())
            
            # General settings
            self.riva_args.set_model_name(self.model_name_entry.get())
            self.riva_args.set_input_device(int(self.input_device_entry.get()))
            self.riva_args.set_file_streaming_chunk(int(self.file_streaming_chunk_entry.get()))
            self.riva_args.set_automatic_punctuation(self.automatic_punctuation_var.get())
            self.riva_args.set_no_verbatim_transcripts(self.no_verbatim_transcripts_var.get())
            self.riva_args.set_sample_rate_hz(int(self.sample_rate_entry.get()))
            self.riva_args.set_asr_language_code(self.language_code_entry.get())
            self.riva_args.set_target_language_code(self.target_language_code_entry.get())
            
            # Advanced settings
            self.riva_args.set_max_alternatives(int(self.max_alternatives_entry.get()))
            self.riva_args.set_profanity_filter(self.profanity_filter_var.get())
            self.riva_args.set_boosted_lm_words(self.boosted_lm_words_entry.get())
            self.riva_args.set_boosted_lm_score(float(self.boosted_lm_score_entry.get()))
            self.riva_args.set_speaker_diarization(self.speaker_diarization_var.get())
            self.riva_args.set_diarization_max_speakers(int(self.diarization_max_speakers_entry.get()))
            self.riva_args.set_custom_configuration(self.custom_configuration_entry.get())
            
            # History settings
            self.riva_args.set_start_history(int(self.start_history_entry.get()))
            self.riva_args.set_start_threshold(float(self.start_threshold_entry.get()))
            self.riva_args.set_stop_history(int(self.stop_history_entry.get()))
            self.riva_args.set_stop_threshold(float(self.stop_threshold_entry.get()))
            self.riva_args.set_stop_history_eou(int(self.stop_history_eou_entry.get()))
            self.riva_args.set_stop_threshold_eou(float(self.stop_threshold_eou_entry.get()))
            
            self.show_message(settings_window, "Success", 
                            "Settings saved successfully!")
            settings_window.after(1500, settings_window.destroy)
            
        except ValueError as e:
            self.show_message(settings_window, "Error", 
                            f"Error saving settings: {str(e)}", 
                            is_error=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioConverterApp(root)
    root.mainloop()
