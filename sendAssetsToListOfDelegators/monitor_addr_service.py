from audioop import add
from glob import glob
import cardano_cli_helper as cli
import helper
import sendAssetsToRecipients as sendAssets
import json
import time
from datetime import datetime
from os.path import exists
import os

# Global variables
MyPaymentAddrFile = '/home/christo/Desktop/cnode/priv/wallet/SkepsisCoinWallet/payment.addr'
MyPaymentAddrSignKeyFile = '/home/christo/Desktop/cnode/priv/wallet/SkepsisCoinWallet/payment.skey'
TokenPolicyID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.XXXXXXXXXXX'      
TokenPriceLovelace = 3000000
NoOfTokensToSend = 1
MinADAToSendWithToken = 1444443
MinFee = cli.minFee
Incoming_txhash_log = '/home/christo/Documents/scripts/sendAssetsToRecipients/logs/incoming_txhash_log.json'
Sent_txhash_log = '/home/christo/Documents/scripts/sendAssetsToRecipients/logs/sent_txhash_log.json'


def main():
    sent_utxos_set = set([])
    # Add the last known used (sent) txHash from the logfile
    if exists(Sent_txhash_log):
        try:
            with open(Sent_txhash_log, 'r') as jsonlog:
                old_sent_txhash = json.load(jsonlog)     
                old_list = list(old_sent_txhash.keys())
                old_list.sort(reverse=True)
                sent_utxos_set.update(old_sent_txhash[old_list[0]])                
        except:
            print('Logfile misformated. Backing up and starting new.')
            os.rename(Sent_txhash_log, Sent_txhash_log + '.bk')

    tokenRecipientList = [] # List of class Recipient objects (address, ada amount received, ada refund amount, tokens to send)

    with open(MyPaymentAddrFile) as file:
        paymentAddr = file.read()
    cli.getProtocolJson() # Checks if it already exists, if not gets a new copy  
    while True:
        # Get your payment address TxHashes
        utxos = cli.getAddrUTxOs(paymentAddr)
        myTxHash = cli.getTxInWithLargestTokenAmount(utxos, TokenPolicyID)
        sent_utxos_set.add(myTxHash)
        # Store on log file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        latest_utxo = {}
        latest_utxo[current_time] = list(utxos)
        sent_utxo = {}
        sent_utxo[current_time] = list(sent_utxos_set)              
        new_utxos_set = set(utxos.keys())
        if (sent_utxos_set.issuperset(new_utxos_set)):
            print ('No incoming Tx, sleeping for 60 seconds...')
            time.sleep(6)
            continue
        helper.appendLogJson(Incoming_txhash_log, latest_utxo)
        helper.appendLogJson(Sent_txhash_log, sent_utxo)  
        print('Incoming Tx detected!')
        diff_utxos = new_utxos_set.difference(sent_utxos_set)
        
        for new_utxo in diff_utxos:
            address_received = helper.getSenderAddressFromTxHash(new_utxo)
            if not address_received:
                continue
            print('Address received:', address_received)
            if address_received == paymentAddr:
                sent_utxos_set.add(new_utxo)
                continue
            lovelace_received = utxos[new_utxo]['value']['lovelace']
            print('Amount received:', lovelace_received)
            tokens_to_send = int((lovelace_received - MinADAToSendWithToken - MinFee) / TokenPriceLovelace)
            print('Tokens to send: ', tokens_to_send)
            lovelace_amount_to_refund = lovelace_received - (tokens_to_send * TokenPriceLovelace) - MinFee
            print('Lovelace amount to refund: ', lovelace_amount_to_refund)
            tokenRecipientList.append(cli.Recipient(address_received, lovelace_received, 
                                                    lovelace_amount_to_refund, tokens_to_send))            
        if sendAssets.main(tokenRecipientList):           
            for new_utxo in diff_utxos:
                sent_utxos_set.add(new_utxo)
            tokenRecipientList = []
        else:
            print('Unexpected error encountered, trying again...')         


if __name__ == '__main__':
    print('Monitor an address for incoming payments.')
    main()
