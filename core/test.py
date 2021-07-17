from solidity.abi import abi
from web3 import Web3
provider_rpc = {
    'development': 'https://ropsten.infura.io/v3/396094052a124676a222214bd8a3bab8',
} #設定節點
w3 = Web3(Web3.HTTPProvider(provider_rpc['development'])) #將web3連上節點，這邊用測試的Ropsten
#平台帳號資訊
account_from = {
    'private_key': '6af669c4f0c75961cd006a970c8839ea122612c85305ff2da1edb3eff39ffaf7',
    'address': '0xA3E58464444bC66b5bb7FB8e76D7F4fDE52126F2',
}
Core = w3.eth.contract('0x0494B34C9Cbc0835D1F0dB3529f9F204BC2C5C56',abi=abi)
construct_txn = Core.functions.mintTokenA(300000).buildTransaction(
        {
            'from': account_from['address'],
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
)

# 簽名
tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])

# transaction送出並且等待回傳
tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

