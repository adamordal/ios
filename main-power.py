#! /usr/bin/env python

from netmiko import ConnectHandler
import netmiko
import re
import concurrent.futures
import logging
import csv
from datetime import datetime
import getpass

##Setup Logging##
t = datetime.now()
now = t.strftime("%m-%d-%I-%M")
logging.basicConfig(filename='switches-{}.log'.format(now), level=logging.INFO)

def get_power_inline(switch):
    ports = []
    logging.info('Getting power info from {}'.format(switch['host']))
    try:
        ssh_conn = ConnectHandler(**switch)
        result = ssh_conn.send_command("show power inline | inc Gi1/0/12", delay_factor=5,max_loops=300)
#        result = ssh_conn.send_command("show power inline | inc AIR", delay_factor=5,max_loops=300)
        for line in result.splitlines():
            #Get switch number and switch port
            if bool(re.search(r'(^Gi\S+)',line)):
                port_id = re.search(r'(^Gi\S+)',line).group(1)
                ports.append(port_id)
        temp_dict = {
            'host':switch['host'],
            'ports': ports
        }
        return(temp_dict)
    except netmiko.ssh_exception.NetmikoAuthenticationException as e:
        if 'Authentication to device failed' in str(e):
            logging.error('Authentication failed during show run on {}'.format(switch['host']))


def open_file(filename):
    '''Open a file for reading'''
    raw_file = open(filename, mode = 'r', encoding='utf-8-sig')
    csv_reader = csv.DictReader(raw_file)
    return csv_reader

def main():
    #Define some temporary variables
    temp_list = []
    switches = []
    power_devices = []

    #prompt user for csv filename & credentials
    filename = str(input("Enter the name of the csv file. Include file extension.:\n"))
    username = str(input("Enter the username for all of the devices in the csv:\n"))
    password = getpass.getpass("Enter the password for all of the devices in the csv:\n")

    #Open CSV
    devices = open_file(filename)

    #Assign temp_dict to devices (switch IPs from the csv)
    for device in devices:
        if device['Switch'] not in temp_list:
            switch = {
                'host':device['Switch'],
                'username':username,
                'password': password,
                'device_type': 'cisco_ios'
            }
            switches.append(switch)
            temp_list.append(device['Switch'])

    #Async run through the list of devices
    with concurrent.futures.ThreadPoolExecutor() as executor:
        power_devices+=executor.map(get_power_inline, switches)


        #Create a new .csv
    csv_file = open('new_csv.csv', mode='w',newline='')
    #Set headers
    fieldnames = ['Switch','Port']
    #Write headers
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for device in power_devices:
        for port in device['ports']:
            writer.writerow({'Switch':device['host'],'Port':port})

    csv_file.close()

if __name__ == '__main__':
    main()