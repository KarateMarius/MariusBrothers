import pygame as py
import random
import os
import pygame.mixer
import pygame.time
import pygame.font
from csv import reader
from os import walk
from ffpyplayer.player import MediaPlayer
from ffpyplayer.tools import set_loglevel
from pymediainfo import MediaInfo
from errno import ENOENT

# pygame initialisieren
py.init()

# fenster attribute
fenster_width = 960
fenster_height = 720
testfenster = py.display.set_mode((fenster_width, fenster_height)) #py.FULLSCREEN
py.display.set_caption("Marius Brothers™")
clock = py.time.Clock()
fps = 60

class Button():
	def __init__(self, image, pos, text_input, font, base_color, hovering_color):
		self.image = image
		self.x_pos = pos[0]
		self.y_pos = pos[1]
		self.font = font
		self.base_color, self.hovering_color = base_color, hovering_color
		self.text_input = text_input
		self.text = self.font.render(self.text_input, True, self.base_color)
		if self.image is None:
			self.image = self.text
		self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
		self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

	def update(self, screen):
		if self.image is not None:
			screen.blit(self.image, self.rect)
		screen.blit(self.text, self.text_rect)

	def checkForInput(self, position):
		if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
			return True
		return False

	def changeColor(self, position):
		if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
			self.text = self.font.render(self.text_input, True, self.hovering_color)
		else:
			self.text = self.font.render(self.text_input, True, self.base_color)

class Video:
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(ENOENT, os.strerror(ENOENT), path)
        set_loglevel("quiet")

        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]

        self._video = MediaPlayer(path)
        self._frame_num = 0

        info = MediaInfo.parse(path).video_tracks[0]

        self.frame_rate = float(info.frame_rate)
        self.frame_count = int(info.frame_count)
        self.frame_delay = 1 / self.frame_rate
        self.duration = info.duration / 1000
        self.original_size = (info.width, info.height)
        self.current_size = self.original_size

        self.active = True
        self.frame_surf = pygame.Surface((0, 0))

        self.alt_resize = pygame.transform.smoothscale

    def close(self):
        self._video.close_player()

    def restart(self):
        self._video.seek(0, relative=False)
        self._frame_num = 0
        self.frame_surf = None
        self.active = True

    def set_size(self, size: tuple):
        self._video.set_size(*size)
        self.current_size = size

    # volume goes from 0.0 to 1.0
    def set_volume(self, volume: float):
        self._video.set_volume(volume)

    def get_volume(self) -> float:
        return self._video.get_volume()

    def get_paused(self) -> bool:
        return self._video.get_pause()

    def pause(self):
        self._video.set_pause(True)

    def resume(self):
        self._video.set_pause(False)

    # gets time in seconds
    def get_pos(self) -> float:
        return self._video.get_pts()

    def toggle_pause(self):
        self._video.toggle_pause()

    def _update(self):
        updated = False

        if self._frame_num + 1 == self.frame_count:
            self.active = False
            return False

        while self._video.get_pts() > self._frame_num * self.frame_delay:
            frame = self._video.get_frame()[0]
            self._frame_num += 1

            if frame != None:
                size = frame[0].get_size()
                img = pygame.image.frombuffer(frame[0].to_bytearray()[0], size, "RGB")
                if size != self.current_size:
                    img = self.alt_resize(img, self.current_size)
                self.frame_surf = img

                updated = True

        return updated

    # seek uses seconds
    def seek(self, seek_time: int):
        vid_time = self._video.get_pts()
        if vid_time + seek_time < self.duration and self.active:
            self._video.seek(seek_time)
            while vid_time + seek_time < self._frame_num * self.frame_delay:
                self._frame_num -= 1

    def draw(self, surf: pygame.Surface, pos: tuple, force_draw: bool = True) -> bool:
        if self.active and (self._update() or force_draw):
            surf.blit(self.frame_surf, pos)
            return True

        return False


vid = Video("assets/video/Marius Brothers Start.mp4")
vid.set_size((960, 720))


def intro():
    yes = True
    while yes:
        vid.draw(testfenster, (0, 0))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                yes = False
    Play()


# starten des pygame fenster


def Play():
    # spieler klasse mit eigenschaften und definitionen des spielers
    class Spieler(py.sprite.Sprite):
        def __init__(self, position):
            super().__init__()  # brauch man um die sprites (bilder) darzustellen

            # liste der animations-zustände
            self.animations_liste = {"stand": [], "walk": [], "jump": [], "falling": []}
            self.import_charakter_ordner()
            # (ersetzt array) angabe des animierten spieler ordners (move stand jump fall)
            self.frame_nummer = 0
            self.animation_geschw = 0.175

            self.image = self.animations_liste["stand"][self.frame_nummer]
            self.rect = self.image.get_rect(topleft=position)

            # spieler variablen
            # in x richtung (.x)nur ändern um 1 für links rechts richtung
            # wie das array nur einfacher da zustand über "True" 1 und False 0
            self.richtung = py.math.Vector2(0, 0)
            self.geschw = 8
            self.gravity = 0.8
            self.jump_geschw = -16
            self.collision_rect = py.Rect(self.rect.topleft, (40, self.rect.height))

            # spieler animationsstatus
            self.status = "stand"
            self.blick_right = True
            self.touch_boden = False
            self.touch_decke = False
            self.touch_left = False
            self.touch_right = False

            # spieler sound
            if entry_get == "Lena":
                self.jump_sound = py.mixer.Sound("assets/musik/jump2.ogg")
            else:
                self.jump_sound = py.mixer.Sound("assets/musik/jump.ogg")

        # importieren der animations ordner inhalte
        def import_charakter_ordner(self):
            if entry_get == "Lena":
                character_path = "assets/character/char2/"
            else:
                character_path = "assets/character/char1/"

            for animation in self.animations_liste.keys():
                full_path = character_path + animation
                self.animations_liste[animation] = import_ordner(full_path)

        # animieren des spielers
        def animiere(self):
            animation = self.animations_liste[self.status]

            # legt die abspielgeschwindigkeit fest
            self.frame_nummer += self.animation_geschw
            if self.frame_nummer >= len(animation):
                self.frame_nummer = 0

            # festlegen der richtung für den spielersprite
            image = animation[int(self.frame_nummer)]
            if self.blick_right:
                self.image = image
                self.rect.bottomleft = self.collision_rect.bottomleft
            else:
                flipped_image = py.transform.flip(image, True, False)
                self.image = flipped_image
                self.rect.bottomright = self.collision_rect.bottomright

            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

        # schaut ob der benutzer eine der gesuchten tasten drückt?
        def get_input(self):
            keys = py.key.get_pressed()

            # setzt die richtung (den vector) auf 1 also True
            if keys[py.K_LEFT] or keys[py.K_a]:
                self.richtung.x = -1
                self.blick_right = False
            elif keys[py.K_RIGHT] or keys[py.K_d]:
                self.richtung.x = 1
                self.blick_right = True
            else:
                self.richtung.x = 0

            if keys[py.K_SPACE] and self.touch_boden or keys[py.K_UP] and self.touch_boden or keys[
                py.K_w] and self.touch_boden:
                self.jump()

            if keys[py.K_ESCAPE]:

                # prüft ob der spieler "runterfällt"
                if not self.rect.top > fenster_height:
                    if not entry_get:
                        spielername = "Player"
                    else:
                        spielername = entry_get

                    file = open("assets/txts/highscore.txt", "a")
                    file.write(str(clicked_level) + " " + str(spielername) + " " + str(round(game.score)) + "\n")
                    file.close()
                    py.quit()
                else:
                    py.quit()

        # setzt den animationsstatus je nach zu stand für den charakter
        def spieler_animation_status(self):
            if self.richtung.y < 0:
                self.status = "jump"
            elif self.richtung.y > 1:
                self.status = "falling"
            else:
                if self.richtung.x != 0:
                    self.status = "walk"
                else:
                    self.status = "stand"

        # nach unten fallen immer aktiv (wird durch collision außer Kraft gesetzt)
        def gravity_movement(self):
            self.richtung.y += self.gravity
            self.collision_rect.y += self.richtung.y

        # sprung
        def jump(self):
            self.richtung.y = self.jump_geschw
            # wenn der spieler keine +y macht kein sprung sound
            if self.jump_geschw == 0:
                self.jump_sound.set_volume(0)
            else:
                self.jump_sound.play()

        # update methode zum immer ausführen gebrauchter funktionen
        def update(self):
            self.get_input()
            self.spieler_animation_status()
            self.animiere()

    # blockklasse für die einzelnen welten
    # festlegen der hitbox
    # updaten der poistion
    class Block(py.sprite.Sprite):
        def __init__(self, size, x, y):
            super().__init__()
            self.image = py.Surface((size, size))
            self.rect = self.image.get_rect(topleft=(x, y))

        def update(self, verschiebung):
            self.rect.x += verschiebung

    # nicht animiter block
    # nur änderung der koordinaten
    class Statischer_Block(Block):
        def __init__(self, size, x, y, ebene):
            super().__init__(size, x, y)
            self.image = ebene

    # animiter block (z.b. blume)
    # zeitliches getimtes austauschen
    class Animierter_Block(Block):
        def __init__(self, size, x, y, path):
            super().__init__(size, x, y)
            self.bilder = import_ordner(path)
            self.frame_nummer = 0
            self.image = self.bilder[self.frame_nummer]

        def animiere(self):
            # änderung des bildes
            self.frame_nummer += 0.05
            if self.frame_nummer >= len(self.bilder):
                self.frame_nummer = 0
            self.image = self.bilder[int(self.frame_nummer)]

        # änderung der blockeingenschaften
        def update(self, verschiebung):
            self.animiere()
            self.rect.x += verschiebung

    # dasselbe wie der animierte block
    # nur die bilder im ordner werden schneller durchlaufen
    class Schnell_Animierter_Block(Block):
        def __init__(self, size, x, y, path):
            super().__init__(size, x, y)
            self.bilder = import_ordner(path)
            self.frame_nummer = 0
            self.image = self.bilder[self.frame_nummer]

        def animiere(self):
            self.frame_nummer += 0.15
            if self.frame_nummer >= len(self.bilder):
                self.frame_nummer = 0
            self.image = self.bilder[int(self.frame_nummer)]

        def update(self, verschiebung):
            self.animiere()
            self.rect.x += verschiebung

    # generiert den himmel
    class Himmel:
        def __init__(self, horizont_height):
            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4":
                self.oben = py.image.load("assets/blocks/himmel3/himmel1.png")
                self.mitte = py.image.load("assets/blocks/himmel3/himmel2.png")
                self.unten = py.image.load("assets/blocks/himmel3/himmel3.png")
            else:
                self.oben = py.image.load("assets/blocks/himmel/himmel1.png")
                self.mitte = py.image.load("assets/blocks/himmel/himmel2.png")
                self.unten = py.image.load("assets/blocks/himmel/himmel3.png")

            # grenze für oberes himmelstück (bis zum übergang)
            self.horizont_height = horizont_height

            # einzelne himmel bilder werden auf die breite des fensters gestreckt -> statischer hintergrund
            self.oben = py.transform.scale(self.oben, (fenster_width, block_size))
            self.mitte = py.transform.scale(self.mitte, (fenster_width, block_size))
            self.unten = py.transform.scale(self.unten, (fenster_width, block_size))

        # zeichnen des himmels im "pyfenster"/grundlage
        def draw(self, ebene):
            for reihen in range(vertical_blocks):
                x = 0
                y = reihen * block_size
                if reihen < self.horizont_height:
                    ebene.blit(self.oben, (x, y))
                elif reihen == self.horizont_height:
                    ebene.blit(self.mitte, (x, y))
                else:
                    ebene.blit(self.unten, (x, y))

    # wasser klasse
    # bild wird x mal kopiert das es ein stück über das level hinaus ragt
    # wird vor dem himmel aber unter dem level gezeichnet
    class Wasser:
        def __init__(self, top, level_width):
            wasser_start = -fenster_width
            wasser_block_width = 192
            block_x_menge = int((level_width + fenster_width) / wasser_block_width)  # wassermenge
            self.wasser_ebene = py.sprite.Group()

            for block in range(block_x_menge):
                x = block * wasser_block_width + wasser_start
                y = top
                sprite = Animierter_Block(192, x, y, "assets/blocks/wasser")
                self.wasser_ebene.add(sprite)

        def draw(self, ebene, wasser_verschiebung):
            self.wasser_ebene.update(wasser_verschiebung)
            self.wasser_ebene.draw(ebene)

    # wolken klasse
    # generiert eine bestimmte anzahl von wolken an einer zufälligen position auf den bildschirm
    class Wolken:
        def __init__(self, horizont_height, level_width, wolken_number):

            if clicked_level == "World 1 - 2" and not "Leo" == entry_get or clicked_level == "World 1 - 2" and not "Leo" == entry_get:
                wolken_surf_liste = import_ordner("assets/blocks/wolken")
            elif clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4" or clicked_level == "World 1 - 8":
                wolken_surf_liste = import_ordner("assets/blocks/schnee")
            elif entry_get == "Leo" and clicked_level == "World 1 - 2":
                wolken_surf_liste = import_ordner("assets/blocks/hexe")
            else:
                wolken_surf_liste = import_ordner("assets/blocks/wolken")
            min_x = -fenster_width
            max_x = level_width + fenster_width
            min_y = 0
            max_y = horizont_height
            self.wolken_ebene = py.sprite.Group()

            # positions bestimmung der wolken
            for wolken in range(wolken_number):
                wolken = random.choice(wolken_surf_liste)
                x = random.randint(min_x, max_x)
                y = random.randint(min_y, max_y)
                sprite = Statischer_Block(0, x, y, wolken)
                self.wolken_ebene.add(sprite)

        # zeichnen der wolken
        # bewegen der wolken (langsamer als das level weil cool)
        def draw(self, ebene, verschiebung):
            self.wolken_ebene.update(verschiebung)
            self.wolken_ebene.draw(ebene)

    # level klasse
    # eigentliches spiel
    # level werden erstellt auseinander gehalten und je nach zustand verschiedene features aktiviert
    class Level:
        def __init__(self, level_data, ebene):

            # splash screen font
            self.font_name = py.font.match_font("arial")

            # bestimmen der level musik für bestimmte level
            if clicked_level == "World 1 - 1":
                self.level_bg_music = py.mixer.Sound("assets/musik/Intro Theme.ogg")
                self.level_bg_music.set_volume(0.3)
            elif clicked_level == "World 1 - 2":
                self.level_bg_music = py.mixer.Sound("assets/musik/happy.ogg")
                self.level_bg_music.set_volume(0.3)
            elif clicked_level == "World 1 - 3":
                self.level_bg_music = py.mixer.Sound("assets/musik/Worldmap Theme.ogg")
                self.level_bg_music.set_volume(0.3)
            elif clicked_level == "World 1 - 4":
                self.level_bg_music = py.mixer.Sound("assets/musik/ChillWinterLoopable.ogg")
                self.level_bg_music.set_volume(0.3)
            # eine easter egg musik -> für das jungle level welcome to the jungle
            # wenn der spieler name "Guns n Roses" lautet wird dieses feature aktiviert
            elif clicked_level == "World 1 - 5":
                if entry_get == "Guns n Roses":
                    self.level_bg_music = py.mixer.Sound(
                        "assets/musik/welcome-to-the-jungle-studio-version-high-quality.ogg")
                    self.level_bg_music.set_volume(0.3)
                # wenn nicht wird die normale jungle level musik abgespielt
                else:
                    self.level_bg_music = py.mixer.Sound("assets/musik/Jungle.ogg")
                    self.level_bg_music.set_volume(0.1)
            elif clicked_level == "World 1 - 6":
                self.level_bg_music = py.mixer.Sound("assets/musik/the-lion-sleeps-tonight-wimoweh-audio.ogg")
                self.level_bg_music.set_volume(0.1)
            elif clicked_level == "World 1 - 7":
                self.level_bg_music = py.mixer.Sound("assets/musik/bhh.mp3")
                self.level_bg_music.set_volume(0.2)
            elif clicked_level == "World 1 - 8":
                self.level_bg_music = py.mixer.Sound("assets/musik/sah.mp3")
                self.level_bg_music.set_volume(0.2)
            # wenn als spielername die "666" eingegeben wird
            # spielt in jedem level von iron maiden "the number of the beast" (666)
            if entry_get == "666":
                self.level_bg_music = py.mixer.Sound("assets/musik/the-number-of-the-beast-1998-remaster.ogg")
                self.level_bg_music.set_volume(0.3)
            # bestes lied eines freundes als easteregg für einen seiner ingame namen
            if entry_get == "lmaoscur":
                self.level_bg_music = py.mixer.Sound("assets/musik/dnd.ogg")
                self.level_bg_music.set_volume(0.3)

            # falls der spieler das level länger spielt als das lied lang ist fängst dies eif wieder von vorne an
            self.level_bg_music.play(loops=-1)

            # einsammeln von münzen sound
            self.coin_sound = py.mixer.Sound("assets/musik/coin.ogg")
            self.coin_sound.set_volume(0.5)

            # GUI (graphical user interface) attribute
            self.ui = GUI(pyfenster)

            # münzen menge zum start des spieles
            self.coins = 0

            # zeit für das level
            # loop erscheint dadurch sinnlos aber 312 sekunden sind über 5 min und so lang geht nich jedes lied
            self.time_left = 312

            # "True" oder "False" statement um zu prüfen ob das zeit runterzählen gestoppt werden soll
            self.time_stop = 0

            # level klasse eigenschaften
            self.draw_ebene = ebene  # -> pyfenster
            self.level_verschiebung = 0  # -> solang der spieler sich nicht bewegt
            self.wolken_verschiebung = self.level_verschiebung / 2  # -> für cooleren wolken scroll effekt nur die halbe geschw

            # importieren der start- und endposition des spielers
            spieler_layout = import_csv_datei(level_data["spieler"])
            self.spieler = py.sprite.GroupSingle()
            self.ziel = py.sprite.GroupSingle()
            self.setup_spieler(spieler_layout)

            # level blöcke laden
            untergrund_layout = import_csv_datei(level_data["untergrund"])
            self.untergrund_ebene = self.level_sprite_group(untergrund_layout, "untergrund")

            # level länge also maximale block gerade (nicht durchgängig sondern theoretisch möglich)
            level_width = (len(
                untergrund_layout[0]) * block_size)  # muss an die stell durch die abhänigkeit an den untergrund

            bereich_layout = import_csv_datei(level_data["ziel"])
            self.bereich_ebene = self.level_sprite_group(bereich_layout, "ziel")

            decoration_layout = import_csv_datei(level_data["dekorationen"])
            self.decoration_ebene = self.level_sprite_group(decoration_layout, "dekorationen")

            # für manche level sind nur bestimmte texturen gebraucht diese werden aus und eingeschalten
            if not clicked_level == "World 1 - 5" and not clicked_level == "World 1 - 6" and not clicked_level == "World 1 - 7":
                blumen_layout = import_csv_datei(level_data["blumen"])
                self.blumen_ebene = self.level_sprite_group(blumen_layout, "blumen")

            coin_layout = import_csv_datei(level_data["coins"])
            self.coin_ebene = self.level_sprite_group(coin_layout, "coins")

            baum_layout = import_csv_datei(level_data["baum"])
            self.baum_ebene = self.level_sprite_group(baum_layout, "baum")

            if not clicked_level == "World 1 - 3" and not clicked_level == "World 1 - 4" and not clicked_level == "World 1 - 8":
                busch_layout = import_csv_datei(level_data["busch"])
                self.busch_ebene = self.level_sprite_group(busch_layout, "busch")
                if not clicked_level == "World 1 - 5" and not clicked_level == "World 1 - 6":
                    pilze_layout = import_csv_datei(level_data["pilze"])
                    self.pilze_ebene = self.level_sprite_group(pilze_layout, "pilze")

            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4" or clicked_level == "World 1 - 8":
                geschenk_layout = import_csv_datei(level_data["geschenk"])
                self.geschenk_ebene = self.level_sprite_group(geschenk_layout, "geschenk")

            if clicked_level == "World 1 - 5" or clicked_level == "World 1 - 6":
                busch_2_layout = import_csv_datei(level_data["busch_2"])
                self.busch_2_ebene = self.level_sprite_group(busch_2_layout, "busch_2")

                ranken_layout = import_csv_datei(level_data["ranken"])
                self.ranken_ebene = self.level_sprite_group(ranken_layout, "ranken")

            # nächstes easter egg -> insider -> alle wolken werden durch eine hexe ersetzt
            if entry_get == "Leo":
                self.wolken = Wolken(100, level_width, 100)

            # hier werden die wolken mit schneeflocken ersetzt für das winter level
            elif clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4" or clicked_level == "World 1 - 8":
                self.wolken = Wolken(750, level_width, 100)

            # wenn kein extra der fall ist einfache wolken spawnen
            else:
                self.wolken = Wolken(400, level_width, 20)
            # eigenschaftfestlegung des himmels
            self.himmel = Himmel(11)  # 11 ist die horizont_height also maximale wolken höhe

            # eigenschaftfestlegung des wassers
            self.wasser = Wasser(fenster_height - 40,
                                 level_width * 1.2)  # länge dafür falls der spieler über das ziel hinaus springt oder den anfang

        # zeit herunter zählen
        def change_time(self, sekunden):
            self.time_left -= sekunden

        # überprüfen der zeit
        def check_time(self):

            # wenn zeit herunter gezählt werden soll ist self.time_stop = 0
            if self.time_stop == 0:
                self.change_time(0.02)

                # sorgt dafür das die zeit immer die gleiche länge hat
                # 002 sekunden
                # 100 sekunden
                # fügt an den anfang "0" hinzu damit sich die visuelle länge nicht ändert
                if self.time_left >= 100:
                    self.time_left_string = str(round(self.time_left))
                if self.time_left < 100:
                    self.time_left_string = "0" + str(round(self.time_left))
                    if self.time_left < 10:
                        self.time_left_string = "00" + str(round(self.time_left))

                        # wenn keine zeit mehr vorhanden musik immer leiser werden lassen
                        # "abspielen" des verloren fensters
                        if self.time_left <= 0:
                            pygame.mixer.fadeout(500)
                            pyfenster.fill("black")
                            self.draw_text("Deine Zeit ist abgelaufen!", 48, "white", fenster_width / 2,
                                           fenster_height / 2)
            elif self.time_stop == 1:
                # ausführen keiner funktion da hier nur das zeit management stattfindet
                # abgeschlossen und heruntergefallen (verloren) splash screen in eigener funktion
                pass

        # ändern der münzen menge des spielers
        def change_coins(self, menge):
            self.coins += menge

        # prüfen ob der spieler mit einer münze in kontakt kommt
        def check_coin_collisions(self):
            collided_coins = py.sprite.spritecollide(self.spieler.sprite, self.coin_ebene, True)
            # wenn ja abspielen des münzen einsammel geräuschs und ändern der eingesammelten coin menge
            if collided_coins:
                self.coin_sound.play()

                # kann mit mehreren münzen gleichzeitig kollidieren
                for coin in collided_coins:
                    self.change_coins(1)

        # laden der einzelnen blockgrafiken
        def level_sprite_group(self, layout, typ):

            # große sprite gruppe wo alle blöcke gesammelt werden
            sprite_group = py.sprite.Group()

            # mehr im csv abschnitt (imports.py)
            for reihen_nummer, reihen in enumerate(layout):
                for spalten_nummer, nummer in enumerate(reihen):

                    # ein value von -1 in der csv datei bedeutet "Luft" also kein block
                    if nummer != "-1":
                        x = spalten_nummer * block_size
                        y = reihen_nummer * block_size

                        # für level unterschiede bestimmtes laden der blöcke
                        # typ wird durch ein dictonary festgelegt das mit einer csv-datei verbunden ist
                        if typ == "untergrund":
                            if clicked_level == "World 1 - 1" or clicked_level == "World 1 - 2" or clicked_level == "World 1 - 7":
                                untergrund_block_liste = grafiken_teilen("assets/blocks/blöcke2.png")
                                block_ebene = untergrund_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4" or clicked_level == "World 1 - 8":
                                untergrund_block_liste = grafiken_teilen("assets/blocks/blöcke3.png")
                                block_ebene = untergrund_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                            if clicked_level == "World 1 - 5" or clicked_level == "World 1 - 6":
                                untergrund_block_liste = grafiken_teilen("assets/blocks/blöcke5.png")
                                block_ebene = untergrund_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                        if typ == "ziel":
                            bereich_block_liste = grafiken_teilen("assets/blocks/Zielkomplett.png")
                            block_ebene = bereich_block_liste[int(nummer)]
                            sprite = Statischer_Block(block_size, x, y, block_ebene)
                            sprite_group.add(sprite)

                        if typ == "dekorationen":
                            decoration_block_liste = grafiken_teilen("assets/blocks/decoration.png")
                            block_ebene = decoration_block_liste[int(nummer)]
                            sprite = Statischer_Block(block_size, x, y, block_ebene)
                            sprite_group.add(sprite)

                        if typ == "blumen":
                            if clicked_level == "World 1 - 1" or clicked_level == "World 1 - 2" or clicked_level == "World 1 - 7":
                                sprite = Animierter_Block(block_size, x, y, "assets/blocks/blumen")
                                sprite_group.add(sprite)

                            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4" or clicked_level == "World 1 - 8":
                                sprite = Animierter_Block(block_size, x, y, "assets/blocks/pusteblume")
                                sprite_group.add(sprite)

                        if typ == "coins":
                            sprite = Schnell_Animierter_Block(block_size, x, y, "assets/blocks/coins")
                            sprite_group.add(sprite)

                        if typ == "baum":
                            if clicked_level == "World 1 - 1" or clicked_level == "World 1 - 2" or clicked_level == "World 1 - 7":
                                baum_block_liste = grafiken_teilen("assets/blocks/tree.png")
                                block_ebene = baum_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4" or clicked_level == "World 1 - 8":
                                baum_block_liste = grafiken_teilen("assets/blocks/winter_bäume.png")
                                block_ebene = baum_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                            if clicked_level == "World 1 - 5" or clicked_level == "World 1 - 6":
                                baum_block_liste = grafiken_teilen("assets/blocks/jungle_baum.png")
                                block_ebene = baum_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                        if typ == "busch":
                            if clicked_level == "World 1 - 1" or clicked_level == "World 1 - 2" or clicked_level == "World 1 - 7":
                                busch_block_liste = grafiken_teilen("assets/blocks/bush.png")
                                block_ebene = busch_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                            if clicked_level == "World 1 - 5" or clicked_level == "World 1 - 6":
                                busch_block_liste = grafiken_teilen("assets/blocks/jungle_busch.png")
                                block_ebene = busch_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                        if typ == "pilze":
                            if clicked_level == "World 1 - 1" or clicked_level == "World 1 - 2" or clicked_level == "World 1 - 7":
                                pilze_block_liste = grafiken_teilen("assets/blocks/shroom.png")
                                block_ebene = pilze_block_liste[int(nummer)]
                                sprite = Statischer_Block(block_size, x, y, block_ebene)
                                sprite_group.add(sprite)

                        if typ == "geschenk":
                            geschenk_block_liste = grafiken_teilen("assets/blocks/geschenk.png")
                            block_ebene = geschenk_block_liste[int(nummer)]
                            sprite = Statischer_Block(block_size, x, y, block_ebene)
                            sprite_group.add(sprite)

                        if typ == "busch_2":
                            busch_2_block_liste = grafiken_teilen("assets/blocks/jungle_busch_2.png")
                            block_ebene = busch_2_block_liste[int(nummer)]
                            sprite = Statischer_Block(block_size, x, y, block_ebene)
                            sprite_group.add(sprite)

                        if typ == "ranken":
                            ranken_block_liste = grafiken_teilen("assets/blocks/ranken.png")
                            block_ebene = ranken_block_liste[int(nummer)]
                            sprite = Statischer_Block(block_size, x, y, block_ebene)
                            sprite_group.add(sprite)

            return sprite_group

        # bestimmer der spieler position
        def setup_spieler(self, layout):

            for reihen_nummer, reihen in enumerate(layout):
                for spalten_nummer, nummer in enumerate(reihen):
                    x = spalten_nummer * block_size
                    y = reihen_nummer * block_size

                    # spieler spawn position
                    # level wird nicht um den spieler herum geladen!!
                    if nummer == "0":
                        sprite = Spieler((x, y))
                        self.spieler.add(sprite)

                    # ziel bereich
                    if nummer == "1":
                        bereich_ebene = py.image.load(
                            "assets/blocks/bereich.png")  # unsichtbares zwischen feld -> gebraucht für die collsion bestimmung
                        sprite = Statischer_Block(block_size, x, y, bereich_ebene)
                        self.ziel.add(sprite)

        # änderung der spieler bewegung in x richtung
        def bewegung_x(self):

            # vor kurzem erstellte spieler sprite
            spieler = self.spieler.sprite

            # für die "Kamera" benötigt
            spieler_x = spieler.rect.centerx
            richtung_x = spieler.richtung.x

            # legt wie eine fenster grenze des spielers fest damit es aussieht als könnte er sich frei im fenster bewegen
            # und dennoch in dem level herum "scrollen"
            # wenn der spieler diese "wand" berührt bewegt sich das level nicht mehr der spieler
            # so wird einfacheres manövrieren im fenster garantiert

            if spieler_x < (fenster_width / 4) and richtung_x < 0:
                self.level_verschiebung = 8
                spieler.geschw = 0
                self.wolken_verschiebung = self.level_verschiebung / 2

            elif spieler_x > (fenster_width - (fenster_width / 3)) and richtung_x > 0:
                self.level_verschiebung = -8
                spieler.geschw = 0
                self.wolken_verschiebung = self.level_verschiebung / 2

            else:
                self.level_verschiebung = 0
                spieler.geschw = 8
                self.wolken_verschiebung = self.level_verschiebung / 2

        # splash screen text vorlage
        def draw_text(self, text, size, color, x, y):
            schrift_font = py.font.Font(self.font_name, size)
            text_surface = schrift_font.render(text, True, color)
            text_rect = text_surface.get_rect()
            text_rect.midtop = (x, y)  # wird immer mittig platziert
            pyfenster.blit(text_surface, text_rect)

        # prüft ob der spieler "gewinnt" oder "verliert"
        def check_game_state(self):

            spieler = self.spieler.sprite

            # wenn der spieler das ziel berührt gewinnt er
            if py.sprite.spritecollide(self.spieler.sprite, self.ziel, False):
                pygame.mixer.fadeout(500)  # musik wird leiser
                self.time_stop = 1  # zeit zählen wird gestoppt
                keys = py.key.get_pressed()

                # bewegungsunfähigkeit des spielers sonst heraus laufen springen... aus dem ziel
                spieler.richtung.x = 0  # wenn die vektoren 0 sind kann er sich nicht mehr bewegen da die vektoren multipliziert werden
                spieler.richtung.y = 0  # "--"
                spieler.jump_geschw = 0  # "--"

                # schwärzen des fensters und zeichnen des textes
                pyfenster.fill("black")
                self.draw_text("Du hast: " + str(self.coins) + " Münzen gesammelt!", 48, "white", fenster_width / 2,
                               fenster_height * 1 / 4)
                self.draw_text("Level abgeschlossen! Das war SPITZE!", 48, "white", fenster_width / 2,
                               fenster_height / 2)
                self.draw_text("Drücke ESC zum speichern und verlassen!", 48, "white", fenster_width / 2,
                               fenster_height * 3 / 4)

                if keys[py.K_ESCAPE]:
                    py.quit()

            # spieler fällt aus der map herunter
            if spieler.rect.top > fenster_height:  # es wird die höhe genommen da in der oberen linken ecke gestartet wird mit dem fenster aufbau
                pygame.mixer.fadeout(500)  # musik wird leiser
                self.time_stop = 1  # zeit zählen wird gestoppt

                keys = py.key.get_pressed()

                # bewegungsunfähigkeit des spielers sonst herauslaufen springen... aus dem ziel
                spieler.richtung.x = 0
                spieler.richtung.y = 0
                spieler.jump_geschw = 0

                # schwärzen des fensters und zeichnen des textes
                pyfenster.fill("black")
                self.draw_text("Du bist leider gestorben :(", 48, "white", fenster_width / 2,
                               fenster_height * 1 / 4)
                self.draw_text("Versuch es doch noch einmal", 48, "white", fenster_width / 2,
                               fenster_height / 2)
                self.draw_text("Drücke ESC zum verlassen!", 48, "white", fenster_width / 2, fenster_height * 3 / 4)

                self.draw_text("Leertaste zum neustarten drücken!", 48, "white", fenster_width / 2,
                               fenster_height * 3.5 / 4)

                if keys[py.K_SPACE]:
                    py.quit()
                    Play()

        # prüft die kollision mit einer wand auf horiziontaler ebene
        def x_richtung_collision(self):

            spieler = self.spieler.sprite
            spieler.collision_rect.x += spieler.richtung.x * spieler.geschw

            for sprite in self.untergrund_ebene.sprites():
                if sprite.rect.colliderect(spieler.collision_rect):

                    # linke seite
                    if spieler.richtung.x < 0:
                        spieler.collision_rect.left = sprite.rect.right
                        spieler.touch_left = True
                        self.position_x = spieler.rect.left  # gibt an wo die colliosion geschieht

                    # rechte seite
                    elif spieler.richtung.x > 0:
                        spieler.collision_rect.right = sprite.rect.left
                        spieler.touch_right = True
                        self.position_x = spieler.rect.right  # guckt ob der spieler sich weiter drinne als der rand von dem block befindet

        # prüft die kollision mit einer wand auf vertikaler ebene
        def y_richtung_collsion(self):
            spieler = self.spieler.sprite

            # anwenden des immer währenden "fallens"
            spieler.gravity_movement()

            # spieler kollidiert mit einem block
            for sprite in self.untergrund_ebene.sprites():

                # prüft, wo es passiert oben oder unterhalb
                if sprite.rect.colliderect(spieler.collision_rect):
                    if spieler.richtung.y > 0:
                        spieler.collision_rect.bottom = sprite.rect.top
                        spieler.richtung.y = 0
                        spieler.touch_boden = True  # -> wird nicht durch den Block gezogen

                    elif spieler.richtung.y < 0:
                        spieler.collision_rect.top = sprite.rect.bottom
                        spieler.richtung.y = 0
                        spieler.touch_decke = True  # -> sprung wird nicht weiter ausgeführt

            # deaktivieren das durch den boden falles
            if spieler.touch_boden and spieler.richtung.y < 0 or spieler.richtung.y > 1:
                spieler.touch_boden = False

        # errechnen eines einfachen highscores
        def calculating_highscore(self):
            self.score = self.coins * 100 + self.time_left * 50

        # führt die ganzen verschieben und zeichen programme aus
        def run(self):

            # non block-typ
            self.himmel.draw(self.draw_ebene)
            self.wolken.draw(self.draw_ebene, self.wolken_verschiebung)
            self.wasser.draw(self.draw_ebene, self.level_verschiebung)

            # blöcke
            self.untergrund_ebene.update(self.level_verschiebung)
            self.untergrund_ebene.draw(self.draw_ebene)

            self.decoration_ebene.update(self.level_verschiebung)
            self.decoration_ebene.draw(self.draw_ebene)

            # je nach level wieder einige spezial blöcke
            if not clicked_level == "World 1 - 3" and not clicked_level == "World 1 - 4" and not clicked_level == "World 1 - 8":
                self.busch_ebene.update(self.level_verschiebung)
                self.busch_ebene.draw(self.draw_ebene)

                if not clicked_level == "World 1 - 5" and not clicked_level == "World 1 - 6":
                    self.pilze_ebene.update(self.level_verschiebung)
                    self.pilze_ebene.draw(self.draw_ebene)

            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4" or clicked_level == "World 1 - 8":
                self.geschenk_ebene.update(self.level_verschiebung)
                self.geschenk_ebene.draw(self.draw_ebene)

            if clicked_level == "World 1 - 5" or clicked_level == "World 1 - 6":
                self.busch_2_ebene.update(self.level_verschiebung)
                self.busch_2_ebene.draw(self.draw_ebene)

                self.ranken_ebene.update(self.level_verschiebung)
                self.ranken_ebene.draw(self.draw_ebene)

            self.bereich_ebene.update(self.level_verschiebung)
            self.bereich_ebene.draw(self.draw_ebene)

            if not clicked_level == "World 1 - 5" and not clicked_level == "World 1 - 6" and not clicked_level == "World 1 - 7":
                self.blumen_ebene.update(self.level_verschiebung)
                self.blumen_ebene.draw(self.draw_ebene)

            self.baum_ebene.update(self.level_verschiebung)
            self.baum_ebene.draw(self.draw_ebene)

            self.coin_ebene.update(self.level_verschiebung)
            self.coin_ebene.draw(self.draw_ebene)

            self.ziel.update(self.level_verschiebung)
            self.ziel.draw(self.draw_ebene)

            # spieler relevantes
            self.spieler.update()
            self.spieler.draw(self.draw_ebene)
            self.check_coin_collisions()
            self.ui.show_spielername()
            self.ui.show_coins(self.coins)
            self.check_time()
            self.ui.timer(self.time_left_string)
            self.calculating_highscore()
            self.check_game_state()
            self.x_richtung_collision()
            self.y_richtung_collsion()
            self.bewegung_x()

    # interface im level
    class GUI:
        def __init__(self, ebene):

            # spielfenster
            self.draw_ebene = ebene  # -> pyfenster

            # gui zusätze
            self.font = pygame.font.SysFont("Helvetica", 23, bold=True, italic=False)
            self.coin = py.image.load("assets/blocks/coins/1.png")
            self.coin_rect = self.coin.get_rect(topleft=(10, 25))  # position des münzen icon

        # münzen
        def show_coins(self, menge):

            self.draw_ebene.blit(self.coin, self.coin_rect)

            # falls im winter gespielt wird weiße schrift
            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4":
                coin_menge_ebene = self.font.render(str(menge), False, "white")
            else:
                coin_menge_ebene = self.font.render(str(menge), False, "black")

            coin_menge_border = coin_menge_ebene.get_rect(midleft=(self.coin_rect.right + 4, self.coin_rect.centery))
            self.draw_ebene.blit(coin_menge_ebene, coin_menge_border)

        # spielername
        def show_spielername(self):

            # falls kein name in das eingabe feld eingetragen wird Player als Standart gesetzt
            if not entry_get:
                spielername = "Player"
            else:
                spielername = entry_get

            # falls im winter gespielt wird weiße schrift
            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4":
                text_surface = self.font.render(spielername, True, "white")
            else:
                text_surface = self.font.render(spielername, True, "black")

            text_border = text_surface.get_rect()
            text_border.topleft = (15, 10)  # -> position des spielernamens
            pyfenster.blit(text_surface, text_border)

        # zeit
        def timer(self, time_left_string):

            # falls im winter gespielt wird weiße schrift
            if clicked_level == "World 1 - 3" or clicked_level == "World 1 - 4":
                time_ebene = self.font.render(time_left_string, False, "white")
            else:
                time_ebene = self.font.render(time_left_string, False, "black")

            time_border = time_ebene.get_rect()
            time_border.topleft = (885, 40)  # -> position der übrigen zeit
            pyfenster.blit(time_ebene, time_border)

    # definieren einiger datei übergreifend gebrauchter variablen
    block_size = 48
    vertical_blocks = 17

    # importiert alles in einem Ordner
    def import_ordner(path):
        ebenen_liste = []

        # "macht eine liste aus dem ordner"
        for _, _, bild_datei in walk(path):
            for bild in bild_datei:
                full_path = path + "/" + bild  # -> bild pfad wird vom system durch laufen nicht von der funktion -> nicht nur für einen ordner nutzbar
                bild_surf = py.image.load(
                    full_path).convert_alpha()  # ->.convert_alpha() sorgt für die durchsichtigen flächen sonst entstehen schwarze bereiche
                ebenen_liste.append(bild_surf)
        return ebenen_liste

    # csv-datein = comma seperated value sind datein mit langen strings die aus zahlen getrennt mit kommas bestehen
    # für jede zahl kann je nach programm interpretation etwas geschehen
    # hier werden die verschiedenen blockteile "geladen"
    # für eine -1 geschieht nix
    # für eine 0 z.b. das erste, was in der oberen linken ecke des bildes das gerade genutzt wird
    # dies wird dann in eine liste kopiert
    def import_csv_datei(path):
        untergrund_map = []

        with open(path) as level_daten:
            level = reader(level_daten, delimiter=",")  # delimiter = unterbrecher
            for reihe in level:
                untergrund_map.append(list(reihe))
            return untergrund_map

    # "teilen" der grafiken
    # für die grafiken (bilder) die z.b. für die blöcke werden zahlen für bereiche festgelegt
    # diese kann vom csv programm verarbeitet werden
    def grafiken_teilen(path):
        # pfad übergabe
        surface = py.image.load(path).convert_alpha()

        block_menge_x = int(surface.get_size()[0] / block_size)  # zeilen
        block_menge_y = int(surface.get_size()[1] / block_size)  # spalten

        block_teile = []

        for reihe in range(block_menge_y):
            for spalte in range(block_menge_x):
                x = spalte * block_size
                y = reihe * block_size
                neu_surf = py.Surface((block_size, block_size), flags=py.SRCALPHA)
                neu_surf.blit(surface, (0, 0), py.Rect(x, y, block_size, block_size))
                block_teile.append(neu_surf)

        return block_teile

    # ermitteln des ausgewählten levels
    clicked_level = "World 1 - 1"  #clicked.get()

    # ermitteln der eingabe werte für spielernamen
    entry_get = "Marius"  #eingabe_feld.get()

    # bestimmen des levels durch das ausgewählte feld im hauptmenu
    # danach auswählen der gebrauchten csv-datein

    # level 1
    if clicked_level == "World 1 - 1":
        level_map = {"untergrund": "assets/level_data/Level_1/level_1_overworld_erde.csv",
                     "coins": "assets/level_data/Level_1/level_1_overworld_coins.csv",
                     "ziel": "assets/level_data/Level_1/level_1_overworld_ziel.csv",
                     "spieler": "assets/level_data/Level_1/level_1_overworld_spieler.csv",
                     "dekorationen": "assets/level_data/Level_1/level_1_overworld_zaun.csv",
                     "pilze": "assets/level_data/Level_1/level_1_overworld_pilze.csv",
                     "baum": "assets/level_data/Level_1/level_1_overworld_bäume.csv",
                     "blumen": "assets/level_data/Level_1/level_1_overworld_blumen.csv",
                     "busch": "assets/level_data/Level_1/level_1_overworld_busch.csv"
                     }

    # level 2
    elif clicked_level == "World 1 - 2":
        level_map = {"untergrund": "assets/level_data/Level_2/level_2_overworld_erde.csv",
                     "baum": "assets/level_data/Level_2/level_2_overworld_bäume.csv",
                     "coins": "assets/level_data/Level_2/level_2_overworld_coins.csv",
                     "spieler": "assets/level_data/Level_2/level_2_overworld_spieler.csv",
                     "dekorationen": "assets/level_data/Level_2/level_2_overworld_zaun.csv",
                     "busch": "assets/level_data/Level_2/level_2_overworld_busch.csv",
                     "ziel": "assets/level_data/Level_2/level_2_overworld_ziel.csv",
                     "blumen": "assets/level_data/Level_2/level_2_overworld_blumen.csv",
                     "pilze": "assets/level_data/Level_2/level_2_overworld_pilze.csv",
                     }

    # level 3
    elif clicked_level == "World 1 - 3":
        level_map = {"untergrund": "assets/level_data/Level_3/level_3_snow_schnee.csv",
                     "baum": "assets/level_data/Level_3/level_3_snow_bäume.csv",
                     "coins": "assets/level_data/Level_3/level_3_snow_coins.csv",
                     "spieler": "assets/level_data/Level_3/level_3_snow_spieler.csv",
                     "dekorationen": "assets/level_data/Level_3/level_3_snow_zaun.csv",
                     "ziel": "assets/level_data/Level_3/level_3_snow_ziel.csv",
                     "blumen": "assets/level_data/Level_3/level_3_snow_blumen.csv",
                     "geschenk": "assets/level_data/Level_3/level_3_snow_geschenk.csv",
                     }

    # level 4
    elif clicked_level == "World 1 - 4":
        level_map = {"untergrund": "assets/level_data/Level_4/level_4_snow_schnee.csv",
                     "baum": "assets/level_data/Level_4/level_4_snow_bäume.csv",
                     "coins": "assets/level_data/Level_4/level_4_snow_coins.csv",
                     "spieler": "assets/level_data/Level_4/level_4_snow_spieler.csv",
                     "dekorationen": "assets/level_data/Level_4/level_4_snow_zaun.csv",
                     "ziel": "assets/level_data/Level_4/level_4_snow_ziel.csv",
                     "blumen": "assets/level_data/Level_4/level_4_snow_blumen.csv",
                     "geschenk": "assets/level_data/Level_4/level_4_snow_geschenk.csv"
                     }

    # level 5
    elif clicked_level == "World 1 - 5":
        level_map = {"untergrund": "assets/level_data/Level_5/level_5_jungle_jungle.csv",
                     "baum": "assets/level_data/Level_5/level_5_jungle_baum.csv",
                     "coins": "assets/level_data/Level_5/level_5_jungle_coins.csv",
                     "spieler": "assets/level_data/Level_5/level_5_jungle_spieler.csv",
                     "dekorationen": "assets/level_data/Level_5/level_5_jungle_zaun.csv",
                     "ziel": "assets/level_data/Level_5/level_5_jungle_ziel.csv",
                     "busch": "assets/level_data/Level_5/level_5_jungle_busch.csv",
                     "busch_2": "assets/level_data/Level_5/level_5_jungle_busch_2.csv",
                     "ranken": "assets/level_data/Level_5/level_5_jungle_ranken.csv"
                     }

    # level 6
    elif clicked_level == "World 1 - 6":
        level_map = {"untergrund": "assets/level_data/Level_6/level_6_jungle_jungle.csv",
                     "baum": "assets/level_data/Level_6/level_6_jungle_baum.csv",
                     "coins": "assets/level_data/Level_6/level_6_jungle_coins.csv",
                     "spieler": "assets/level_data/Level_6/level_6_jungle_spieler.csv",
                     "dekorationen": "assets/level_data/Level_6/level_6_jungle_zaun.csv",
                     "ziel": "assets/level_data/Level_6/level_6_jungle_ziel.csv",
                     "busch": "assets/level_data/Level_6/level_6_jungle_busch.csv",
                     "busch_2": "assets/level_data/Level_6/level_6_jungle_busch_2.csv",
                     "ranken": "assets/level_data/Level_6/level_6_jungle_ranken.csv"
                     }

    # level 7
    elif clicked_level == "World 1 - 7":
        level_map = {"untergrund": "assets/level_data/Level_7/level_7_erde_erde.csv",
                     "baum": "assets/level_data/Level_7/level_7_erde_baum.csv",
                     "coins": "assets/level_data/Level_7/level_7_erde_coins.csv",
                     "spieler": "assets/level_data/Level_7/level_7_erde_spieler.csv",
                     "dekorationen": "assets/level_data/Level_7/level_7_erde_zaun.csv",
                     "ziel": "assets/level_data/Level_7/level_7_erde_ziel.csv",
                     "busch": "assets/level_data/Level_7/level_7_erde_busch.csv",
                     "pilze": "assets/level_data/Level_7/level_7_erde_pilze.csv",
                     }

    # level 8
    elif clicked_level == "World 1 - 8":
        level_map = {"untergrund": "assets/level_data/Level_8/level_8_schnee_schnee.csv",
                     "baum": "assets/level_data/Level_8/level_8_schnee_bäume.csv",
                     "coins": "assets/level_data/Level_8/level_8_schnee_coins.csv",
                     "spieler": "assets/level_data/Level_8/level_8_schnee_spieler.csv",
                     "dekorationen": "assets/level_data/Level_8/level_8_schnee_zaun.csv",
                     "ziel": "assets/level_data/Level_8/level_8_schnee_ziel.csv",
                     "blumen": "assets/level_data/Level_8/level_8_schnee_blumen.csv",
                     "geschenk": "assets/level_data/Level_8/level_8_schnee_geschenk.csv"
                     }

    # pygame initialisieren
    py.init()

    # fenster attribute
    fenster_width = 960
    fenster_height = 720
    pyfenster = py.display.set_mode((fenster_width, fenster_height))  # py.FULLSCREEN
    py.display.set_caption("Marius Brothers™")
    clock = py.time.Clock()
    fps = 60

    game = Level(level_map, pyfenster)

    game_state = True
    # fenster loop
    while game_state:
        clock.tick(fps)  # aktualisierungsrate des fensters
        for event in py.event.get():
            if event.type == py.QUIT:
                game_state = False
                py.quit()
        game.run()  # -> immer wieder neu laden aller sprites und interface teile daher das eigentliche bewegen
        py.display.update()

intro()
