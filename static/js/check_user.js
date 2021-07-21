async function checkUser(data, user) {
    var check_addr;
    var input_data = JSON.stringify(data);
    var _hash = web3.utils.keccak256(input_data);
    var _sig = await window.web3.eth.personal.sign(_hash, user);
    await web3.eth.personal.ecRecover(_hash, _sig)
        .then(function (res) { check_addr = res });
    return check_addr;
}