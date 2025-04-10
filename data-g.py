import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import zlib
import threading
import os
import math
from dataclasses import dataclass
from typing import Optional, Tuple

# Configuration de l'apparence
ctk.set_appearance_mode("system")  # S'adapte au thème du système
ctk.set_default_color_theme("blue")  

# Constantes
BLOCK_SIZE = AES.block_size
MAX_LSB = 2  # Nombre maximum de bits LSB à utiliser
DEFAULT_IMAGE_FORMATS = [("PNG (Recommandé)", "*.png"), 
                        ("BMP (Non compressé)", "*.bmp"),
                        ("Tous les fichiers", "*.*")]

@dataclass
class ImageInfo:
    path: str
    width: int
    height: int
    mode: str
    capacity: int = 0

class SteganoProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SteganoPro Ultimate")
        self.geometry("850x700")
        self.minsize(800, 600)
        self.image_info: Optional[ImageInfo] = None
        self.current_lsb = 1
        
        # Configuration de la fenêtre principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Conteneur principal
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.show_home()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_container()
        
        # Header
        header = ctk.CTkFrame(self.container)
        header.pack(pady=(20, 40), fill="x")
        ctk.CTkLabel(header, text="SteganoPro Ultimate", 
                     font=ctk.CTkFont(size=28, weight="bold")).pack()
        
        # Boutons principaux
        buttons_frame = ctk.CTkFrame(self.container)
        buttons_frame.pack(pady=20)
        
        btn_enc = ctk.CTkButton(
            buttons_frame, 
            text="📥 Cacher un message", 
            width=250,
            height=50,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=16),
            command=self.show_encode_interface
        )
        btn_enc.grid(row=0, column=0, padx=20, pady=10)
        
        btn_dec = ctk.CTkButton(
            buttons_frame, 
            text="📤 Révéler un message", 
            width=250,
            height=50,
            fg_color="#2196F3",
            hover_color="#0b7dda",
            font=ctk.CTkFont(size=16),
            command=self.show_decode_interface
        )
        btn_dec.grid(row=0, column=1, padx=20, pady=10)
        
        # Footer
        footer = ctk.CTkFrame(self.container)
        footer.pack(side="bottom", fill="x", pady=(40, 10))
        ctk.CTkLabel(footer, text="© 2023 SteganoPro Ultimate", 
                    text_color="gray").pack()

    def show_encode_interface(self, prefill_message: str = ""):
        self.clear_container()
        
        # Header avec bouton retour
        header = ctk.CTkFrame(self.container)
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            header, 
            text="← Retour", 
            width=80,
            command=self.show_home
        ).pack(side="left")
        
        ctk.CTkLabel(
            header, 
            text="Cacher un message", 
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=20)
        
        # Sélection d'image
        img_frame = ctk.CTkFrame(self.container)
        img_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            img_frame,
            text="📁 Choisir une image",
            command=self.select_image_encode
        ).pack(side="left", padx=5)
        
        self.lbl_image = ctk.CTkLabel(img_frame, text="Aucune image sélectionnée")
        self.lbl_image.pack(side="left", padx=10)
        
        # Options LSB
        options_frame = ctk.CTkFrame(self.container)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(options_frame, text="Bits LSB:").pack(side="left", padx=5)
        
        self.lsb_slider = ctk.CTkSlider(
            options_frame, 
            from_=1, 
            to=MAX_LSB, 
            number_of_steps=MAX_LSB-1,
            command=self.update_capacity
        )
        self.lsb_slider.set(1)
        self.lsb_slider.pack(side="left", padx=5)
        
        self.lsb_label = ctk.CTkLabel(options_frame, text="1")
        self.lsb_label.pack(side="left", padx=5)
        
        # Capacité
        self.capacity_frame = ctk.CTkFrame(self.container)
        self.capacity_frame.pack(fill="x", pady=10)
        
        self.lbl_capacity = ctk.CTkLabel(self.capacity_frame, text="Capacité estimée: -")
        self.lbl_capacity.pack(side="left")
        
        # Zone de texte pour le message
        self.txt_message = ctk.CTkTextbox(
            self.container, 
            width=600, 
            height=150,
            wrap="word",
            font=ctk.CTkFont(size=14)
        )
        self.txt_message.pack(pady=10, fill="x", padx=20)
        self.txt_message.insert("0.0", prefill_message)
        self.txt_message.bind("<KeyRelease>", self.update_usage)
        
        # Indicateur d'utilisation
        self.usage_frame = ctk.CTkFrame(self.container)
        self.usage_frame.pack(fill="x", pady=(0, 10), padx=20)
        
        self.usage_label = ctk.CTkLabel(self.usage_frame, text="Utilisation: 0 / 0 bytes (0%)")
        self.usage_label.pack(side="left")
        
        self.usage_pb = ctk.CTkProgressBar(self.usage_frame)
        self.usage_pb.set(0)
        self.usage_pb.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Section sécurité
        security_frame = ctk.CTkFrame(self.container)
        security_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(security_frame, text="Clé secrète:").pack(side="left", padx=5)
        
        self.entry_key = ctk.CTkEntry(
            security_frame, 
            placeholder_text="Entrez une clé de chiffrement",
            show="*",
            width=300
        )
        self.entry_key.pack(side="left", padx=5)
        
        self.show_key_btn = ctk.CTkButton(
            security_frame,
            text="👁",
            width=30,
            command=self.toggle_key_visibility
        )
        self.show_key_btn.pack(side="left", padx=5)
        
        # Boutons d'action
        btn_frame = ctk.CTkFrame(self.container)
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Cacher le message",
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=self.start_encode
        ).pack(side="right", padx=10)
        
        # Barre de progression
        self.encode_pb = ctk.CTkProgressBar(self.container)
        
        # Mise à jour initiale
        self.update_capacity()

    def toggle_key_visibility(self):
        current_show = self.entry_key.cget("show")
        self.entry_key.configure(show="" if current_show == "*" else "*")
        self.show_key_btn.configure(text="👁" if current_show == "*" else "🔒")

    def select_image_encode(self):
        path = filedialog.askopenfilename(filetypes=DEFAULT_IMAGE_FORMATS)
        if not path:
            return
            
        try:
            with Image.open(path) as img:
                self.image_info = ImageInfo(
                    path=path,
                    width=img.width,
                    height=img.height,
                    mode=img.mode
                )
                self.lbl_image.configure(text=os.path.basename(path))
                self.update_capacity()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'image:\n{str(e)}")

    def update_capacity(self, *args):
        if not self.image_info:
            return
            
        self.current_lsb = int(self.lsb_slider.get())
        self.lsb_label.configure(text=str(self.current_lsb))
        
        # Calcul de la capacité en bits
        bits_capacity = self.image_info.width * self.image_info.height * 3 * self.current_lsb
        
        # Convertir en octets
        byte_capacity = bits_capacity // 8
        
        # Ajuster pour le padding AES
        if self.entry_key.get():
            byte_capacity = (byte_capacity // BLOCK_SIZE) * BLOCK_SIZE
            
        self.image_info.capacity = byte_capacity
        self.lbl_capacity.configure(
            text=f"Capacité estimée: {byte_capacity} octets "
                 f"({self.image_info.width}x{self.image_info.height}, {self.current_lsb} LSB)"
        )
        self.update_usage()

    def update_usage(self, event=None):
        if not self.image_info:
            return
            
        text = self.txt_message.get("0.0", "end-1c")
        used_bytes = len(text.encode('utf-8'))
        
        # Estimation de la taille compressée
        try:
            compressed_size = len(zlib.compress(text.encode('utf-8')))
            compression_ratio = f" (compressé: ~{compressed_size} octets)"
        except:
            compression_ratio = ""
            
        pct = min(used_bytes / self.image_info.capacity, 1.0) if self.image_info.capacity else 0
        
        self.usage_label.configure(
            text=f"Utilisation: {used_bytes}{compression_ratio} / {self.image_info.capacity} octets ({pct*100:.1f}%)"
        )
        self.usage_pb.set(pct)
        
        # Changer la couleur si dépassement
        if pct > 0.9:
            self.usage_label.configure(text_color="red")
        elif pct > 0.7:
            self.usage_label.configure(text_color="orange")
        else:
            self.usage_label.configure(text_color="white")

    def start_encode(self):
        if not self.image_info:
            messagebox.showerror("Erreur", "Veuillez choisir une image.")
            return
            
        msg = self.txt_message.get("0.0", "end-1c").strip()
        if not msg:
            messagebox.showerror("Erreur", "Veuillez entrer un message.")
            return
            
        key = self.entry_key.get().strip()
        if not key:
            if messagebox.askyesno("Confirmation", 
                                 "Aucune clé fournie - le message ne sera pas chiffré.\nContinuer ?"):
                key = None
            else:
                return
                
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("BMP", "*.bmp")],
            title="Enregistrer l'image avec le message caché"
        )
        
        if not save_path:
            return
            
        # Avertissement si format avec perte
        if not save_path.lower().endswith(('.png', '.bmp')):
            if not messagebox.askyesno("Attention", 
                                      "Les formats autres que PNG/BMP peuvent causer une perte de données.\n"
                                      "Voulez-vous vraiment continuer ?"):
                return
                
        # Démarrer l'encodage
        self.encode_pb.set(0)
        self.encode_pb.pack(fill="x", pady=10, padx=20)
        
        threading.Thread(
            target=self.encode_worker,
            args=(msg, key, save_path),
            daemon=True
        ).start()

    def encode_worker(self, msg: str, key: Optional[str], out_path: str):
        try:
            # Préparation des données
            data = msg.encode('utf-8')
            
            # Compression
            compressed = zlib.compress(data)
            if len(compressed) < len(data):
                data = compressed
                
            # Chiffrement
            if key:
                cipher = AES.new(pad(key.encode(), BLOCK_SIZE), AES.MODE_ECB)
                data = cipher.encrypt(pad(data, BLOCK_SIZE))
                
            # Conversion en binaire
            binary_data = ''.join(f"{b:08b}" for b in data)
            binary_data += "0" * 16  # Marqueur de fin
            
            # Chargement de l'image
            with Image.open(self.image_info.path) as img:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                    
                pixels = img.load()
                total_bits = len(binary_data)
                bit_index = 0
                
                # Parcours des pixels
                for y in range(img.height):
                    for x in range(img.width):
                        if bit_index >= total_bits:
                            break
                            
                        r, g, b = pixels[x, y][:3]
                        
                        # Modification des LSB
                        for i, color in enumerate((r, g, b)):
                            if bit_index < total_bits:
                                mask = ~((1 << self.current_lsb) - 1)
                                bits = binary_data[bit_index:bit_index+self.current_lsb]
                                bits = bits.ljust(self.current_lsb, '0')
                                new_color = (color & mask) | int(bits, 2)
                                
                                if i == 0:
                                    r = new_color
                                elif i == 1:
                                    g = new_color
                                else:
                                    b = new_color
                                    
                                bit_index += self.current_lsb
                                
                        pixels[x, y] = (r, g, b)
                    
                    # Mise à jour de la progression
                    progress = min(bit_index / total_bits, 1.0)
                    self.after(0, lambda: self.encode_pb.set(progress))
                    
                    if bit_index >= total_bits:
                        break
                        
                # Sauvegarde
                img.save(out_path)
                
            self.after(0, lambda: messagebox.showinfo(
                "Succès", 
                f"Message caché avec succès dans:\n{out_path}"
            ))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Erreur", 
                f"Échec de l'encodage:\n{str(e)}"
            ))
        finally:
            self.after(0, lambda: self.encode_pb.pack_forget())

    def show_decode_interface(self):
        self.clear_container()
        
        # Header avec bouton retour
        header = ctk.CTkFrame(self.container)
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            header, 
            text="← Retour", 
            width=80,
            command=self.show_home
        ).pack(side="left")
        
        ctk.CTkLabel(
            header, 
            text="Révéler un message", 
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=20)
        
        # Sélection d'image
        img_frame = ctk.CTkFrame(self.container)
        img_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            img_frame,
            text="📁 Choisir une image",
            command=self.select_image_decode
        ).pack(side="left", padx=5)
        
        self.lbl_decode_image = ctk.CTkLabel(img_frame, text="Aucune image sélectionnée")
        self.lbl_decode_image.pack(side="left", padx=10)
        
        # Options LSB
        options_frame = ctk.CTkFrame(self.container)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(options_frame, text="Bits LSB:").pack(side="left", padx=5)
        
        self.decode_lsb_slider = ctk.CTkSlider(
            options_frame, 
            from_=1, 
            to=MAX_LSB, 
            number_of_steps=MAX_LSB-1
        )
        self.decode_lsb_slider.set(1)
        self.decode_lsb_slider.pack(side="left", padx=5)
        
        self.decode_lsb_label = ctk.CTkLabel(options_frame, text="1")
        self.decode_lsb_label.pack(side="left", padx=5)
        
        # Section sécurité
        security_frame = ctk.CTkFrame(self.container)
        security_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(security_frame, text="Clé secrète:").pack(side="left", padx=5)
        
        self.decode_entry_key = ctk.CTkEntry(
            security_frame, 
            placeholder_text="Entrez la clé de chiffrement (si nécessaire)",
            show="*",
            width=300
        )
        self.decode_entry_key.pack(side="left", padx=5)
        
        self.decode_show_key_btn = ctk.CTkButton(
            security_frame,
            text="👁",
            width=30,
            command=lambda: self.toggle_key_visibility(self.decode_entry_key, self.decode_show_key_btn)
        )
        self.decode_show_key_btn.pack(side="left", padx=5)
        
        # Boutons d'action
        btn_frame = ctk.CTkFrame(self.container)
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Révéler le message",
            fg_color="#2196F3",
            hover_color="#0b7dda",
            command=self.start_decode
        ).pack(side="right", padx=10)
        
        # Barre de progression
        self.decode_pb = ctk.CTkProgressBar(self.container)
        
        # Zone de résultat
        self.result_frame = ctk.CTkFrame(self.container)
        
        self.txt_result = ctk.CTkTextbox(
            self.result_frame,
            width=600,
            height=150,
            wrap="word",
            font=ctk.CTkFont(size=14)
        )
        self.txt_result.pack(pady=10, fill="both", expand=True, padx=10)
        
        # Boutons de résultat
        self.result_buttons = ctk.CTkFrame(self.result_frame)
        self.result_buttons.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkButton(
            self.result_buttons,
            text="Copier",
            command=self.copy_result
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            self.result_buttons,
            text="Réencoder",
            fg_color="#4CAF50",
            command=self.reencode_result
        ).pack(side="left", padx=5)

    def select_image_decode(self):
        path = filedialog.askopenfilename(filetypes=DEFAULT_IMAGE_FORMATS)
        if not path:
            return
            
        self.decode_image_path = path
        self.lbl_decode_image.configure(text=os.path.basename(path))

    def start_decode(self):
        if not hasattr(self, 'decode_image_path') or not self.decode_image_path:
            messagebox.showerror("Erreur", "Veuillez choisir une image.")
            return
            
        lsb = int(self.decode_lsb_slider.get())
        key = self.decode_entry_key.get().strip()
        
        # Démarrer le décodage
        self.decode_pb.set(0)
        self.decode_pb.pack(fill="x", pady=10, padx=20)
        
        threading.Thread(
            target=self.decode_worker,
            args=(self.decode_image_path, lsb, key),
            daemon=True
        ).start()

    def decode_worker(self, image_path: str, lsb: int, key: str):
        try:
            with Image.open(image_path) as img:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                    
                width, height = img.size
                pixels = img.load()
                binary_data = []
                total_pixels = width * height
                processed_pixels = 0
                
                # Extraction des bits LSB
                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y][:3]
                        
                        for color in (r, g, b):
                            bits = color & ((1 << lsb) - 1)
                            binary_data.append(f"{bits:0{lsb}b}")
                            
                        processed_pixels += 1
                        if processed_pixels % 100 == 0:
                            progress = processed_pixels / total_pixels
                            self.after(0, lambda: self.decode_pb.set(progress))
                
                # Conversion en bytes
                binary_str = ''.join(binary_data)
                bytes_data = bytearray()
                
                for i in range(0, len(binary_str), 8):
                    byte_str = binary_str[i:i+8]
                    if len(byte_str) < 8:
                        break
                    bytes_data.append(int(byte_str, 2))
                
                # Détection du marqueur de fin
                end_marker = bytes_data.find(b'\x00\x00')
                if end_marker != -1:
                    bytes_data = bytes_data[:end_marker]
                
                # Déchiffrement si nécessaire
                if key:
                    try:
                        cipher = AES.new(pad(key.encode(), BLOCK_SIZE), AES.MODE_ECB)
                        bytes_data = unpad(cipher.decrypt(bytes_data), BLOCK_SIZE)
                    except Exception as e:
                        raise ValueError(f"Erreur de déchiffrement - mauvais mot de passe ?\n{str(e)}")
                
                # Décompression
                try:
                    bytes_data = zlib.decompress(bytes_data)
                except:
                    pass  # Peut-être pas compressé
                
                # Affichage du résultat
                result = bytes_data.decode('utf-8', errors='replace')
                self.after(0, lambda: self.show_decode_result(result))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Erreur", 
                f"Échec du décodage:\n{str(e)}\n\nConseils:\n"
                "- Vérifiez le nombre de bits LSB\n"
                "- Vérifiez la clé de chiffrement\n"
                "- L'image peut être corrompue"
            ))
        finally:
            self.after(0, lambda: self.decode_pb.pack_forget())

    def show_decode_result(self, result: str):
        self.result_frame.pack(fill="both", expand=True, pady=10, padx=20)
        self.txt_result.delete("0.0", "end")
        self.txt_result.insert("0.0", result)
        
        # Stocker le résultat pour réencodage
        self.last_decoded_message = result

    def copy_result(self):
        text = self.txt_result.get("0.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Succès", "Message copié dans le presse-papiers")

    def reencode_result(self):
        if hasattr(self, 'last_decoded_message'):
            self.show_encode_interface(self.last_decoded_message)

if __name__ == "__main__":
    app = SteganoProApp()
    app.mainloop()