import os
import subprocess
import ast

SendingAddress   = 'addr1XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
Tx = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
Ix = X
Balance = 4823587
ReceivingAddress = 'addr1XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
CurrentEra = ' --allegra-era'
SendAmount = 1000000

TransactionFolder = '/home/name/transaction/'
ProtocolJson = 'protocol.json'
TransactionDraftFile = 'tx.draft'
TransactionRawFile = 'tx.raw'
TransactionSignedFile = 'tx.signed'

KeysFolder = '/home/name/keys/'
PaymentSKey = 'payment.skey'

# Only works for new addresses with one TxIx
def queryForTxIxBalance(address):
	queryString = 'cardano-cli query utxo --address ' + address + ' --mainnet ' + CurrentEra
	proc = subprocess.Popen([queryString], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	resultString = out.decode("utf-8")
	resultListLines = resultString.split('\n')
	resultSpaces = resultListLines[2].split(' ')
	result = []
	for elem in resultSpaces:
		if elem == '':
			continue
		result.append(elem)
	return result[0], result[1], result[2]


def createProtocolFile(protocolFile):
	queryString = 'cardano-cli query protocol-parameters --mainnet --out-file ' + protocolFile + CurrentEra
	proc = subprocess.Popen([queryString], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	return os.path.isfile(protocolFile)


def createTransactionFile(rawFile, Tx, Ix, sendAmount, changebackAmount, slotNo, fee):
        queryString = 'cardano-cli transaction build-raw --tx-in ' + str(Tx) + '#' + str(Ix) +\
        ' --tx-out ' + ReceivingAddress + '+' + str(sendAmount) +\
        ' --tx-out ' + SendingAddress + '+' + str(changebackAmount) +\
        ' --ttl ' + str(slotNo+500) +\
        ' --fee ' + str(fee) +\
        ' --out-file ' + rawFile

        print('Transaction File: ', queryString)
        proc = subprocess.Popen([queryString], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        return os.path.isfile(rawFile)


def getTransactionFees(rawFile, protocolFile):
	queryString = 'cardano-cli transaction calculate-min-fee' +\
	' --tx-body-file ' + rawFile +\
	' --tx-in-count 1' +\
	' --tx-out-count 2' +\
	' --witness-count 1' +\
	' --byron-witness-count 0' +\
	' --mainnet' +\
	' --protocol-params-file ' + protocolFile
	proc = subprocess.Popen([queryString], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	resultString = out.decode("utf-8")
	resultList = resultString.split(' ')
	return resultList[0]


def getCurrentSlotNo():
	queryString = 'cardano-cli query tip --mainnet'
	proc = subprocess.Popen([queryString], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	dict_str = out.decode("UTF-8")
	dict = ast.literal_eval(dict_str)
	return int(dict['slotNo'])


def signTransaction(rawTxFile, paymentSkey, txSignedFile):
        queryString = 'cardano-cli transaction sign' +\
        ' --tx-body-file ' + rawTxFile +\
        ' --signing-key-file ' + paymentSkey +\
        ' --mainnet' +\
        ' --out-file ' + txSignedFile
        proc = subprocess.Popen([queryString], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        return os.path.isfile(txSignedFile)


def submitTransaction(txSignedFile):
        queryString = 'cardano-cli transaction submit' +\
        ' --tx-file ' + txSignedFile +\
        ' --mainnet'

        proc = subprocess.Popen([queryString], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print('out: ', out)
        return True

def main():
        # (Tx, Ix, balance) = queryForTxIxBalance(SendingAddress)
        if not createProtocolFile(TransactionFolder + ProtocolJson):
                return False
        else:
                print('Protocol file created: ' + TransactionFolder + ProtocolJson)

        if not createTransactionFile(TransactionFolder + TransactionDraftFile, Tx, Ix, 0, 0, 0, 0):
                return False
        else:
                print('Transaction Draft file created: ' + TransactionFolder + TransactionDraftFile)

        fees = getTransactionFees(TransactionFolder + TransactionDraftFile, TransactionFolder + ProtocolJson)
        print('Fees: ', fees)
        print('Balance: ', Balance)
        print('SendAmount: ', SendAmount)
        changeback = Balance - SendAmount - int(fees)

        if changeback < 0:
                print("Insufficient Balance.")
                exit(0)

        print('Change Back: ', changeback)
        currentSlotNo = getCurrentSlotNo()

# TODO: Make a better slot check
        if currentSlotNo < 20577171 or currentSlotNo > 500000000:
                print("Slot number returned was invalid")
        else:
                print('SlotNo: ', currentSlotNo)

        if not createTransactionFile(TransactionFolder + TransactionRawFile, Tx, Ix, SendAmount, changeback, currentSlotNo, fees):
                print('ERROR: Transaction Raw file')
                exit(0)
        else:
                print('Transaction Raw file created: ' + TransactionFolder + TransactionRawFile)

        if not signTransaction(TransactionFolder + TransactionRawFile, KeysFolder + PaymentSKey, TransactionFolder + TransactionSignedFile):
                print('ERROR: Transaction not signed')
                exit(0)
        else:
                print('Transaction signed: ' + TransactionFolder + TransactionSignedFile)

        if not submitTransaction(TransactionFolder + TransactionSignedFile):
                print('ERROR: Transaction not submitted')
                exit(0)
        else:
               print('Transaction submitted!')

if __name__ == "__main__":
        # execute only if run as a script
        main()

