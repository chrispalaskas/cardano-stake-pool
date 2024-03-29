import cardano_cli_helper as cli
import helper
import send_assets_to_recipients as sendAssets
import json
from datetime import datetime
from os.path import exists
import os


def main(myPaymentAddrFile,
         myPaymentAddrSignKeyFile,
         tokenPolicyID,
         tokenPriceLovelace,
         minADAToSendWithToken,
         minFee,
         incomingTxhashLogFile,
         sentTxhashLogFile,
         sentTokensLogFile,
         blockFrostURL,
         blockFrostProjID):
    sent_utxos_set = set([])
    # Add the last known used (sent) txHash from the logfile
    if exists(sentTxhashLogFile):
        try:
            with open(sentTxhashLogFile, 'r') as jsonlog:
                old_sent_txhash = json.load(jsonlog)
                old_list = list(old_sent_txhash.keys())
                old_list.sort(reverse=True)
                sent_utxos_set.update(old_sent_txhash[old_list[0]])
        except:
            print('Logfile misformated. Backing up and starting new.')
            os.rename(sentTxhashLogFile, sentTxhashLogFile + '.bk')

    tokenRecipientList = [] # List of class Recipient objects (address, ada amount received, ada refund amount, tokens to send)

    with open(myPaymentAddrFile) as file:
        paymentAddr = file.read()
    cli.getProtocolJson() # Checks if it already exists, if not gets a new copy
    while True:
        # Get your payment address TxHashes
        utxos = cli.getAddrUTxOs(paymentAddr)
        myTxHash = cli.getTxInWithLargestTokenAmount(utxos, tokenPolicyID)
        sent_utxos_set.add(myTxHash)
        # Store on log file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        latest_utxo = {}
        latest_utxo[current_time] = list(utxos)
        sent_utxo = {}
        sent_utxo[current_time] = list(sent_utxos_set)
        new_utxos_set = set(utxos.keys())
        # if (sent_utxos_set.issuperset(new_utxos_set)):
        #     print ('No incoming Tx, sleeping for 60 seconds...')
        #     time.sleep(6)
        #     continue
        helper.appendLogJson(incomingTxhashLogFile, latest_utxo)
        helper.appendLogJson(sentTxhashLogFile, sent_utxo)
        print('Incoming Tx detected!')
        diff_utxos = new_utxos_set.difference(sent_utxos_set)
        
        for new_utxo in diff_utxos:
            address_received = helper.getSenderAddressFromTxHash(new_utxo, blockFrostURL, blockFrostProjID)
            if not address_received:
                continue
            print('Address received:', address_received)
            if address_received == paymentAddr:
                sent_utxos_set.add(new_utxo)
                continue
            lovelace_received = utxos[new_utxo]['value']['lovelace']
            print('Amount received:', lovelace_received)
            tokens_to_send = int((lovelace_received - minADAToSendWithToken - minFee) / tokenPriceLovelace)
            print('Tokens to send: ', tokens_to_send)
            lovelace_amount_to_refund = lovelace_received - (tokens_to_send * tokenPriceLovelace) - minFee
            print('Lovelace amount to refund: ', lovelace_amount_to_refund)
            tokenRecipientList.append(cli.Recipient(address_received, lovelace_received, 
                                                    lovelace_amount_to_refund, tokens_to_send))
        if sendAssets.main(tokenRecipientList,
                           myPaymentAddrFile,
                           myPaymentAddrSignKeyFile,
                           tokenPolicyID,
                           sentTokensLogFile,
                           minFee):
            for new_utxo in diff_utxos:
                sent_utxos_set.add(new_utxo)
            tokenRecipientList = []
        else:
            print('Unexpected error encountered, trying again...')


if __name__ == '__main__':
    print('Monitor an address for incoming payments.')
    configFile = './config.json'
    myPaymentAddrFile, \
    myPaymentAddrSignKeyFile, \
    tokenPolicyID, \
    tokenPriceLovelace, \
    minADAToSendWithToken, \
    minFee, \
    incomingTxhashLogFile, \
    sentTxhashLogFile, \
    sentTokensLogFile, \
    blockFrostURL, \
    blockFrostProjID = helper.parseConfigMonitorAddr(configFile)

    main(myPaymentAddrFile,
         myPaymentAddrSignKeyFile,
         tokenPolicyID,
         tokenPriceLovelace,
         minADAToSendWithToken,
         minFee,
         incomingTxhashLogFile,
         sentTxhashLogFile,
         sentTokensLogFile,
         blockFrostURL,
         blockFrostProjID)