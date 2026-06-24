# 🌦️ Plugin Météo France & Vigilance pour Domoticz (Sans Clé API)

Ce plugin Python pour [Domoticz](https://www.domoticz.com/) permet de récupérer et d'afficher en temps réel les données de **Météo France** (vigilance météo nationale/départementale, prévisions horaires/quotidiennes de température et humidité, prévisions de pluie dans l'heure) pour votre localisation, **sans nécessiter aucune clé API personnelle**.

Il utilise l'API privée (non publique) de l'application mobile Météo France, offrant ainsi une intégration stable et sans contraintes de création de compte.

---

## ✨ Fonctionnalités

Le plugin crée automatiquement **5 dispositifs** sur votre tableau de bord Domoticz, nommés dynamiquement avec le nom de la ville ou du département résolu :

1. ⚠️ **{Département} - Vigilance Aujourd'hui** (Type : *Alerte*) :
   * Niveau de vigilance global pour la journée en cours (Vert, Jaune, Orange, Rouge).
   * Description des phénomènes en cours (ex. *Vent violent (Jaune), Orages (Orange)*).
2. ⚠️ **{Département} - Vigilance Demain** (Type : *Alerte*) :
   * Niveau de vigilance prévu pour le lendemain.
   * Reconstitution chronologique basée sur l'analyse de la timeline de vigilance (les données J+1 étant extraites précisément sur le créneau 00:00 - 23:59 local).
3. 🌡️ **{Ville} - Météo Temp+Hum** (Type : *Temp+Hum*) :
   * Température actuelle en °C.
   * Humidité relative en %.
   * Statut de confort calculé automatiquement (*Normal, Confortable, Sec, Humide*).
4. 📝 **{Ville} - Prévisions météo** (Type : *Texte*) :
   * Description textuelle de la météo prévue pour la journée et températures minimale/maximale (ex. *Averses de pluie (Min: 14°C, Max: 21°C)*).
5. ☔ **{Ville} - Pluie dans l'heure** (Type : *Alerte*) :
   * Indication en temps réel de l'arrivée de la pluie dans les 60 prochaines minutes.
   * Couleur dynamique : Vert (Sec), Jaune (Pluie faible), Orange (Pluie modérée), Rouge (Pluie forte).
   * Affiche la chronologie précise (ex. *Pluie faible à 14h15, Pluie modérée à 14h30*).
   * Affiche *Indisponible pour cette localisation* si la zone n'est pas couverte par le radar de pluie (ex. Outre-Mer).

---

## 🛠️ Fonctionnement Interne (Comment ça marche ?)

* **Pas de clé API requise** : Le plugin s'appuie sur le point d'accès privé de Météo France (`webservice.meteofrance.com`) avec un jeton applicatif partagé et intégré.
* **Résolution de localisation intelligente** :
  * Si vous saisissez un **code postal** (ex: `18000`) ou une **ville** (ex: `Bourges`), le plugin interroge le service de géocodage de Météo France au démarrage pour en déduire les coordonnées GPS (Latitude/Longitude) et le département.
  * Si vous saisissez un **département** (ex: `13` ou `2A`), le plugin applique un fallback sur le chef-lieu (ex: Marseille pour le 13) pour localiser les coordonnées géographiques et lier le département de vigilance.
  * Supporte les départements d'Outre-mer (Guadeloupe, Martinique, Guyane, La Réunion, Mayotte).
* **Analyse de la Vigilance J+1** : L'API privée renvoie les alertes sous forme de flux chronologique continu (*timelaps*). Le plugin filtre ces fenêtres temporelles pour reconstituer fidèlement le niveau maximal d'alerte pour le lendemain.

---

## ⚙️ Installation

1. Accédez au répertoire de votre serveur Domoticz.
2. Allez dans le dossier `plugins/`.
3. Tapez les commandes :
   ```bash
   git clone https://github.com/J0hnMatrix/domoticz-vigilance-meteo
   ```
4. Redémarrez Domoticz :
   ```bash
   sudo systemctl restart domoticz
   ```
   ou redémarrez votre conteneur Domoticz
   
---

## 🔧 Configuration dans Domoticz

1. Connectez-vous à l'interface de Domoticz.
2. Allez dans **Configuration > Matériel**.
3. Dans la liste déroulante **Type**, sélectionnez **Vigilance Météo France**.
4. Renseignez les paramètres suivants :
   * **Nom** : Le nom de votre choix (ex: `Météo France`).
   * **Localisation** : Votre ville (ex: `Bourges`), votre code postal (ex: `18000`), ou votre département (ex: `18`).
   * **Intervalle de rafraîchissement (min)** : Fréquence de mise à jour en minutes (30 par défaut, minimum 15 recommandé pour éviter de surcharger les serveurs de Météo France).
   * **Debug** : `Oui` ou `Non` (active les journaux détaillés dans Domoticz).
5. Cliquez sur **Ajouter**.

Les 5 tuiles de mesures et d'alertes seront créées immédiatement avec les noms préfixés par votre ville ou département résolu pour valider visuellement la géolocalisation.

---

## 📋 Prérequis

* Domoticz installé (version supportant les plugins Python, typiquement v4+).
* Python 3 installé sur le système exécutant Domoticz.
* Aucune bibliothèque externe (telle que `requests`) n'est requise, le plugin utilise exclusivement les modules natifs de Python (`urllib`, `json`, `datetime`) pour garantir une installation sans friction.

---

## 📝 Licence / Crédits

Plugin adapté pour fonctionner sans clé API et enrichi des données de prévisions complètes et pluie dans l'heure.
Dépôt GitHub : [J0hnMatrix/domoticz-vigilance-meteo](https://github.com/J0hnMatrix/domoticz-vigilance-meteo)
