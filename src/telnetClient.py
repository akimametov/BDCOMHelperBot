import re

from netmiko import ConnectHandler


def getOnuInformation(IPList,ONU_MAC,USER,PASSWORD):

    for IP in IPList:
        DEVICE_PARAMS = {
            'device_type': 'cisco_ios_telnet',
            'host': IP,
            'username': USER,
            'password': PASSWORD,
            'port': 23,
        }

        with ConnectHandler(**DEVICE_PARAMS) as telnet:
            telnet.enable()
            ONUInformation = telnet.send_command('sh epon onu-information mac-address ' + ONU_MAC)
            if ONUInformation != '':

                #Найти в выводе команды интерфейс соответсвующего ONU
                ONUInterfaceRegex=re.compile(r'EPON0/\d+:\d{1,2}')
                ONUInterfaceMatch=ONUInterfaceRegex.search(ONUInformation)
                ONUInterface=ONUInterfaceMatch.group()

                ONUStatus=ONUInformation.split()[-2]

                #Description
                ONUDescriptionRegex=re.compile(r'\w{4}.\w{4}.\w{4}\s(\S*)')
                ONUDescriptionMatch=ONUDescriptionRegex.search(ONUInformation)
                ONUDescription=ONUDescriptionMatch.group(1)

                if ONUStatus=="auto-configured" or ONUStatus=="figured":    #"figured" - для поддержки старых P3310 (статус выводится так - "auto-con\nfigured")
                    ONUOpticalSignal=telnet.send_command('sh epon interface '+ONUInterface+' onu ctc optical-transceive')
                    ONUEthPortState=telnet.send_command('sh epon interface '+ONUInterface+' onu port 1 state', read_timeout=30, delay_factor=30)
                    ONUMacAddress=telnet.send_command('sh mac address-table interface '+ONUInterface)
                    ONUActiveInformation=telnet.send_command('sh epon active-onu mac-address '+ONU_MAC)                   

                    #Uptime и LastDeregReason
                    ONUActiveInformationRegex=re.compile(r'(\d+\W\d+\W\d+\W\d+:\d+:\d+)\s(\S+)\s+(\d(\s+)?\.\d\d:\d\d:\d\d)')
                    ONUActiveUptimeMatch=ONUActiveInformationRegex.search(ONUActiveInformation)
                    ONUActiveLastDeregTime=ONUActiveUptimeMatch.group(1)
                    ONUActiveLastDeregReason=ONUActiveUptimeMatch.group(2)
                    ONUActiveUptime=ONUActiveUptimeMatch.group(3)

                    #Состояние Eth-порта
                    ONUEthPortStateRegex=re.compile(r'\D+(Link-Up|Link-Down)(\D+(\d+Mbps)\s\D+(Full-Duplex|Half-Duplex))?')
                    ONUEthPortStateMatch=ONUEthPortStateRegex.search(ONUEthPortState)
                    ONUEthPortState=ONUEthPortStateMatch.group(1)
                    if ONUEthPortState == "Link-Up" and ONUEthPortStateMatch.group(3) != None and ONUEthPortStateMatch.group(4) != None:
                        ONUEthPortState+=' ' + ONUEthPortStateMatch.group(3)
                        ONUEthPortState+=' ' + ONUEthPortStateMatch.group(4)


                    #Таблица MAC-адресов
                    ONUMacAddressRegex=re.compile(r'\d+\t+\w{4}.\w{4}.\w{4}')
                    ONUMacAddress=ONUMacAddressRegex.findall(ONUMacAddress)

                    return(ONUInterface, ONUStatus, ONUOpticalSignal.split()[-1], ONUActiveUptime, ONUActiveLastDeregReason, ONUActiveLastDeregTime, ONUEthPortState, ONUDescription, *ONUMacAddress)

                elif ONUStatus=="deregistered":
                    ONUInactiveInformation=telnet.send_command('sh epon inactive-onu mac-address '+ONU_MAC)
                    ONUInactiveInformationRegex=re.compile(r'(\S+)\s+(\d+\W+\d\d:\d\d:\d\d)')
                    ONUInactiveInformationMatch=ONUInactiveInformationRegex.search(ONUInactiveInformation)
                    ONUInactiveLastDeregReason=ONUInactiveInformationMatch.group(1)
                    ONUInactiveAbsenttime=ONUInactiveInformationMatch.group(2)

                    return(ONUInterface, ONUStatus, ONUInactiveLastDeregReason, ONUInactiveAbsenttime, ONUDescription)
                        
                    
                else:   #ONUStatus=="lost"
                    return(ONUInterface, ONUStatus)


        telnet.disconnect()
                
    if ONUInformation == "":
        return ('ONU не найден')