let accounts;
const connect_wallet = document.getElementById("connect")
const addr = document.getElementById("addr")
document.getElementById('connect').addEventListener('click', async () => {
    // Modern dapp browsers...
    // if (window.ethereum) {
    //     window.web3 = new Web3(ethereum);
        try {
            // Request account access if needed
            const accounts = await window.ethereum.request({method: 'eth_requestAccounts'});
            console.log(accounts[0]);
            connect_wallet.style.display = 'none';
            // accounts = await web3.eth.getAccounts();
            addr.style.display = 'block';
            // web3.eth.sendTransaction({/* ... */});
        } catch (error) {
            // User denied account access...
        }
    // }
    // Legacy dapp browsers...
   
});
window.ethereum.on('accountsChanged', function (accounts) {
    $('#addr').val(accounts[0]);
});