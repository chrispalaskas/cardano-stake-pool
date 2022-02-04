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
import time


# Global variables
url = 'https://cardano-mainnet.blockfrost.io/api/v0/'
blockFrostProjID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
myPaymentAddrFile = '/home/christo/Desktop/cnode/priv/wallet/SkepsisCoinWallet/payment.addr'
myPaymentAddrSignKeyFile = '/home/christo/Desktop/cnode/priv/wallet/SkepsisCoinWallet/payment.skey'
tokenPolicyID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXXXXXx'      
noOfTokensToSend = 1
minADAToSendWithToken = 1444443

# List of addresses you want to send to
recipientList = [
                    'addr1XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
                ] 
                
# List of stake addresses you want to send to                
stakeAddressesOfRecipients = \
    [        

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
            print('Error: Request return not in JSON format or key ', key, ' doesn\'t exist')
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
    txHashWithTokenFound = False
    sumLovelace = 0
    sumToken = 0
    for key in utxosJson.keys():
        # tokensDict = {}
        for key2 in utxosJson[key]['value'].keys():
            if key2 == 'lovelace':
                # tokensDict['ADA'] = utxosJson[key]['value'][key2]
                sumLovelace += utxosJson[key]['value'][key2]
            else:
                for key3 in utxosJson[key]['value'][key2].keys():
                    # tokensDict[key2+'.'+key3] = utxosJson[key]['value'][key2][key3]
                    if key2+'.'+key3 == tokenPolicyID:
                        txHashWithTokenFound = True
                        sumToken += utxosJson[key]['value'][key2][key3]
    if sumLovelace == 0 or sumToken == 0:
        txHashWithTokenFound = False
    return utxosJson.keys(), sumLovelace, sumToken, txHashWithTokenFound


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


def getMinFee(txInCnt, txOutCnt):
    print('Getting min fee for transaction...')
    txOutCnt += 1
    witness_count = 1
    command = f'cardano-cli transaction calculate-min-fee \
                                --tx-body-file tx.tmp \
                                --tx-in-count {txInCnt} \
                                --tx-out-count {txOutCnt} \
                                --mainnet \
                                --witness-count {witness_count} \
                                --byron-witness-count 0 \
                                --protocol-params-file protocol.json'
    feeString = getCardanoCliValue(command, '')
    return int(feeString.split(' ')[0])


def getDraftTX(txInList, returnAddr, recipientList, ttlSlot):
    print('Creating tx.tmp...') 
    command = f'cardano-cli transaction build-raw \
                --fee 0 '
    for txIn in txInList:
        command += f'--tx-in {txIn} '
    for toAddr in recipientList:
        command += f'--tx-out {toAddr}+0+"0 {tokenPolicyID}" '
    command += f'--tx-out {returnAddr}+0+"0 {tokenPolicyID}" \
                 --invalid-hereafter {ttlSlot}  \
                 --out-file tx.tmp'
    getCardanoCliValue(command, '')
    return
    

def getRawTx(txInList, initLovelace, initToken, returnAddr, recipientList, ttlSlot, fee, adaAmount, tokenAmount, isConsolidation):
    print('Creating tx.raw...')
    adaToReturn = initLovelace - fee - adaAmount*len(recipientList)
    tokensToReturn = initToken - tokenAmount*len(recipientList)
    print('adaToReturn: ', adaToReturn)
    print('tokensToReturn: ', tokensToReturn)
    command = f'cardano-cli transaction build-raw \
                --fee {fee} '
    for txIn in txInList:
        command += f'--tx-in {txIn} '
    for toAddr in recipientList:
        command += f'--tx-out {toAddr}+{adaAmount}+"{tokenAmount} {tokenPolicyID}" ' 
    if not isConsolidation:
        command += f'--tx-out {returnAddr}+{adaToReturn}+"{tokensToReturn} {tokenPolicyID}" '
    command += f'--invalid-hereafter {ttlSlot} \
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
    return getCardanoCliValue(command, '')


def sendTokenToAddr(txInList, initLovelace, initToken, fromAddr, recipientList, adaAmount, tokenAmount):
    ttlSlot = getCurrentSlot() + 2000
    print('TTL Slot:', ttlSlot)
    getDraftTX(txInList, fromAddr, recipientList, ttlSlot)
    fee = getMinFee(len(txInList), len(recipientList))
    print ('Min fee:', fee)
    getRawTx(txInList, initLovelace, initToken, fromAddr, recipientList, ttlSlot, fee, adaAmount, tokenAmount, False)
    signTx()
    return submitSignedTx()


def getRecipientsFromStakeAddr():
    # Convert staking address list to sending address list
    for stakeAddr in stakeAddressesOfRecipients:
        requestString = url + 'accounts/' + stakeAddr + '/addresses'
        header = {"project_id":blockFrostProjID}
        # Get call from blockfrost.io
        getAddresses = requests.get(requestString, headers=header)
        if (getAddresses.status_code != 200):
            print('Error: Request failed: ', requestString)
            continue
        try:
            addressJson = json.loads(getAddresses.text)
        except:
            print('Error: Request return not in JSON format')
            return(-1)
        # Use first address from the returned list 
        try:
            delegatorAddr = addressJson[0]['address']
            print(delegatorAddr)
            recipientList.append(delegatorAddr)
        except:
            print('Error: Key address not found.')


def main():
    with open(myPaymentAddrFile) as file:
        paymentAddr = file.read()
    getProtocolJson() # Checks if it already exists, if not gets a new copy

    getRecipientsFromStakeAddr()      

    # Get your payment address TxHashes
    utxos = getAddrUTxOs(paymentAddr) 

    # Get your TxHash which contains the tokens with PolicyID, and your ADA and token amount
    myTxInList, myInitLovelace, myInitToken, txHashWithTokenFound = getTxHashWithToken(utxos, tokenPolicyID)

    # Error checks
    if (not txHashWithTokenFound):
        print ('Error: Insufficient balances found in sender Address.')
        return -1
    print ('myInitLovelace:', myInitLovelace)
    print ('myInitToken:', myInitToken)

    # Send noOfTokens to all your recipients with one Tx
    result = sendTokenToAddr(myTxInList, myInitLovelace, myInitToken, paymentAddr, recipientList, minADAToSendWithToken, noOfTokensToSend) 
    if result == -1:
        print ('Error: Tokens could not be sent.')
        return -1
    
    # Print the current time to estimate how long it will take
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print('Transaction submitted at ' + current_time + '.')

    while True:
        time.sleep (10)
        utxosNew = getAddrUTxOs(paymentAddr)
        if utxos != utxosNew:
            timediff = datetime.now() - now
            print ('Trasnaction succesfully recorded on blockchain in ', timediff)
            return 0
        print ('Network is loaded, waiting for the next block to record Tx...')

    return (0)

if __name__ == '__main__':
    print('Send one NFT to each delegator in the list.')
    main()
