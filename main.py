import time
import network
import machine
from simple import MQTTClient

#config infos capteurs dans un dictionnaire (broche TRIC, ECHO, led associée et topic associé)
CAPTEURS = [
    {'TRIG': machine.Pin(2, machine.Pin.OUT), 'ECHO': machine.Pin(3, machine.Pin.IN), 'LED': machine.Pin(20, machine.Pin.OUT), 'TOPIC': "places/place1"},
    {'TRIG': machine.Pin(4, machine.Pin.OUT), 'ECHO': machine.Pin(5, machine.Pin.IN), 'LED': machine.Pin(19, machine.Pin.OUT), 'TOPIC': "places/place2"},
    {'TRIG': machine.Pin(6, machine.Pin.OUT), 'ECHO': machine.Pin(7, machine.Pin.IN), 'LED': machine.Pin(18, machine.Pin.OUT), 'TOPIC': "places/place3"}
]

#config wifi/MQTT
SSID = "CIEL1_2.4G"
PASSWORD = "StMichel2023-25"
MQTT_BROKER = "172.31.254.254"
MQTT_CLIENT_ID = "pico1"

TIMEOUT_US = 15000  #timeout pour éviter les blocages capteurs

def mesureDistance(capteur):
    capteur['TRIG'].low()
    time.sleep_us(2)
    capteur['TRIG'].high()
    time.sleep_us(50)
    capteur['TRIG'].low()
    
    debut = time.ticks_us()
    while capteur['ECHO'].value() == 0:
        if time.ticks_diff(time.ticks_us(), debut) > TIMEOUT_US: #si dépassement de la valeur de timeout
            return -1 
        
    debut = time.ticks_us()
    while capteur['ECHO'].value() == 1:
        if time.ticks_diff(time.ticks_us(), debut) > TIMEOUT_US: #si dépassement de la valeur de timeout
            return -1
    duree = time.ticks_us() - debut
    return round((duree * 0.0343) / 2, 2) #conversion cm

def connectionWifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    for _ in range(5):
        if wlan.isconnected():
            return True
        time.sleep(1)
    #print("Erreur connexion wifi")
    return False

def envoiMqtt(client, topic, etat):
    try:
        client.publish(topic, etat)
    except Exception as e:
        print(f"Erreur publication sur le serveur mqtt")

if not connectionWifi():
    machine.reset() #si la pico ne se connecte au wifi pas au démarrage, redémarrage auto

try:
    mqtt_client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    mqtt_client.connect()
except:
    machine.reset() #si la pico ne se connecte pas au broker mqtt lors du démarrage, redémarrage auto


while True:
    if not network.WLAN(network.STA_IF).isconnected():
        machine.reset() #vérifie que ce la pico soit toujours connecté au wifi au début de chaque boucle, sinon redémarrage auto
    
    #itération sur dictionnaire des capteurs
    for capteur in CAPTEURS:
        distance = mesureDistance(capteur)
        if distance == -1:
            continue #si -1 (erreur) saute l'itération
        
        etat = "Prise" if distance < 9 else "Libre"
        capteur['LED'].value(etat == "Libre")
        envoiMqtt(mqtt_client, capteur['TOPIC'], etat) #envoi etat de la place sur le topic du capteur associé
        #print(f"{capteur['TOPIC']}: {etat} (Distance: {distance} cm)")
        
    time.sleep(0.5)
