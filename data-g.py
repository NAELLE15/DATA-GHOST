# DATA-GHOST - Outil professionnel de stéganographie
# Fonctionnalités : Chiffrement AES-256 | Multi-LSB (1-4 bits) 

# Importation des bibliothèques nécessaires
import customtkinter as ctk  # Pour l'interface graphique moderne
from tkinter import filedialog, messagebox  # Pour les dialogues de fichiers et les boîtes de message
from PIL import Image, ImageTk  # Pour la manipulation d'images
from Crypto.Cipher import AES  # Pour le chiffrement AES
from Crypto.Util.Padding import pad, unpad  # Pour le padding des données
import threading  # Pour exécuter des tâches en arrière-plan
import os  # Pour les opérations système
from dataclasses import dataclass  # Pour créer des classes de données
from typing import Optional  # Pour le typage
import binascii  # Pour les conversions binaires

# Configuration de l'interface
ctk.set_appearance_mode("system")  # Thème système par défaut
ctk.set_default_color_theme("dark-blue")  # Thème couleur bleu foncé

# Constantes
BLOCK_SIZE = AES.block_size  # Taille de bloc pour AES (16 octets)
MAX_LSB = 4  # Nombre maximum de bits LSB supportés
SUPPORTED_FORMATS = [("Tous fichiers", "*.*")]  # Formats de fichiers supportés

# Définition des thèmes disponibles
THEMES = {
    "Classique": {"bg": "#2b2b2b", "text": "#ffffff", "primary": "#3b8eed"},
    "Professionnel": {"bg": "#1e1e1e", "text": "#f0f0f0", "primary": "#2a6fc9"},
    "Clair": {"bg": "#f5f5f5", "text": "#333333", "primary": "#1e88e5"}
}

# Classe pour stocker les données de l'image
@dataclass
class ImageData:
    path: str  # Chemin de l'image
    width: int  # Largeur de l'image
    height: int  # Hauteur de l'image
    mode: str  # Mode de l'image (RGB, RGBA, etc.)
    capacity: int = 0  # Capacité de stockage en octets

# Classe pour stocker les paramètres de l'application
@dataclass
class GhostSettings:
    lsb: int = 1  # Nombre de bits LSB à utiliser (1-4)
    theme: str = "Classique"  # Thème actuel
    encryption: bool = True  # Si le chiffrement est activé

# Classe principale de l'application
class DataGhostApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Configuration de la fenêtre principale
        self.title("DATA-GHOST - Outil de stéganographie")
        self.geometry("1000x750")
        self.minsize(900, 650)
        
        # Initialisation des variables
        self.settings = GhostSettings()
        self.image_data = None
        self.preview_image = None
        self.last_decoded = ""
        
        # Configuration de l'interface
        self._setup_main_window()
        self._apply_theme()
        self.show_home_screen()
        
    def _setup_main_window(self):
        """Configure la structure de base de la fenêtre principale."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Cadre principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Barre de statut
        self.status_bar = ctk.CTkLabel(
            self, 
            text="Prêt | Mode: Ghost | LSB: 1 | Thème: Classique",
            anchor="w"
        )
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=20)
        
    def _apply_theme(self):
        """Applique le thème sélectionné à l'interface."""
        theme = THEMES[self.settings.theme]
        ctk.set_appearance_mode("dark" if self.settings.theme != "Clair" else "light")
        self.main_frame.configure(fg_color=theme["bg"])
        self.status_bar.configure(text_color=theme["primary"], fg_color=theme["bg"])
        self._update_status()
    
    def _update_status(self):
        """Met à jour le texte de la barre de statut."""
        status_text = (
            f"Prêt | Mode: {'Ghost' if self.settings.encryption else 'Stealth'} | "
            f"LSB: {self.settings.lsb} | Thème: {self.settings.theme}"
        )
        self.status_bar.configure(text=status_text)
    
    def clear_frame(self):
        """Efface tous les widgets du cadre principal."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def show_home_screen(self):
        """Affiche l'écran d'accueil."""
        self.clear_frame()
        
        # En-tête
        header = ctk.CTkFrame(self.main_frame)
        header.pack(pady=(30, 40))
        
        ctk.CTkLabel(
            header,
            text="DATA-GHOST",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=THEMES[self.settings.theme]["primary"]
        ).pack()
        
        ctk.CTkLabel(
            header,
            text="Solution professionnelle de stéganographie",
            font=ctk.CTkFont(size=14),
            text_color=THEMES[self.settings.theme]["text"]
        ).pack()
        
        # Boutons principaux
        btn_frame = ctk.CTkFrame(self.main_frame)
        btn_frame.pack(pady=20)
        
        # Bouton Mode Ghost
        ctk.CTkButton(
            btn_frame,
            text="🕵️ MODE GHOST",
            width=220,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=THEMES[self.settings.theme]["primary"],
            hover_color="#2a6fc9",
            command=self.show_ghost_mode
        ).grid(row=0, column=0, padx=20, pady=10)
        
        # Bouton Mode Stealth
        ctk.CTkButton(
            btn_frame,
            text="👻 MODE STEALTH",
            width=220,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#7e57c2",
            hover_color="#5e35b1",
            command=self.show_stealth_mode
        ).grid(row=0, column=1, padx=20, pady=10)
        
        # Paramètres
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(pady=30)
        
        # Sélecteur de thème
        ctk.CTkLabel(settings_frame, text="Thème:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5)
        theme_menu = ctk.CTkOptionMenu(settings_frame, values=list(THEMES.keys()), command=self.change_theme)
        theme_menu.set(self.settings.theme)
        theme_menu.grid(row=0, column=1, padx=5)
        
        # Sélecteur de bits LSB
        ctk.CTkLabel(settings_frame, text="Bits LSB:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5)
        lsb_menu = ctk.CTkOptionMenu(settings_frame, values=[str(i) for i in range(1, MAX_LSB+1)], command=self.change_lsb)
        lsb_menu.set(str(self.settings.lsb))
        lsb_menu.grid(row=0, column=3, padx=5)
        
        # Pied de page
        ctk.CTkLabel(
            self.main_frame,
            text="© 2025 DATA-GHOST | Version Professionnelle",
            text_color="gray50"
        ).pack(side="bottom", pady=20)
    
    def show_ghost_mode(self):
        """Affiche l'interface du mode Ghost (dissimulation de données)."""
        self.settings.encryption = True
        self.clear_frame()
        self._update_status()
        
        # Configuration de l'interface
        header = ctk.CTkFrame(self.main_frame)
        header.pack(fill="x", pady=(10, 20))
        
        # Bouton retour et titre
        ctk.CTkButton(header, text="← Accueil", width=100, command=self.show_home_screen).pack(side="left")
        ctk.CTkLabel(header, text="🕵️ MODE GHOST", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=20)
        
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Colonne image
        left_col = ctk.CTkFrame(content_frame)
        left_col.pack(side="left", fill="y", padx=10, pady=10)
        
        # Widgets pour l'image porteuse
        ctk.CTkLabel(left_col, text="Image porteuse", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.img_btn = ctk.CTkButton(left_col, text="📁 Charger image", command=self.load_image)
        self.img_btn.pack(pady=5)
        
        self.preview_label = ctk.CTkLabel(left_col, text="Aperçu:")
        self.preview_label.pack(pady=5)
        
        self.canvas = ctk.CTkCanvas(left_col, width=300, height=200, bg="#333333")
        self.canvas.pack()
        self.img_info = ctk.CTkLabel(left_col, text="Aucune image chargée")
        self.img_info.pack(pady=10)
        
        # Colonne configuration
        right_col = ctk.CTkFrame(content_frame)
        right_col.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Section message
        msg_frame = ctk.CTkFrame(right_col)
        msg_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(msg_frame, text="Message à dissimuler", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.msg_entry = ctk.CTkTextbox(msg_frame, height=150, wrap="word", font=ctk.CTkFont(size=12))
        self.msg_entry.pack(fill="x", pady=5)
        
        # Section sécurité
        security_frame = ctk.CTkFrame(right_col)
        security_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(security_frame, text="Sécurité", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        # Champ pour la clé secrète
        key_frame = ctk.CTkFrame(security_frame)
        key_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(key_frame, text="Clé secrète:").pack(side="left")
        self.key_entry = ctk.CTkEntry(key_frame, placeholder_text="Entrez votre clé secrète (16, 24 ou 32 caractères)", show="*")
        self.key_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.show_key_btn = ctk.CTkButton(key_frame, text="👁", width=30, command=self.toggle_key_visibility)
        self.show_key_btn.pack(side="left")
        
        # Bouton principal
        action_frame = ctk.CTkFrame(right_col)
        action_frame.pack(fill="x", pady=20)
        self.ghost_btn = ctk.CTkButton(
            action_frame,
            text="👻 GHOSTIFIER",
            fg_color=THEMES[self.settings.theme]["primary"],
            hover_color="#2a6fc9",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.start_ghost_process
        )
        self.ghost_btn.pack(fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(right_col)
    
    def show_stealth_mode(self):
        """Affiche l'interface du mode Stealth (extraction de données)."""
        self.settings.encryption = False
        self.clear_frame()
        self._update_status()
        
        # Configuration de l'interface
        header = ctk.CTkFrame(self.main_frame)
        header.pack(fill="x", pady=(10, 20))
        
        # Bouton retour et titre
        ctk.CTkButton(header, text="← Accueil", width=100, command=self.show_home_screen).pack(side="left")
        ctk.CTkLabel(header, text="👻 MODE STEALTH", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=20)
        
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Colonne image
        left_col = ctk.CTkFrame(content_frame)
        left_col.pack(side="left", fill="y", padx=10, pady=10)
        
        # Widgets pour l'image à analyser
        ctk.CTkLabel(left_col, text="Image à analyser", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.stealth_img_btn = ctk.CTkButton(left_col, text="📁 Charger image", command=self.load_stealth_image)
        self.stealth_img_btn.pack(pady=5)
        
        self.stealth_preview_label = ctk.CTkLabel(left_col, text="Aperçu:")
        self.stealth_preview_label.pack(pady=5)
        
        self.stealth_canvas = ctk.CTkCanvas(left_col, width=300, height=200, bg="#333333")
        self.stealth_canvas.pack()
        self.stealth_img_info = ctk.CTkLabel(left_col, text="Aucune image chargée")
        self.stealth_img_info.pack(pady=10)
        
        # Colonne configuration
        right_col = ctk.CTkFrame(content_frame)
        right_col.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Options d'analyse
        options_frame = ctk.CTkFrame(right_col)
        options_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(options_frame, text="Paramètres d'analyse", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        # Sélecteur de bits LSB
        lsb_frame = ctk.CTkFrame(options_frame)
        lsb_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(lsb_frame, text="Bits LSB:").pack(side="left")
        self.stealth_lsb_slider = ctk.CTkSlider(lsb_frame, from_=1, to=MAX_LSB, number_of_steps=MAX_LSB-1)
        self.stealth_lsb_slider.set(self.settings.lsb)
        self.stealth_lsb_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.stealth_lsb_label = ctk.CTkLabel(lsb_frame, text=str(self.settings.lsb))
        self.stealth_lsb_label.pack(side="left")
        
        # Champ pour la clé (optionnel)
        key_frame = ctk.CTkFrame(options_frame)
        key_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(key_frame, text="Clé (optionnel):").pack(side="left")
        self.stealth_key_entry = ctk.CTkEntry(key_frame, placeholder_text="Clé si chiffrement utilisé (16, 24 ou 32 caractères)", show="*")
        self.stealth_key_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Bouton d'analyse
        action_frame = ctk.CTkFrame(right_col)
        action_frame.pack(fill="x", pady=20)
        self.analyze_btn = ctk.CTkButton(
            action_frame,
            text="🔍 ANALYSER",
            fg_color="#7e57c2",
            hover_color="#5e35b1",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self.start_stealth_analysis
        )
        self.analyze_btn.pack(fill="x")
        
        # Zone de résultats
        self.result_frame = ctk.CTkFrame(right_col)
        ctk.CTkLabel(self.result_frame, text="Résultats", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=5)
        self.result_text = ctk.CTkTextbox(self.result_frame, height=150, wrap="word", font=ctk.CTkFont(size=12))
        self.result_text.pack(fill="both", expand=True)
        
        # Boutons résultats
        result_btn_frame = ctk.CTkFrame(self.result_frame)
        result_btn_frame.pack(fill="x", pady=5)
        ctk.CTkButton(result_btn_frame, text="Copier", width=80, command=self.copy_results).pack(side="left", padx=5)
        ctk.CTkButton(
            result_btn_frame,
            text="Ghostifier ce message",
            fg_color=THEMES[self.settings.theme]["primary"],
            command=self.ghostify_result
        ).pack(side="left", padx=5)
        
        self.stealth_progress = ctk.CTkProgressBar(right_col)
    
    # Fonctions utilitaires
    def toggle_key_visibility(self):
        """Bascule la visibilité de la clé secrète."""
        current = self.key_entry.cget("show")
        self.key_entry.configure(show="" if current == "*" else "*")
        self.show_key_btn.configure(text="🔒" if current == "*" else "👁")
    
    def change_theme(self, choice):
        """Change le thème de l'interface."""
        self.settings.theme = choice
        self._apply_theme()
    
    def change_lsb(self, choice):
        """Change le nombre de bits LSB à utiliser."""
        self.settings.lsb = int(choice)
        self._update_status()
    
    def load_image(self):
        """Charge une image pour le mode Ghost."""
        path = filedialog.askopenfilename(filetypes=SUPPORTED_FORMATS)
        if not path: return
        
        try:
            with Image.open(path) as img:
                # Crée un objet ImageData avec les propriétés de l'image
                self.image_data = ImageData(
                    path=path,
                    width=img.width,
                    height=img.height,
                    mode=img.mode,
                    capacity=(img.width * img.height * 3 * self.settings.lsb) // 8  # Calcule la capacité de stockage
                )
                
                # Met à jour les informations de l'image
                self.img_info.configure(text=f"{os.path.basename(path)}\n{img.width}x{img.height} | {img.mode}\nCapacité: {self.image_data.capacity} octets")
                
                # Crée un aperçu de l'image
                img.thumbnail((300, 200))
                self.preview_image = ImageTk.PhotoImage(img)
                self.canvas.create_image(150, 100, image=self.preview_image, anchor="center")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger l'image:\n{str(e)}")
    
    def start_ghost_process(self):
        """Lance le processus de dissimulation de données."""
        if not self.image_data:
            messagebox.showerror("Erreur", "Veuillez charger une image")
            return
        
        message = self.msg_entry.get("1.0", "end-1c").strip()
        if not message:
            messagebox.showerror("Erreur", "Veuillez entrer un message")
            return
        
        key = self.key_entry.get().strip()
        if not key and self.settings.encryption:
            messagebox.showerror("Erreur", "Une clé est requise en mode Ghost")
            return
        
        if self.settings.encryption and len(key) not in [16, 24, 32]:
            messagebox.showerror("Erreur", "La clé doit faire 16, 24 ou 32 caractères")
            return
        
        # Demande où sauvegarder l'image
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Tous fichiers", "*.*")],
            title="Enregistrer l'image"
        )
        if not save_path: return
        
        # Configure la barre de progression
        self.progress_bar.pack(fill="x", pady=10)
        self.progress_bar.set(0)
        self.ghost_btn.configure(state="disabled")
        
        # Lance le processus en arrière-plan
        threading.Thread(
            target=self.ghost_worker,
            args=(message, key, save_path),
            daemon=True
        ).start()
    
    def ghost_worker(self, message: str, key: str, save_path: str):
        """Traitement principal pour dissimuler les données dans l'image."""
        try:
            data = message.encode('utf-8')
            
            # Chiffrement si activé
            if self.settings.encryption:
                data = encrypt_data(key, data)
            
            # Convertit les données en binaire
            binary_data = ''.join(f"{byte:08b}" for byte in data)
            binary_data += "00000000"  # Marqueur de fin
            
            # Ouvre l'image et traite les pixels
            with Image.open(self.image_data.path) as img:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                pixels = img.load()
                total_bits = len(binary_data)
                bit_index = 0
                
                # Parcourt tous les pixels
                for y in range(img.height):
                    for x in range(img.width):
                        if bit_index >= total_bits: break
                        
                        r, g, b = pixels[x, y][:3]
                        
                        # Modifie les bits LSB de chaque composante de couleur
                        for i, color in enumerate((r, g, b)):
                            if bit_index < total_bits:
                                mask = ~((1 << self.settings.lsb) - 1)
                                bits = binary_data[bit_index:bit_index+self.settings.lsb]
                                bits = bits.ljust(self.settings.lsb, '0')
                                new_val = (color & mask) | int(bits, 2)
                                
                                if i == 0: r = new_val
                                elif i == 1: g = new_val
                                else: b = new_val
                                
                                bit_index += self.settings.lsb
                        
                        pixels[x, y] = (r, g, b)
                    
                    # Met à jour la barre de progression
                    self.after(0, lambda: self.progress_bar.set(min(bit_index / total_bits, 1.0)))
                    if bit_index >= total_bits: break
                
                # Sauvegarde l'image modifiée
                img.save(save_path)
            
            self.after(0, lambda: messagebox.showinfo("Succès", f"Message caché dans:\n{save_path}"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erreur", f"Échec:\n{str(e)}"))
        finally:
            # Réactive le bouton et cache la barre de progression
            self.after(0, lambda: self.ghost_btn.configure(state="normal"))
            self.after(0, lambda: self.progress_bar.pack_forget())
    
    def load_stealth_image(self):
        """Charge une image pour le mode Stealth."""
        path = filedialog.askopenfilename(filetypes=SUPPORTED_FORMATS)
        if not path: return
        
        try:
            with Image.open(path) as img:
                self.stealth_image_path = path
                self.stealth_img_info.configure(text=f"{os.path.basename(path)}\n{img.width}x{img.height} | {img.mode}")
                
                # Crée un aperçu de l'image
                img.thumbnail((300, 200))
                self.stealth_preview_image = ImageTk.PhotoImage(img)
                self.stealth_canvas.create_image(150, 100, image=self.stealth_preview_image, anchor="center")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger l'image:\n{str(e)}")
    
    def start_stealth_analysis(self):
        """Lance l'analyse de l'image pour extraire les données cachées."""
        if not hasattr(self, 'stealth_image_path'):
            messagebox.showerror("Erreur", "Veuillez charger une image")
            return
        
        lsb = int(self.stealth_lsb_slider.get())
        key = self.stealth_key_entry.get().strip()
        
        if key and len(key) not in [16, 24, 32]:
            messagebox.showerror("Erreur", "La clé doit faire 16, 24 ou 32 caractères")
            return
        
        # Configure la barre de progression
        self.stealth_progress.pack(fill="x", pady=10)
        self.stealth_progress.set(0)
        self.analyze_btn.configure(state="disabled")
        self.result_frame.pack_forget()
        
        # Lance l'analyse en arrière-plan
        threading.Thread(
            target=self.stealth_worker,
            args=(lsb, key),
            daemon=True
        ).start()
    
    def stealth_worker(self, lsb: int, key: str):
        """Traitement principal pour extraire les données cachées."""
        try:
            with Image.open(self.stealth_image_path) as img:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                width, height = img.size
                pixels = img.load()
                binary_data = []
                total_pixels = width * height
                processed_pixels = 0
                
                # Parcourt tous les pixels pour extraire les bits LSB
                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y][:3]
                        
                        # Extrait les bits LSB de chaque composante de couleur
                        for color in (r, g, b):
                            bits = color & ((1 << lsb) - 1)
                            binary_data.append(f"{bits:0{lsb}b}")
                            
                        processed_pixels += 1
                        if processed_pixels % 100 == 0:
                            self.after(0, lambda: self.stealth_progress.set(processed_pixels / total_pixels))
                
                # Convertit les bits en octets
                binary_str = ''.join(binary_data)
                bytes_data = bytearray()
                
                for i in range(0, len(binary_str), 8):
                    byte_str = binary_str[i:i+8]
                    if len(byte_str) < 8: break
                    bytes_data.append(int(byte_str, 2))
                
                # Trouve le marqueur de fin (00)
                try:
                    end_index = bytes_data.index(0)
                    bytes_data = bytes_data[:end_index]
                except ValueError:
                    pass  # Pas de marqueur de fin trouvé
                
                result = ""
                
                # Tentative de déchiffrement si une clé est fournie
                if key and bytes_data:
                    try:
                        decrypted = decrypt_data(key, bytes_data)
                        result += "✅ Données déchiffrées avec succès\n\n"
                        try:
                            # Essaie de décoder en UTF-8
                            text = decrypted.decode('utf-8')
                            result += "=== MESSAGE EXTRAIT ===\n" + text
                            self.last_decoded = text
                        except UnicodeDecodeError:
                            # Si ce n'est pas du texte, affiche les données brutes
                            result += "⚠️ Données déchiffrées mais format non texte:\n\n" + str(decrypted)
                            self.last_decoded = ""
                    except Exception as e:
                        result += f"⚠️ Échec du déchiffrement: {str(e)}\n\n"
                        try:
                            # Essaie de décoder sans déchiffrement
                            text = bytes_data.decode('utf-8')
                            result += "=== MESSAGE EXTRAIT (non chiffré) ===\n" + text
                            self.last_decoded = text
                        except UnicodeDecodeError:
                            result += "=== DONNÉES BRUTES ===\n" + str(bytes_data)
                            self.last_decoded = ""
                else:
                    # Sans clé, essaie simplement de décoder
                    try:
                        text = bytes_data.decode('utf-8')
                        result += "=== MESSAGE EXTRAIT ===\n" + text
                        self.last_decoded = text
                    except UnicodeDecodeError:
                        result += "⚠️ Format binaire - Affichage brut:\n\n" + str(bytes_data)
                        self.last_decoded = ""
                
                self.after(0, lambda: self.show_stealth_results(result))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Erreur",
                f"Échec de l'analyse:\n{str(e)}\n\n"
                "Conseils:\n"
                "- Essayez différents bits LSB\n"
                "- Vérifiez la clé\n"
                "- L'image peut ne pas contenir de données"
            ))
        finally:
            # Réactive le bouton et cache la barre de progression
            self.after(0, lambda: self.analyze_btn.configure(state="normal"))
            self.after(0, lambda: self.stealth_progress.pack_forget())
    
    def show_stealth_results(self, text: str):
        """Affiche les résultats de l'analyse."""
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(text_color=THEMES[self.settings.theme]["text"])
        self.result_frame.pack(fill="both", expand=True, pady=10)
    
    def copy_results(self):
        """Copie les résultats dans le presse-papiers."""
        text = self.result_text.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Succès", "Texte copié dans le presse-papiers")
    
    def ghostify_result(self):
        """Réutilise le message extrait dans le mode Ghost."""
        if hasattr(self, 'last_decoded') and self.last_decoded:
            self.show_ghost_mode()
            self.msg_entry.delete("1.0", "end")
            self.msg_entry.insert("1.0", self.last_decoded)
        else:
            messagebox.showwarning("Attention", "Aucun message valide à réutiliser")

def encrypt_data(key: str, data: bytes) -> bytes:
    """Chiffre les données avec AES-256 en mode CBC."""
    # Assure que la clé est de la bonne taille (16, 24 ou 32 octets)
    key = key.encode('utf-8')
    key = key.ljust(32, b'\0')[:32]  # Tronque ou complète à 32 octets
    
    # Génère un vecteur d'initialisation et chiffre les données
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data, BLOCK_SIZE))
    return iv + encrypted  # Retourne IV + données chiffrées

def decrypt_data(key: str, data: bytes) -> bytes:
    """Déchiffre les données avec AES-256 en mode CBC."""
    if len(data) < 16:
        raise ValueError("Données chiffrées trop courtes")
    
    # Assure que la clé est de la bonne taille (16, 24 ou 32 octets)
    key = key.encode('utf-8')
    key = key.ljust(32, b'\0')[:32]  # Tronque ou complète à 32 octets
    
    # Extrait le vecteur d'initialisation et déchiffre
    iv = data[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    try:
        decrypted = unpad(cipher.decrypt(data[16:]), BLOCK_SIZE)
        return decrypted
    except ValueError as e:
        # Si le dépadding échoue, retourne les données brutes
        return cipher.decrypt(data[16:])
    except Exception as e:
        raise ValueError(f"Échec du déchiffrement: {str(e)}")

if __name__ == "__main__":
    app = DataGhostApp()
    app.mainloop()
