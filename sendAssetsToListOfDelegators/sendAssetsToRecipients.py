#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 15:40:30 2022

@author: Christos ASKP
"""

import requests
import json
from subprocess import PIPE, Popen
from os.path import exists
from datetime import datetime

# Global variables
url = 'https://cardano-mainnet.blockfrost.io/api/v0/'
blockFrostProjID = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
myPaymentAddrFile = 'PATH_TO/payment.addr'
myPaymentAddrSignKeyFile = 'PATH_TO/payment.skey'
tokenPolicyID = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx'      
noOfTokensToSend = 1
minADAToSendWithToken = 1444443

stakeAddressesOfRecipients = \
    [
        "stake1XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxx",
        "stake2XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxx",
        "stake3XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxx",
        "stake4XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxx",
        "stake5XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxx"        
     ]


def getCardanoCliValue(command, key):
    with Popen(command, stdout=PIPE, stderr=PIPE, shell=True) as process:       
        stdout, stderr = process.communicate()    
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")        
        print(stdout)
        print(stderr)
        if not stderr == '':
            return (-1)
    if not key == '': 
        try:
            result = json.loads(stdout)[key]
            return result
        except:
            print('Error: Request return not in JSON format')
            return(-1)
    return stdout


def getAddrUTxOs(addr):
    print('Getting address\' transactions...')
    outfile = 'utxos.json'
    command = f'cardano-cli query utxo --address {addr} --mainnet --out-file {outfile}'
    getCardanoCliValue(command, '')
    file = open(outfile)
    utxosJson = json.load(file)
    file.close()
    return utxosJson


def getTxHashWithToken(utxosJson, policyID):
    print (utxosJson)
    txHashWithToken = ''
    initLovelace = -1
    initToken = -1
    for key in utxosJson.keys():
        address = utxosJson[key]['address']
        tokensDict = {}
        for key2 in utxosJson[key]['value'].keys():
            if key2 == 'lovelace':
                tokensDict['ADA'] = utxosJson[key]['value'][key2] / 1000000
                initLovelace = utxosJson[key]['value'][key2]
            else:
                for key3 in utxosJson[key]['value'][key2].keys():
                    tokensDict[key2+'.'+key3] = utxosJson[key]['value'][key2][key3]
                    if key2+'.'+key3 == tokenPolicyID:
                        txHashWithToken = key
                        initToken = utxosJson[key]['value'][key2][key3]
    return txHashWithToken, initLovelace, initToken


def getProtocolJson():
    if not exists('protocol.json'):
        print('Getting protocol.json...')
        command = 'cardano-cli query protocol-parameters --mainnet --out-file protocol.json'
        return getCardanoCliValue(command, '')
    else:
        print ('Protocol file found.')
        return


def getCurrentSlot():
    print('Getting current slotNo...')
    command = f'cardano-cli query tip --mainnet'
    return getCardanoCliValue(command, 'slot')


def getMinFee(txOutCnt):
    print('Getting min fee for transaction...')
    command = f'cardano-cli transaction calculate-min-fee \
                                --tx-body-file tx.tmp \
                                --tx-in-count 1 \
                                --tx-out-count {txOutCnt} \
                                --mainnet \
                                --witness-count 1 \
                                --byron-witness-count 0 \
                                --protocol-params-file protocol.json'
    feeString = getCardanoCliValue(command, '')
    return int(feeString.split(' ')[0])
    

def getDraftTX(txIn, returnAddr, recipientList, ttlSlot):
    print('Creating tx.tmp...')
    command = f'cardano-cli transaction build-raw \
                --fee 0 \
                --tx-in {txIn} '
    for toAddr in recipientList:
        command += f'--tx-out {toAddr}+0+"0 {tokenPolicyID}" '
    command += f'--tx-out {returnAddr}+0+"0 {tokenPolicyID}" \
                 --invalid-hereafter {ttlSlot}  \
                 --out-file tx.tmp'
    return getCardanoCliValue(command, '')
    

def getRawTx(txIn, initLovelace, initToken, returnAddr, recipientList, ttlSlot, fee, adaAmount, tokenAmount):
    print('Creating tx.raw...')
    adaToReturn = initLovelace - fee - adaAmount*len(recipientList)
    tokensToReturn = initToken - tokenAmount*len(recipientList)
    print('adaToReturn: ', adaToReturn)
    print('tokensToReturn: ', tokensToReturn)
    command = f'cardano-cli transaction build-raw \
                --fee {fee} \
                --tx-in {txIn} '
    for toAddr in recipientList:
        command += f'--tx-out {toAddr}+{adaAmount}+"{tokenAmount} {tokenPolicyID}" ' 
    command += f'--tx-out {returnAddr}+{adaToReturn}+"{tokensToReturn} {tokenPolicyID}" \
                 --invalid-hereafter {ttlSlot} \
                 --out-file tx.raw'   
    getCardanoCliValue(command, '')

    
def signTx():
    print('Signing Transaction...')
    command = f'cardano-cli transaction sign \
                    --signing-key-file {myPaymentAddrSignKeyFile} \
                    --tx-body-file tx.raw \
                    --out-file tx.signed \
                    --mainnet'    
    getCardanoCliValue(command, '')


def submitSignedTx():
    print('Submitting Transaction...')
    command = 'cardano-cli transaction submit --tx-file tx.signed --mainnet'
    getCardanoCliValue(command, '')


def sendTokenToAddr(txIn, initLovelace, initToken, fromAddr, recipientList, adaAmount, tokenAmount):
    ttlSlot = getCurrentSlot() + 2000
    print('TTL Slot:', ttlSlot)
    getDraftTX(txIn, fromAddr, recipientList, ttlSlot)
    fee = getMinFee(len(recipientList))
    print ('Min fee:', fee)
    getRawTx(txIn, initLovelace, initToken, fromAddr, recipientList, ttlSlot, fee, adaAmount, tokenAmount)
    signTx()
    submitSignedTx()
    

def main():
    with open(myPaymentAddrFile) as f:
        paymentAddr = f.read()
    getProtocolJson()
    recipientList = []
    for stakeAddr in stakeAddressesOfRecipients:
        requestString = url + 'accounts/' + stakeAddr + '/addresses'
        header = {"project_id":blockFrostProjID}
        getAddresses = requests.get(requestString, headers=header)
        if (getAddresses.status_code != 200):
            print('Error: Request failed: ', requestString)
        try:
            addressJson = json.loads(getAddresses.text)
        except:
            print('Error: Request return not in JSON format')
            return(-1)
        delegatorAddr = addressJson[0]['address']
        recipientList.append(delegatorAddr)

    utxos = getAddrUTxOs(paymentAddr)
    myTxIn, myInitLovelace, myInitToken = getTxHashWithToken(utxos, tokenPolicyID)
    if (myTxIn == ''):
        print ('Error: No token found in sender Address.')
        return -1
    if (myInitLovelace == -1):
        print ('Error: No ADA balance found in sender Address.')
        return -1
    if (myInitToken == -1):
        print ('Error: No token balance found in sender Address.')
        return -1
    print ('myTxIn: ', myTxIn)
    print ('myInitLovelace', myInitLovelace)
    print ('myInitToken', myInitToken)

    sendTokenToAddr(myTxIn, myInitLovelace, myInitToken, paymentAddr, recipientList, minADAToSendWithToken, noOfTokensToSend)

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print('Transaction submitted at ' + current_time + '.')

    return (0)

if __name__ == '__main__':
    print('Send one NFT to each delegator in the list.')
    main()
