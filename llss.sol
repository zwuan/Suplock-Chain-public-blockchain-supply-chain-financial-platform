// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
// 
contract llss{  //is IERC165
    address public ace; //合約持有人
    uint256 public count; //token個數

    event TransferSingle(address indexed operator, address indexed from, address indexed to, uint256 id, uint256 value);// 鑄幣、移轉時觸發
    event ApprovalForAll(address indexed account, address indexed operator, bool approved);

    mapping(uint256 => mapping(address => uint256)) private _balances;  // [ID類別][所有人地址]-->持有數量
    mapping(uint256=>uint256) private _price;  //[id類別]-->單價
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    
    constructor(address _ace) public{ //ERC1155("")
        ace = _ace;
        count=0;
    }
    
            //限定合約持有人
    modifier onlyAce() {
        require(msg.sender == ace, "only ace can call this");
        _;
    }
    
            //鑄造新1155(發行數量, 單價)
    function addNew(uint256 initialSupply, uint256 price, address receiver) external onlyAce{
        count++;
        uint256 tokenClassId = count;
        _mint(receiver, tokenClassId, initialSupply, price);        
    }
            //移轉1155
    function transferFrom(address from, address to, uint256 id, uint256 amount) external onlyAce{
        //require(from == msg.sender || isApprovedForAll(from, msg.sender));
        uint256 fromBalance = _balances[id][from];
        require(fromBalance >= amount);
        unchecked {
            _balances[id][from] = fromBalance - amount;
        }
        _balances[id][to] += amount;
        emit TransferSingle(msg.sender, from, to, id, amount);
    }
    
            //增加現有的1155
    function moreToken(address account, uint256 id, uint256 amount) external onlyAce{ 
        _mint(account, id, amount, _price[id]);
    }
            // internal 鑄幣
    function _mint(address account, uint256 id, uint256 amount, uint256 price) internal virtual {
        require(account != address(0), "ERC1155: mint to the zero address");
        _balances[id][account] += amount;
        _price[id] = price;
        emit TransferSingle(msg.sender, address(0), account, id, amount);
    }
    
            //改動現有的token price
    function changePrice(uint256 id, uint256 newPrice) external onlyAce{ 
        _price[id] = newPrice;
    }
            //銷毀某account的id幣
    function burn(uint256 id, address account, uint256 amount) external onlyAce{ 
        _balances[id][account]-=amount;
        
    }
    
            //察看某人持有某token的數量
    function balanceOf(address account, uint256 id) public view returns (uint256) {
        return _balances[id][account];
    }

            //某些人持有某些token的數量  跑不出來...?
    function balanceOfBatch(address[] calldata accounts, uint256[] calldata ids) external view
        returns (uint256[] memory){
            uint256[] memory batchBalances = new uint256[](accounts.length);

            for (uint256 i = 0; i < accounts.length; ++i) {
                batchBalances[i] = balanceOf(accounts[i], ids[i]);
            }

            return batchBalances;
        }
            //msg.sender 開關 operator對自己token的轉移權力
    function setApprovalForAll(address operator, bool approved) external{
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

            //查看account是否給予operator權力
    function isApprovedForAll(address account, address operator) public view returns (bool){
        return _operatorApprovals[account][operator];
    }
}