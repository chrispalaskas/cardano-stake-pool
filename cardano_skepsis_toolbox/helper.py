import requests
import json
import shutil
from os.path import exists
import cardano_cli_helper as cli


def getBlockfrostAPIData(requestString: str, apiKey: str):
    header = {"project_id":apiKey}
    # Get call from blockfrost.io
    data = requests.get(requestString, headers=header)
    if (data.status_code != 200):
        print('Error: Request failed: ', requestString)
        return False
    try:
        dataJson = json.loads(data.text)
        return dataJson
    except:
        print('Error: Request return not in JSON format')
        return False


def getRecipientsFromStakeAddr(stakeAddressesOfRecipients: list, recipientList: list, blockfrostURL: str, apiKey: str):
    # Convert staking address list to sending address list
    for stakeAddr in stakeAddressesOfRecipients:
        requestString = blockfrostURL + 'accounts/' + stakeAddr + '/addresses'
        addressJson = getBlockfrostAPIData(requestString, apiKey)
        # Use first address from the returned list 
        try:
            delegatorAddr = addressJson[0]['address']
            recipientList.append(delegatorAddr)
        except:
            print('Error: Key address not found.')
    return recipientList


def getSenderAddressFromTxHash(txHash: str, blockfrostURL: str, apiKey: str):
    txHash=txHash.split('#')[0] # Drop the TxId
    requestString = blockfrostURL + 'txs/' + txHash + '/utxos'
    txhashJson = getBlockfrostAPIData(requestString, apiKey)
    try:
        senderAddress = txhashJson['inputs'][0]['address']
        return senderAddress
    except:
        print('Error: Key inputs or address not found.')
        return False


def appendLogJson(logfile: str, data: dict):
    try:
        with open(logfile, 'r') as jsonlog:
            old_data = json.load(jsonlog)
    except:
        if exists(logfile):
            print('Logfile not loaded properly. Backing up and creating a new one.')
            shutil.copyfile(logfile, logfile + '.bk')
        else:
            print('Logfile does not exist. Creating a new one.')
        old_data = {}
    if old_data == {}:
        newDict = data
    else:
        newDict = {**old_data, **data}
    with open(logfile, 'w') as jsonlog:
        json.dump(newDict, jsonlog, indent=4)


def parseConfigSendAssets(configFile, stakeAddressesOfRecipients, recipientList):
    finRecipientObjList = []
    try:
        with open(configFile, 'r') as jsonConfig:
            print('Opened config file...')
            config = json.load(jsonConfig)
            myPaymentAddrFile = config['myPaymentAddrFile']
            myPaymentAddrSignKeyFile = config['myPaymentAddrSignKeyFile']
            tokenPolicyID = config['tokenPolicyID']
            noOfTokensToSend = config['noOfTokensToSend']
            minADAToSendWithToken = config['minADAToSendWithToken']
            sentTokensLogFile = config['sentTokensLogFile']
            minFee = config['minFee']
            blockfrostURL = config['blockFrostURL']
            blockFrostProjID = config['blockFrostProjID']
            recipientList = getRecipientsFromStakeAddr(stakeAddressesOfRecipients, recipientList, blockfrostURL, blockFrostProjID)
            for recipientAddr in recipientList:
                finRecipientObjList.append(cli.Recipient(recipientAddr, 0, minADAToSendWithToken, noOfTokensToSend))
            print('Config file parsed succesfully!')
            return myPaymentAddrFile, \
                   myPaymentAddrSignKeyFile, \
                   tokenPolicyID, \
                   sentTokensLogFile, \
                   minFee, \
                   finRecipientObjList
    except:
        print('Configuration file misformated or does not exist.')
        return False


def parseConfigMonitorAddr(configFile):
    print('0')
    try:
        with open(configFile, 'r') as jsonConfig:
            print('Opened config file...')
            config = json.load(jsonConfig)
            myPaymentAddrFile = config['myPaymentAddrFile']
            myPaymentAddrSignKeyFile = config['myPaymentAddrSignKeyFile']
            tokenPolicyID = config['tokenPolicyID']
            tokenPriceLovelace = config['tokenPriceLovelace']
            minADAToSendWithToken = config['minADAToSendWithToken']
            minFee = config['minFee']
            incomingTxhashLogFile = config['incomingTxhashLogFile']
            sentTxhashLogFile = config['sentTxhashLogFile']
            sentTokensLogFile = config['sentTokensLogFile']
            blockFrostURL = config['blockFrostURL']
            blockFrostProjID = config['blockFrostProjID']
            print('Config file parsed succesfully!')
            return myPaymentAddrFile, \
                   myPaymentAddrSignKeyFile, \
                   tokenPolicyID, \
                   tokenPriceLovelace, \
                   minADAToSendWithToken, \
                   minFee, \
                   incomingTxhashLogFile, \
                   sentTxhashLogFile, \
                   sentTokensLogFile, \
                   blockFrostURL, \
                   blockFrostProjID
    except:
        print('Configuration file misformated or does not exist.')
        return False