#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 15:40:30 2022

@author: Christos ASKP
"""

import cardano_cli_helper as cli
import helper
from datetime import datetime


# List of addresses you want to send to
RecipientList = [

                ] 
                
# List of stake addresses you want to send to                
StakeAddressesOfRecipients = \
    [        
        
    ]


def main(finRecipientList, myPaymentAddrFile, tokenPolicyID, sent_tokens_log_file, minFee):
    with open(myPaymentAddrFile) as file:
        paymentAddr = file.read()
    cli.getProtocolJson() # Checks if it already exists, if not gets a new copy  

    # Get your payment address TxHashes
    utxos = cli.getAddrUTxOs(paymentAddr) 

    # Get your TxHash which contains the tokens with PolicyID, and your ADA and token amount
    allTxInList = utxos.keys() # Use this as tx_In to consolidate all addresses
    myTxHash = cli.getTxInWithLargestTokenAmount(utxos, tokenPolicyID)
    tokensDict = cli.getTokenListFromTxHash(utxos)
    if 'ADA' in tokensDict.keys():
        myInitLovelace = tokensDict['ADA']
    else:
        print('Error: no ADA found in address.')
        return False
    if tokenPolicyID in tokensDict.keys():
        myInitToken = tokensDict[tokenPolicyID]
    else:
        print('Error: Could not find token with Policy ID ', tokenPolicyID)    
        return False
    print ('myInitLovelace:', myInitLovelace)
    print ('myInitToken:', myInitToken)

    # Send noOfTokens to all your recipients with one Tx
    result = cli.sendTokenToAddr(myPaymentAddrSignKeyFile, allTxInList, myInitLovelace, myInitToken, paymentAddr,
                                 finRecipientList, tokenPolicyID, minFee) 
    if result == -1:
        print ('Error: Tokens could not be sent.')
        return False
    
    if cli.getCnodeJournal(paymentAddr, tokenPolicyID, myTxHash):
        # Store sent transactions on log file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")  
        latest_tx = {current_time:{}}
        for recipient in finRecipientList:
            latest_tx[current_time][recipient.address] = {}
            latest_tx[current_time][recipient.address]['ADA Received'] = '%.3f'%(recipient.lovelace_amount_received/1000000)
            latest_tx[current_time][recipient.address]['ADA Sent'] = '%.3f'%(recipient.lovelace_amount_to_send/1000000)
            latest_tx[current_time][recipient.address]['Tokens Sent'] = recipient.token_amount_to_send
        helper.appendLogJson(sent_tokens_log_file, latest_tx)
        print('Log appended')
        return True
    else:
        return False


if __name__ == '__main__':
    print('Send one NFT to each delegator in the list.')
    configFile = '/home/christo/Documents/cardano-stake-pool/cardano_skepsis_toolbox/config.json'    
    myPaymentAddrFile, myPaymentAddrSignKeyFile, tokenPolicyID, \
    sentTokensLogFile, noOfTokensToSend, minADAToSendWithToken, \
    finRecipientObjList, minFee = helper.parseConfigSendAssets(configFile, StakeAddressesOfRecipients, RecipientList)

    if len(finRecipientObjList) != 0:
        main(finRecipientObjList, myPaymentAddrFile, tokenPolicyID, sentTokensLogFile, minFee)
    else:
        print('Empty list of recipients received.')
