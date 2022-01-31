*** This script sends Cardano native tokens/NFTs to the first address from a list of staking addresses ***
*** Useful for SPO airdrops to delegators ***

Create a virtual environment and install requirements:
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

Edit the sendAssetsToRecipients.py:
1. Add your own API key for https://cardano-mainnet.blockfrost.io
2. Add the paths to your payment.addr and payment.skey files
3. Add the token's policy ID 
4. Add a list of stake keys you want to send the tokens
5. Run python3 sendAssetsToRecipients.py

Example requests for BlockFrost:
curl -H 'project_id: mainnetvDjTcvrKjuAzCEII8JZUbebidpMCdLOq' https://cardano-mainnet.blockfrost.io/api/v0/genesis
curl -H 'project_id: mainnetvDjTcvrKjuAzCEII8JZUbebidpMCdLOq' https://cardano-mainnet.blockfrost.io/api/v0/blocks/latest
curl -H 'project_id: mainnetvDjTcvrKjuAzCEII8JZUbebidpMCdLOq' https://cardano-mainnet.blockfrost.io/api/v0/pools/?order=desc


