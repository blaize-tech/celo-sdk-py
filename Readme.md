# Python ContractKit

Celo's ContractKit is a library to help developers and validators to interact with the celo-blockchain.

ContractKit supports the following functionality:

- Connect to a node
- Access web3 object to interact with node's Json RPC API
- Send Transaction with celo's extra fields: (feeCurrency)
- Simple interface to interact with CELO and cUSD
- Simple interface to interact with Celo Core contracts
- Utilities

## User Guide

### Getting Started

To install:

```bash
pip install .
```

You need in Python version 3.8 or higher.

To start working with python contractkit you need a `Kit` instance:

```python
from celo_sdk.kit import Kit

kit = Kit('https://alfajores-forno.celo-testnet.org')
```

To access web3:

```python
kit.w3.eth.getBalance(some_address)
```

### Setting Default Tx Options

`Kit` allows you to set default transaction options:

```python
from celo_sdk.kit import Kit

kit = Kit('https://alfajores-forno.celo-testnet.org')
currency_address = kit.base_wrapper.registry.load_contract_by_name('StableToken')['address']
kit.wallet_fee_currency = currency_address
```

### Interacting with CELO & cUSD

celo-blockchain has two initial coins: CELO and cUSD (stableToken).
Both implement the ERC20 standard, and to interact with them is as simple as:

```python
gold_token = kit.base_wrapper.create_and_get_contract_by_name('GoldToken')
balance = gold_token.balance_of(address)
```

To send funds:

```python
one_gold = kit.w3.toWei(1, 'ether')
tx_hash = gold_token.transfer(address, one_gold)
```

To interact with cUSD, is the same but with a different contract:

```python
stable_token = kit.base_wrapper.create_and_get_contract_by_name('StableToken')
```

If you would like to pay fees in cUSD, set the gas price manually:

```python
stable_token = kit.base_wrapper.create_and_get_contract_by_name('StableToken')
gas_price_contract = kit.base_wrapper.create_and_get_contract_by_name('GasPriceMinimum')
gas_price_minimum = gas_price_contract.get_gas_price_minimum(stable_token.address)
gas_price = int(gas_price_minimum * 1.3) # Wiggle room if gas price minimum changes before tx is sent
kit.wallet_fee_currency = stable_token.address # Default to paying fees in cUSD
kit.wallet_gas_price = gas_price

tx = stable_token.transfer(recipient, wei_transfer_amount)
```

### Interacting with Other Contracts

Apart from GoldToken and StableToken, there are many core contracts.

For the moment, we have contract wrappers for:

- Accounts
- Attestations
- BlockchainParameters
- DoubleSigningSlasher
- DowntimeSlasher
- Election
- LockedGold
- Escrow
- Exchange
- Freezer
- GasPriceMinimum
- GoldToken
- Governance
- MultiSig
- Reserve
- ReleaseGold
- SortedOracles
- StableToken
- Validators

To create object of contract wrapper you shold set one of those contract names as a parameter to function `BaseWrapper.create_and_get_contract_by_name(...)`

## A Note About Contract Addresses

Celo Core Contracts addresses, can be obtained by looking at the `Registry` contract.
That's actually how `BaseWrapper` obtain them.

We expose the registry api, which can be accessed by:

```python
gold_token_address = kit.base_wrapper.registry.load_contract_by_name('GoldToken')['address']
```

## Adding new keys to the wallet

Wallet object by defaut generate some private key

But of course you can add your own already generated private key or generate new one

To add your own:

```python
from celo_sdk.kit import Kit

kit = Kit('https://alfajores-forno.celo-testnet.org')
kit.wallet_add_new_key = '0xf2f48ee19680706196e2e339e5da3491186e0c4c5030670656b0e0164837257d'
```

To generate new one:

```python
new_key = kit.generate_new_key()
kit.wallet_add_new_key = new_key
```

To see all the wallet accounts:

```python
accounts = kit.wallet.accounts
```

And to switch between accounts:

```python
kit.wallet_change_account = existing_account_address  # address of account has to be in wallet.__accounts dict
```

## Signing messages with wallet

In addition to signing the transaction, the wallet can sign messages:

```python
from celo_sdk.kit import Kit
from celo_sdk.celo_account.messages import encode_defunct

kit = Kit('https://alfajores-forno.celo-testnet.org')
message = kit.w3.soliditySha3(['address'], [signer]).hex()  # For example we want to sign someones address
message = encode_defunct(hexstr=message)
signature = kit.wallet.active_account.sign_message(message)
```