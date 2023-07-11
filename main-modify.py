from netmiko import ConnectHandler
import netmiko
import concurrent.futures
import logging
import csv
from datetime import datetime
import getpass


##Setup Logging##
t = datetime.now()
now = t.strftime("%m-%d-%I-%M")
logging.basicConfig(filename='switches-{}.log'.format(now), level=logging.INFO)


#Global variable
device_ports = []

def modify_config(switch):
    command_ports = []
    for port in device_ports:
        if port.get('host') == switch['host']:
            command_ports = port['ports']

    logging.info('Modifying ports on {}'.format(switch['host']))
    try:
        ssh_conn = ConnectHandler(**switch)
        for interface in command_ports:
            commands = [f'default interface {interface}',
                f'interface {interface}',
                'description Wireless AP',
                'switchport mode trunk',
                'switchport trunk native vlan 32'
                ]
            #ssh_conn.enable() ## Ask if needed for their environment
            output = ssh_conn.send_config_set(commands,delay_factor=5,max_loops=300)

        return(output)
    except netmiko.ssh_exception.NetmikoAuthenticationException as e:
        if 'Authentication to device failed' in str(e):
            logging.error('Authentication failed during SCP enable on {}'.format(switch['host']))

    return()

def write_mem(switch):
    logging.info('Write mem on {}'.format(switch['host']))
    try:
        ssh_conn = ConnectHandler(**switch)
        commands = [f'write mem']                
        #ssh_conn.enable() ## Ask if needed for their environment
        output = ssh_conn.send_config_set(commands,delay_factor=5,max_loops=300)

        return(output)
    except netmiko.ssh_exception.NetmikoAuthenticationException as e:
        if 'Authentication to device failed' in str(e):
            logging.error('Authentication failed during SCP enable on {}'.format(switch['host']))

    return()

def open_file(filename):
    '''Open a file for reading'''
    raw_file = open(filename, mode = 'r', encoding='utf-8-sig')
    csv_reader = csv.DictReader(raw_file)
    return csv_reader

def main():
    temp_list = []
    
    switches = []

    #prompt user for csv filename & credentials
    filename = str(input("Enter the name of the csv file. Include file extension.:\n"))
    username = str(input("Enter the username for all of the devices in the csv:\n"))
    password = getpass.getpass("Enter the password for all of the devices in the csv:\n")

    #Open CSV
    devices = open_file(filename)

    #Assign temp_dict to devices (switch IPs from the csv)
    for device in devices:
        if device['Switch'] not in temp_list:
            device_port = {
                'host':device['Switch'],
                'ports':[device['Port']]
            }
            switch = {
                'host':device['Switch'],
                'username':username,
                'password': password,
                #'secret': password, ##Ask if needed for their environment
                'device_type': 'cisco_ios'
            }
            switches.append(switch)
            device_ports.append(device_port)
            temp_list.append(device['Switch'])
        else:
            for item in device_ports:
                for k,v in item.items():
                    if v == device['Switch']:
                        item['ports'].append(device['Port'])

    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(modify_config, switches)
        #executor.map(write_mem, switches)  #Commented out for testing. Needs more work.


if __name__ == '__main__':
    main()