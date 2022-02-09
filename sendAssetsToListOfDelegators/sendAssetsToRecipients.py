#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 15:40:30 2022

@author: Christos ASKP
"""

from cmath import log
import cardano_cli_helper as cli
import helper
import json
from datetime import datetime


# Global variables
MyPaymentAddrFile = '/home/christo/Desktop/cnode/priv/wallet/SkepsisCoinWallet/payment.addr'
MyPaymentAddrSignKeyFile = '/home/christo/Desktop/cnode/priv/wallet/SkepsisCoinWallet/payment.skey'
TokenPolicyID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx.XXXXXXXXXXX'      
NoOfTokensToSend = 1
MinADAToSendWithToken = 1444443
Sent_tokens_log_file = '/home/christo/Documents/scripts/sendAssetsToRecipients/logs/sent_tokens_log_file.json'

# List of addresses you want to send to
RecipientList = [

                ] 
                
# List of stake addresses you want to send to                
StakeAddressesOfRecipients = \
    [        

    ]


def main(finRecipientList):
    with open(MyPaymentAddrFile) as file:
        paymentAddr = file.read()
    cli.getProtocolJson() # Checks if it already exists, if not gets a new copy  

    # Get your payment address TxHashes
    utxos = cli.getAddrUTxOs(paymentAddr) 

    # Get your TxHash which contains the tokens with PolicyID, and your ADA and token amount
    allTxInList = utxos.keys() # Use this as tx_In to consolidate all addresses
    myTxHash = cli.getTxInWithLargestTokenAmount(utxos, TokenPolicyID)
    tokensDict = cli.getTokenListFromTxHash(utxos)
    if 'ADA' in tokensDict.keys():
        myInitLovelace = tokensDict['ADA']
    else:
        print('Error: no ADA found in address.')
        return False
    if TokenPolicyID in tokensDict.keys():
        myInitToken = tokensDict[TokenPolicyID]
    else:
        print('Error: Could not find token with Policy ID ', TokenPolicyID)    
        return False
    print ('myInitLovelace:', myInitLovelace)
    print ('myInitToken:', myInitToken)

    # Send noOfTokens to all your recipients with one Tx
    result = cli.sendTokenToAddr(MyPaymentAddrSignKeyFile, allTxInList, myInitLovelace, myInitToken, paymentAddr,
                                 finRecipientList, TokenPolicyID) 
    if result == -1:
        print ('Error: Tokens could not be sent.')
        return False
    
    if cli.getCnodeJournal(paymentAddr, TokenPolicyID, myTxHash):
        # Store sent transactions on log file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")  
        latest_tx = {current_time:{}}
        old_tx_log = {}
        for recipient in finRecipientList:
            latest_tx[current_time][recipient.address] = {}
            latest_tx[current_time][recipient.address]['ADA Received'] = '%.3f'%(recipient.lovelace_amount_received/1000000)
            latest_tx[current_time][recipient.address]['ADA Sent'] = '%.3f'%(recipient.lovelace_amount_to_send/1000000)
            latest_tx[current_time][recipient.address]['Tokens Sent'] = recipient.token_amount_to_send
        helper.appendLogJson(Sent_tokens_log_file, latest_tx)
        return True
    else:
        return False


if __name__ == '__main__':
    print('Send one NFT to each delegator in the list.')
    finalRecipientList = helper.getRecipientsFromStakeAddr(StakeAddressesOfRecipients, RecipientList)
    finRecipientTupleList = []
    for recipientAddr in finalRecipientList:
        finRecipientTupleList.append(cli.Recipient(recipientAddr, 0, MinADAToSendWithToken, NoOfTokensToSend))
    main(finRecipientTupleList)
