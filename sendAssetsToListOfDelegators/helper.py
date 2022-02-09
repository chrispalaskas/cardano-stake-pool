import requests
import json
import shutil
from os.path import exists


BlockfrostURL = 'https://cardano-mainnet.blockfrost.io/api/v0/'
BlockFrostProjID = 'mainnetXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

def getBlockfrostAPIData(requestString: str):
    header = {"project_id":BlockFrostProjID}
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


def getRecipientsFromStakeAddr(stakeAddressesOfRecipients: list, recipientList: list):
    # Convert staking address list to sending address list
    for stakeAddr in stakeAddressesOfRecipients:
        requestString = BlockfrostURL + 'accounts/' + stakeAddr + '/addresses'
        addressJson = getBlockfrostAPIData(requestString)
        # Use first address from the returned list 
        try:
            delegatorAddr = addressJson[0]['address']
            recipientList.append(delegatorAddr)
        except:
            print('Error: Key address not found.')
    return recipientList


def getSenderAddressFromTxHash(txHash: str):
    txHash=txHash.split('#')[0] # Drop the TxId
    requestString = BlockfrostURL + 'txs/' + txHash + '/utxos'
    txhashJson = getBlockfrostAPIData(requestString)
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
