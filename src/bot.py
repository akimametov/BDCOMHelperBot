import os

import telebot
from dotenv import load_dotenv

import OLT
import telnetClient

load_dotenv()

telegramBotToken=os.getenv("telegramBotToken")
oltUsername=os.getenv("oltUsername")
oltPassword=os.getenv("oltPassword")

bot = telebot.TeleBot(telegramBotToken)

@bot.message_handler(content_types=['text'])

def get_text_messages(message):
    location, mac = message.text.splitlines()

    oltListIP = OLT.getOltIP(location)
    if not oltListIP:
        bot.send_message(message.from_user.id,"Населённый пункт не найден")
        return
    
    ONUInformation = telnetClient.getOnuInformation(oltListIP,str(mac),oltUsername,oltPassword)

    if ONUInformation == "ONU не найден":                                                       #Если функция getOnuInformation возвращает строку и в ней содержится "ONU не найден"
        ONUInformationMessage = ["ONU не найден"]

    elif ONUInformation[1] == "auto-configured" or ONUInformation[1] == "figured":              #Если ONU онлайн, выводим полную информацию. "figured" - для поддержки старых P3310 (auto-con\nfigured)
        ONUInformationMessage = [f"Interface: {ONUInformation[0]}\n",
                                 f"Status: {ONUInformation[1]}\n",
                                 f"Signal: {ONUInformation[2]} dBm\n",
                                 "\n",
                                 f"Eth-port: {ONUInformation[6]}\n",
                                 f"MAC-table: \n{"\n".join(ONUInformation[8:])}",
                                 "\n\n",
                                 f"Uptime: {ONUInformation[3]}\n",
                                 f"LastDeregReason: {ONUInformation[4]}\n",
                                 f"LastDeregTime: {ONUInformation[5]}\n"]
        if ONUInformation[7] != "N/A":                                                          #Если у ONU есть description, вставляем его в сообщение
            ONUInformationMessage.insert(1,f"Description: {ONUInformation[7]}\n")

    elif ONUInformation[1] == "deregistered":                                                   #Если ONU оффлайн
        ONUInformationMessage = [f"Interface: {ONUInformation[0]}\n",
                                 f"Status: {ONUInformation[1]}\n",
                                 f"Downtime: {ONUInformation[3]}\n",
                                 f"LastDeregReason: {ONUInformation[2]}"]
        if ONUInformation[4] != "N/A":                                                          #Если у ONU есть description, вставляем его в сообщение
            ONUInformationMessage.insert(1,f"Description: {ONUInformation[4]}\n")

    else:                                                                                       #Иначе ONU lost
       ONUInformationMessage = [f"Interface: {ONUInformation[0]}\n",
                                f"Status: {ONUInformation[1]}\n"]
      
    bot.send_message(message.from_user.id, "".join(ONUInformationMessage))

bot.polling(none_stop=True, interval=0)