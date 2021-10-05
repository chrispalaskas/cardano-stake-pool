# cardano-stake-pool
The source code to the website, using fullPage.js.

Some how tos, helpful for running a cardano staking pool node.

The script sendADA.py has some public variables that need to be set in order to work.

1. SendingAddress: The address from which the ADA tokens will be sent, will be removed.
1. Tx: The hash of the transaction of the sending address we will use.
1. Ix: The ID, usually a single digit (0,1...)
1. Balance: The balance of that TxIx (not the total balance of the address)
1. ReceivingAddress: The address to which we will send the ADA tokens.
1. SendAmount: The amount of lovelace (1 milllionth of an ADA) to send.
1. CurrentEra: The current era of the blockchain (Shelley, Allegra, Maria, Goguen, etc)
1. TransactionFolder: A (temporary) folder where the transaction files will be stored. Can be deleted after the tranasaction.
1. KeysFolder: The folder that contains the address private key.
1. PaymentSKey: The secret or private key, necessary to sign the transaction before submitting.

After these variables are set, run:
> python3 sendADA.py
