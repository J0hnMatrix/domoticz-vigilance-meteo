# Météo France Vigilance & Forecast Domoticz Python Plugin
#
# Author: Antigravity
#
# Description:
#   Queries the Météo France private mobile API to retrieve:
#   1. Weather vigilance alerts (today and tomorrow)
#   2. Current temperature and humidity (Temp+Hum sensor)
#   3. Weather forecast description and min/max temperatures (Text sensor)
#   4. Rain forecast in the next hour (Alert sensor)
#
#   Supports cities, postal codes, and department numbers with auto-resolution.
#   Devices are named after the resolved city and department.
#   Does not require any personal API key.
#
"""
<plugin key="MeteoFranceVigilance" name="Vigilance Météo France" author="Antigravity" version="1.4.2" wikilink="https://github.com/J0hnMatrix/domoticz-vigilance-meteo">
    <description>
        Plugin Météo France &amp; Vigilance (Sans clé requise)

        Ce plugin récupère les prévisions et alertes de Météo France pour votre ville :
        - Vigilance d'aujourd'hui et de demain (Tuiles d'Alerte)
        - Température et humidité actuelles (Tuile Temp+Hum)
        - Description des prévisions quotidiennes (Tuile de Texte)
        - Prévisions de pluie dans l'heure (Tuile d'Alerte)

        Aucune inscription ni clé API personnelle n'est requise ! Renseignez simplement votre ville ou code postal.
    </description>
    <params>
        <param field="Mode1" label="Localisation (Ville, Code Postal ou Dept)" width="200px" required="true" default="75001"/>
        <param field="Mode2" label="Intervalle de mise à jour (min)" width="60px" required="true" default="30"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="Non" value="False" default="true" />
                <option label="Oui" value="True" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import urllib.request
import urllib.error
import urllib.parse
import json
import time
from datetime import datetime, timedelta

# Constantes Météo France
DEFAULT_PRIVATE_TOKEN = "__Wj7dVSTjV9YGu1guveLyDq0g7S7TfTjaHBTPTpO0kj8__"

COLOR_NAMES = {
    1: "Vert",
    2: "Jaune",
    3: "Orange",
    4: "Rouge"
}

COLOR_LEVELS = {
    1: "Pas de vigilance particulière",
    2: "Vigilance Jaune",
    3: "Vigilance Orange",
    4: "Vigilance Rouge"
}

PHENOMENON_NAMES = {
    1: "Vent violent",
    2: "Pluie-inondation",
    3: "Orages",
    4: "Crues",
    5: "Neige-verglas",
    6: "Canicule",
    7: "Grand froid",
    8: "Avalanches",
    9: "Vagues-submersion"
}

# Dictionnaire des départements français
DEPT_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence", "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes", "09": "Ariège", "10": "Aube",
    "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal",
    "16": "Charente", "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère",
    "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde", "34": "Hérault",
    "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire", "38": "Isère", "39": "Jura",
    "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique",
    "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire",
    "50": "Manche", "51": "Marne", "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle",
    "55": "Meuse", "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord",
    "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône",
    "70": "Haute-Saône", "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie",
    "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres",
    "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse",
    "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne",
    "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise", "971": "Guadeloupe", "972": "Martinique",
    "973": "Guyane", "974": "La Réunion", "976": "Mayotte"
}

class BasePlugin:
    enabled = False
    
    def __init__(self):
        self.runInterval = 30 * 6  # 30 minutes par défaut (6 * 10 secondes = 1 minute)
        self.heartbeatCounter = 0
        self.apiToken = DEFAULT_PRIVATE_TOKEN
        self.debug = False
        
        # Localisation résolue
        self.placeResolved = False
        self.locationQuery = "75001"
        self.lat = 48.8592
        self.lon = 2.3417
        self.department = "75"
        self.placeName = "Paris"
        self.deptName = "Paris"
        return

    def onStart(self):
        # Configuration du Debugging Domoticz
        if Parameters["Mode6"] == "True":
            Domoticz.Debugging(1)
            self.debug = True
            Domoticz.Debug("Mode debug activé")
        else:
            Domoticz.Debugging(0)
            self.debug = False

        Domoticz.Log("Démarrage du plugin Météo France (Version sans clé)...")

        # Jeton d'accès privé (toujours celui par défaut)
        self.apiToken = DEFAULT_PRIVATE_TOKEN
            
        # Enregistrer la requête de localisation brute (Mode1)
        self.locationQuery = Parameters["Mode1"].strip()
        
        # Résolution de la localisation immédiatement à l'initialisation
        place = self.searchPlace(self.locationQuery)
        if place:
            self.lat = place.get('lat', 48.8592)
            self.lon = place.get('lon', 2.3417)
            self.department = self.normalizeDept(place.get('admin2', '75'))
            self.placeName = place.get('name', 'Paris')
            self.deptName = DEPT_NAMES.get(self.department, f"Département {self.department}")
            self.placeResolved = True
        else:
            Domoticz.Error("Échec de la résolution de localisation au démarrage. Position par défaut fixée sur Paris.")
            self.lat = 48.8592
            self.lon = 2.3417
            self.department = "75"
            self.placeName = "Paris"
            self.deptName = "Paris"
            self.placeResolved = True # Évite de bloquer
            
        # Calculer le nombre de cycles onHeartbeat (Mode2)
        try:
            minutes = int(Parameters["Mode2"])
            if minutes < 15:
                Domoticz.Error("L'intervalle de rafraîchissement ne peut pas être inférieur à 15 minutes. Configuration fixée à 15 minutes.")
                minutes = 15
        except ValueError:
            minutes = 30
            
        self.runInterval = minutes * 6
        
        # Forcer une récupération immédiate des données au démarrage
        self.heartbeatCounter = self.runInterval

        # Création des dispositifs s'ils n'existent pas avec les noms résolus
        # Unit 1 : Vigilance Aujourd'hui
        # Unit 2 : Vigilance Demain
        # Unit 3 : Météo Temp+Hum
        # Unit 4 : Prévisions
        # Unit 5 : Pluie dans l'heure
        if len(Devices) == 0:
            Domoticz.Device(Name=f"{self.deptName} - Vigilance Aujourd'hui", Unit=1, TypeName="Alert", Used=1).Create()
            Domoticz.Device(Name=f"{self.deptName} - Vigilance Demain", Unit=2, TypeName="Alert", Used=1).Create()
            Domoticz.Device(Name=f"{self.placeName} - Météo Temp+Hum", Unit=3, TypeName="Temp+Hum", Used=1).Create()
            Domoticz.Device(Name=f"{self.placeName} - Prévisions météo", Unit=4, TypeName="Text", Used=1).Create()
            Domoticz.Device(Name=f"{self.placeName} - Pluie dans l'heure", Unit=5, TypeName="Alert", Used=1).Create()
            Domoticz.Log("Création initiale de tous les dispositifs effectuée.")
        else:
            if 1 not in Devices:
                Domoticz.Device(Name=f"{self.deptName} - Vigilance Aujourd'hui", Unit=1, TypeName="Alert", Used=1).Create()
            if 2 not in Devices:
                Domoticz.Device(Name=f"{self.deptName} - Vigilance Demain", Unit=2, TypeName="Alert", Used=1).Create()
            if 3 not in Devices:
                Domoticz.Device(Name=f"{self.placeName} - Météo Temp+Hum", Unit=3, TypeName="Temp+Hum", Used=1).Create()
            if 4 not in Devices:
                Domoticz.Device(Name=f"{self.placeName} - Prévisions météo", Unit=4, TypeName="Text", Used=1).Create()
            if 5 not in Devices:
                Domoticz.Device(Name=f"{self.placeName} - Pluie dans l'heure", Unit=5, TypeName="Alert", Used=1).Create()

        Domoticz.Log(f"Plugin configuré pour '{self.placeName}' ({self.deptName}). Rafraîchissement toutes les {minutes} minutes.")

    def onStop(self):
        Domoticz.Log("Arrêt du plugin Météo France...")

    def onConnect(self, Connection, Status, Description):
        pass

    def onMessage(self, Connection, Data):
        pass

    def onCommand(self, Unit, Command, Level, Hue):
        pass

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        pass

    def onDisconnect(self, Connection):
        pass

    def onHeartbeat(self):
        self.heartbeatCounter += 1
        if self.heartbeatCounter >= self.runInterval:
            self.heartbeatCounter = 0
            self.fetchWeatherData()

    def normalizeDept(self, dept):
        dept = str(dept).strip()
        if len(dept) == 1 and dept.isdigit():
            return f"0{dept}"
        return dept

    def getSearchQuery(self, userInput):
        val = userInput.strip().upper()
        if val == "75":
            return "75001"
        elif val in ["2A", "2A0"]:
            return "Ajaccio"
        elif val in ["2B", "2B0"]:
            return "Bastia"
        elif val == "974":
            return "Saint-Denis, Réunion"
        elif val == "971":
            return "Pointe-à-Pitre"
        elif val == "972":
            return "Fort-de-France"
        elif val == "973":
            return "Cayenne"
        elif val == "976":
            return "Mamoudzou"
        elif len(val) <= 2 and val.isdigit():
            if len(val) == 1:
                return f"0{val}000"
            else:
                return f"{val}000"
        return val

    def searchPlace(self, query):
        search_term = self.getSearchQuery(query)
        Domoticz.Log(f"Résolution de la localisation pour '{query}' (recherche: '{search_term}')...")
        
        q_quoted = urllib.parse.quote(search_term)
        url = f"https://webservice.meteofrance.com/places?q={q_quoted}&token={self.apiToken}"
        
        req = urllib.request.Request(
            url,
            headers={
                "accept": "application/json",
                "User-Agent": "Domoticz-Vigilance-Plugin/1.4"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                results = json.loads(response.read().decode('utf-8'))
                if results and len(results) > 0:
                    place = results[0]
                    Domoticz.Log(f"Localisation résolue : {place.get('name')} (Dept: {place.get('admin2')}, Lat: {place.get('lat')}, Lon: {place.get('lon')})")
                    return place
                else:
                    Domoticz.Error(f"Aucun lieu trouvé pour la recherche '{search_term}'.")
        except Exception as e:
            Domoticz.Error(f"Erreur lors de la recherche de lieu : {str(e)}")
        return None

    def fetchWeatherData(self):
        # S'assurer que le lieu est résolu (fallback si échec au démarrage)
        if not self.placeResolved:
            place = self.searchPlace(self.locationQuery)
            if place:
                self.lat = place.get('lat')
                self.lon = place.get('lon')
                self.department = self.normalizeDept(place.get('admin2'))
                self.placeName = place.get('name', 'Paris')
                self.deptName = DEPT_NAMES.get(self.department, f"Département {self.department}")
                self.placeResolved = True
            else:
                Domoticz.Error("Échec de la résolution de localisation. Position par défaut fixée sur Paris.")
                self.lat = 48.8592
                self.lon = 2.3417
                self.department = "75"
                self.placeName = "Paris"
                self.deptName = "Paris"
                self.placeResolved = True

        self.fetchVigilance()
        self.fetchForecast()
        self.fetchRain()

    def fetchVigilance(self):
        # 1. Requête pour Aujourd'hui (J0)
        url_j0 = f"https://webservice.meteofrance.com/v3/warning/full?domain={self.department}&token={self.apiToken}&echeance=J0"
        req_j0 = urllib.request.Request(url_j0, headers={"accept": "application/json", "User-Agent": "Domoticz-Vigilance-Plugin/1.4"})
        
        data_j0 = None
        data_j1 = None

        # Récupérer J0
        try:
            with urllib.request.urlopen(req_j0, timeout=10) as response:
                data_j0 = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            Domoticz.Error(f"Erreur lors de la récupération de la vigilance J0 : {str(e)}")
            self.updateVigilanceToError(str(e))
            return

        # 2. Requête pour Demain (J1)
        url_j1 = f"https://webservice.meteofrance.com/v3/warning/full?domain={self.department}&token={self.apiToken}&echeance=J1"
        req_j1 = urllib.request.Request(url_j1, headers={"accept": "application/json", "User-Agent": "Domoticz-Vigilance-Plugin/1.4"})
        
        try:
            with urllib.request.urlopen(req_j1, timeout=10) as response:
                data_j1 = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            Domoticz.Log(f"Vigilance J1 non disponible ou erreur : {str(e)}")
            
        self.parseVigilance(data_j0, data_j1)

    def parseVigilance(self, data_j0, data_j1):
        # Aujourd'hui (J0)
        today_max_color = int(data_j0.get("color_max", 1))
        today_warnings = []
        for item in data_j0.get("phenomenons_items", []):
            p_id = int(item["phenomenon_id"])
            p_color = int(item["phenomenon_max_color_id"])
            if p_color > 1:
                today_warnings.append((p_id, PHENOMENON_NAMES.get(p_id, f"Risque {p_id}"), p_color, COLOR_NAMES.get(p_color, "Inconnu")))
        today_warnings.sort(key=lambda x: (-x[2], x[0]))
        
        if today_max_color == 1:
            today_text = "Vert : Pas de vigilance particulière"
        else:
            warnings_str = ", ".join([f"{w[1]} ({w[3]})" for w in today_warnings])
            today_text = f"{COLOR_NAMES.get(today_max_color, 'Jaune')} : {warnings_str}"

        # Demain (J1)
        if data_j1 is not None and "color_max" in data_j1:
            tomorrow_max_color = int(data_j1.get("color_max", 1))
            tomorrow_warnings = []
            for item in data_j1.get("phenomenons_items", []):
                p_id = int(item["phenomenon_id"])
                p_color = int(item["phenomenon_max_color_id"])
                if p_color > 1:
                    tomorrow_warnings.append((p_id, PHENOMENON_NAMES.get(p_id, f"Risque {p_id}"), p_color, COLOR_NAMES.get(p_color, "Inconnu")))
            tomorrow_warnings.sort(key=lambda x: (-x[2], x[0]))

            if tomorrow_max_color == 1:
                tomorrow_text = "Vert : Pas de vigilance particulière"
            else:
                warnings_str = ", ".join([f"{w[1]} ({w[3]})" for w in tomorrow_warnings])
                tomorrow_text = f"{COLOR_NAMES.get(tomorrow_max_color, 'Jaune')} : {warnings_str}"
        else:
            tomorrow_max_color = 1
            tomorrow_text = "Vert : Pas de vigilance ou données non encore publiées"

        # Mise à jour Domoticz
        Devices[1].Update(nValue=today_max_color, sValue=today_text)
        Devices[2].Update(nValue=tomorrow_max_color, sValue=tomorrow_text)

    def updateVigilanceToError(self, error_message):
        if 1 in Devices:
            Devices[1].Update(nValue=0, sValue=f"Erreur Vigilance : {error_message}")
        if 2 in Devices:
            Devices[2].Update(nValue=0, sValue=f"Erreur Vigilance : {error_message}")

    def fetchForecast(self):
        url = f"https://webservice.meteofrance.com/forecast?lat={self.lat}&lon={self.lon}&lang=fr&token={self.apiToken}"
        req = urllib.request.Request(url, headers={"accept": "application/json", "User-Agent": "Domoticz-Vigilance-Plugin/1.4"})
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.parseForecast(data)
        except Exception as e:
            Domoticz.Error(f"Erreur lors de la récupération des prévisions météo : {str(e)}")
            if 3 in Devices:
                Devices[3].Update(nValue=0, sValue="0.0;0;0")
            if 4 in Devices:
                Devices[4].Update(nValue=0, sValue=f"Erreur Prévisions : {str(e)}")

    def parseForecast(self, data):
        # 1. Température et Humidité actuelles (forecast[0])
        try:
            curr_fore = data['forecast'][0]
            temp = float(curr_fore['T']['value'])
            humidity = int(curr_fore['humidity'])
            
            # Comfort level : 0=Normal, 1=Comfortable, 2=Dry, 3=Wet
            if humidity < 30:
                hum_stat = 2
            elif humidity > 70:
                hum_stat = 3
            elif humidity >= 45 and humidity <= 70:
                hum_stat = 1
            else:
                hum_stat = 0
                
            Devices[3].Update(nValue=0, sValue=f"{temp};{humidity};{hum_stat}")
            if self.debug:
                Domoticz.Debug(f"Mise à jour Temp+Hum : Temp={temp}°C, Hum={humidity}%, Stat={hum_stat}")
        except Exception as e:
            Domoticz.Error(f"Erreur lors du traitement Temp+Hum : {str(e)}")

        # 2. Description de la prévision quotidienne
        try:
            curr_desc = data['forecast'][0]['weather']['desc']
            daily_fore = data['daily_forecast'][0]
            t_min = daily_fore['T']['min']
            t_max = daily_fore['T']['max']
            daily_desc = daily_fore['weather12H']['desc']
            s_val = f"{daily_desc} (Min: {t_min}°C, Max: {t_max}°C)"
        except Exception:
            try:
                s_val = f"{curr_desc}"
            except Exception:
                s_val = "Prévisions indisponibles"
                
        if 4 in Devices:
            Devices[4].Update(nValue=0, sValue=s_val)

    def fetchRain(self):
        url = f"https://webservice.meteofrance.com/rain?lat={self.lat}&lon={self.lon}&lang=fr&token={self.apiToken}"
        req = urllib.request.Request(url, headers={"accept": "application/json", "User-Agent": "Domoticz-Vigilance-Plugin/1.4"})
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.parseRain(data)
        except Exception as e:
            Domoticz.Error(f"Erreur lors de la récupération des prévisions de pluie : {str(e)}")
            if 5 in Devices:
                Devices[5].Update(nValue=0, sValue=f"Erreur Pluie : {str(e)}")

    def parseRain(self, data):
        if 5 not in Devices:
            return
            
        position = data.get('position', {})
        rain_avail = position.get('rain_product_available', 0)
        
        if rain_avail == 1:
            rain_max_level = 1
            rain_timeline = []
            
            for item in data.get('forecast', []):
                dt_str = time.strftime('%H:%M', time.localtime(item['dt']))
                level = int(item['rain'])
                desc = item['desc']
                
                rain_max_level = max(rain_max_level, level)
                if level > 1:
                    rain_timeline.append(f"{desc} à {dt_str}")
            
            # Formater le statut textuel
            if rain_max_level == 1:
                rain_text = "Temps sec prévu dans l'heure"
            else:
                rain_text = ", ".join(rain_timeline)
                
            Devices[5].Update(nValue=rain_max_level, sValue=rain_text)
            if self.debug:
                Domoticz.Debug(f"Mise à jour Pluie : nValue={rain_max_level}, sValue='{rain_text}'")
        else:
            Devices[5].Update(nValue=0, sValue="Indisponible pour cette localisation")


# Initialisation globale requise par le moteur de plugins Domoticz
globalActivePlugin = None

def onStart():
    global globalActivePlugin
    if globalActivePlugin is None:
        globalActivePlugin = BasePlugin()
    globalActivePlugin.onStart()

def onStop():
    global globalActivePlugin
    if globalActivePlugin is not None:
        globalActivePlugin.onStop()

def onConnect(Connection, Status, Description):
    global globalActivePlugin
    if globalActivePlugin is not None:
        globalActivePlugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global globalActivePlugin
    if globalActivePlugin is not None:
        globalActivePlugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global globalActivePlugin
    if globalActivePlugin is not None:
        globalActivePlugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global globalActivePlugin
    if globalActivePlugin is not None:
        globalActivePlugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global globalActivePlugin
    if globalActivePlugin is not None:
        globalActivePlugin.onDisconnect(Connection)

def onHeartbeat():
    global globalActivePlugin
    if globalActivePlugin is not None:
        globalActivePlugin.onHeartbeat()
