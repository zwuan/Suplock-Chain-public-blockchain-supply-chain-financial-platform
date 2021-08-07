pragma solidity ^0.8.1;
//import "@openzeppelin/contracts-ethereum-package/contracts/math/SafeMath.sol"; 為啥這個不行
import "github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/math/SafeMath.sol";

contract Core{
    using SafeMath for uint256;
    using SafeMath for uint16;
    //加interface
    constructor (address _core, uint _total_amount){
        core = _core;
        total_amount_A = _total_amount;
        token_A[_core] = _total_amount;
        emit core_event(address(this),core);
    }
    
    struct TokenB{
        address core; //核心地址
        address parent; //來源者，二次轉移時，可用作還錢使用
        uint256 par;//票面價值，代表原來的價錢
        uint256 amount;
        uint256 interest;
        uint256 date;
        uint id;
        uint former_id; //用於轉移時可以找回那筆
        uint16 class;
        uint16 former_class;
        string status;
        uint256 level;
        
    }
    
    mapping(address=>uint256)public token_A;
    mapping(address=>mapping(uint16=>uint256))public transaction;
    mapping(address=>mapping(uint16=>mapping(uint256=>TokenB)))public token_B; //由持有人地址、class、transaction可以找到那個tokenB
    address public core; // 合約的持有者
    uint256 total_amount_A; //紀錄取得的tokenA總數
    uint256 total_amount_B; //紀錄發出的tokenB總數
    address platform =  0x5B38Da6a701c568545dCfcB03FcB875f56beddC4; //部署人（平台）
    //0x5B38Da6a701c568545dCfcB03FcB875f56beddC4
    
    //event 的部分
    event core_event(address contraact, address core); //合約地址，和核心地址
    event loan_event(address loaner ,uint id, uint256 amount, uint256 interest, uint256 date); //貸款人、loan_token id, 數量、 利息
    event minttokenA_event(uint256 amount);// mint了多少tokenA
    event tokenB_event(address issuer, address receiver, uint256 amount, uint16 class, uint id, uint256 interest, uint256 date); //剩餘次數、存貨驗證? AtoB(), BtoC()
    event burnB_event(uint id, uint16 class, address company);//tokenB_id, tokenB class, 及目前的持有人
    event partial_burnB_event(uint id, uint16 class, address company, uint256 amount);//tokenB_id, tokenB class, 及目前的持有人
    event burnA_event(uint256 amount); //燒了多少tokenＡ
    event BtoPlatform(address from, uint256 amount);//廠商給平台多少tokenB
    
    modifier onlyPlatform(){
        //確認是由平台發出交易
        require(msg.sender == platform);
        _;
    }
    
    function totalSupply_A() public view virtual  onlyPlatform returns (uint256) {
        return total_amount_A;
    }
    
    function totalSupply_B() public view virtual onlyPlatform returns (uint256) {
        return total_amount_B;
    }
    
    function ballanceOf_A(address _account) public view virtual onlyPlatform returns(uint256){
        return token_A[_account];
    } 
    function mintTokenA(uint256 _amount) public onlyPlatform {
        require(msg.sender == platform);
        token_A[core] = token_A[core].add(_amount);
        total_amount_A = total_amount_A.add(_amount);
        emit minttokenA_event(_amount);
    }
    function _getTransaction(address _account, uint16 _class) private view onlyPlatform returns(uint256){
        return transaction[_account][_class];
    }
    function AToB(address _to, uint256 _amount, uint256 _interest, uint256 _date, uint16 _class)public  onlyPlatform{
        _AToPlatform(_amount); //將核心的tokenA數量減去，並轉移給平台
        uint256 num_trac = _addTransaction(_to,_class); //取得本次(原來+1)交易次數
        TokenB memory _tokenB; //建立一個tokenB
        _tokenB.core = core; //核心企業地址
        _tokenB.parent = core; //來源
        _tokenB.par = _amount;
        _tokenB.amount = _amount; //amount設定
        _tokenB.interest = _interest;
        _tokenB.class = _class; //將tokenB分為三類（1應收、2訂單、3轉移、4借貸）這邊只有前兩種
        _tokenB.date = _date;//時間從後端來？
        _tokenB.level = 1;
        _tokenB.id = uint(keccak256(abi.encodePacked(block.timestamp))); //ID的建立
        _tokenB.status = "unfinished";
        token_B[_to][_class][num_trac] = _tokenB; //將token轉移給目標地址
        total_amount_B = total_amount_B.add(_amount);
        emit tokenB_event(core, _to, _tokenB.amount, _class, _tokenB.id, _tokenB.interest, _tokenB.date); //剩餘次數、存貨驗證? AtoB(), BtoC()

    }
    
    function llssToB(uint256 _amount, uint256 _interest, uint256 _date) external {
        uint256 num_trac = _addTransaction(core, 5); //取得本次(原來+1)交易次數
        TokenB memory _tokenB; //建立一個tokenB
        _tokenB.core = core; //核心企業地址
        _tokenB.parent = core; //來源
        _tokenB.amount = _amount; //amount設定
        _tokenB.interest = _interest;
        _tokenB.class = 5; //第5類:實體物驗證抵押
        _tokenB.date = _date;
        _tokenB.id = uint(keccak256(abi.encodePacked(block.timestamp))); //ID的建立
        _tokenB.status = "unfinished";
        token_B[core][5][num_trac] = _tokenB; //將token轉移給目標地址
        total_amount_B = total_amount_B.add(_amount);
        emit tokenB_event(core, core, _tokenB.amount, 5, _tokenB.id, _tokenB.interest, _tokenB.date);
    } 
    
    function BtoC(address _from, address _to, uint256 _amount, uint256 _interest, uint _id, uint16 _class, uint16 c_class, uint256 _date) public onlyPlatform {
        //tokenB的二次交易
        //後端做利率及時間的檢查
        uint256 trac = _findTransaction(_from, _class, _id); //找id一樣的transaction
        require(trac!=0, "Token not found!");//若為0代表沒有符合條件的訂單
        TokenB memory _tokenB  = token_B[_from][_class][trac]; //取得原來的tokenB
        require(keccak256(abi.encodePacked(_tokenB.status)) != keccak256(abi.encodePacked("finished")),"Token is not avaliable!");//若是該筆教交易已經完成，則不可以進行轉移
        _tokenB.amount = _tokenB.amount.sub(_amount); //將此訂單減去amount
        _tokenB.status = "Part_Transfered"; //部分被轉移，還有餘額
        if (_tokenB.amount==0){
            _tokenB.status = "Transfered"; //全部都被轉移
        }
        uint256 former_level = _tokenB.level;
        token_B[_from][_class][trac] = _tokenB;
        uint256 trac_c = _addTransaction(_to, c_class); //計算這次tracsaction的編號，c_class為b跟c之間的關係
        TokenB memory _tokenC; //鑄新的交易
        _tokenC.core = core;
        _tokenC.parent = _from; //來源者，之後還錢用來記錄
        _tokenC.par = _amount;
        _tokenC.amount = _amount;
        _tokenC.interest = _interest;
        _tokenC.id = uint(keccak256(abi.encodePacked(block.timestamp))); //ID的建立
        _tokenC.former_id = _id;//tokenB的ID記錄在這裡
        _tokenC.class = c_class; //將tokenB分為三類（應收、訂單、轉移、貸款)
        _tokenC.former_class = _class; //tokenB的的class記錄在這
        _tokenC.date = _date;//時間從後端來？
        _tokenC.level = former_level.add(1);
        _tokenC.status = "unfinishded";
        token_B[_to][c_class][trac_c] = _tokenC; //將token轉移給目標地址
        emit tokenB_event(_from, _to, _tokenC.amount, _tokenC.class, _tokenC.id, _tokenC.interest, _tokenC.date);
        
    }
    function _findTransaction(address _from, uint16 _class, uint _id) view internal onlyPlatform returns(uint256){
        //iterator用時間（id）來尋找要用來操作的那筆TokenB
        uint256 transaction_time =_getTransaction(_from,_class); //這個是此地址在平台使用哪種Class的操作次數
        for (uint i = 1; i < transaction_time+1; i++){
            if(token_B[_from][_class][i].id==_id){
                return i; //ID一樣則對該筆TokenB進行操作
            }
        }
        return 0; //找不到即為0
        
    }
    function _addTransaction(address _to, uint16 _class) internal onlyPlatform returns(uint256){
        uint256 num_trac = _getTransaction(_to,_class); //先用getTransaction拿到目前的交易次數
        if(num_trac==0){
            transaction[_to][_class] = 1;
        }
        else{
            transaction[_to][_class] = transaction[_to][_class].add(1); //加一代表本次轉移
        }
        return transaction[_to][_class];
        
    }
    function _AToPlatform(uint256 _amount) onlyPlatform internal {
        token_A[core] = token_A[core].sub(_amount); //將核心企業的tokenA數量修正
        token_A[platform] = token_A[platform].add(_amount); //並將tokenA數量轉移給平台
    }
    function _BToPlatform(address _from, uint256 _amount, uint16 _class, uint _id) onlyPlatform internal{
        uint256 trac = _findTransaction(_from, _class, _id);
        TokenB memory _tokenB = token_B[_from][_class][trac]; 
        require(keccak256(abi.encodePacked(_tokenB.status)) != keccak256(abi.encodePacked("finished")),"Token is not avaliable!");
        _tokenB.amount = _tokenB.amount.sub(_amount);
        if (_tokenB.amount==0){
            _tokenB.status = "loaning";
        }
        token_B[_from][_class][trac] = _tokenB;
        emit BtoPlatform(_from, _tokenB.amount);

    }
    //驗證（扣押721）有市價，ERC1155
    //function etherDeposit(address holder)
    //kill contract
    function burnA(uint256 _amount) onlyPlatform public{
        require(msg.sender == platform);
        token_A[core] = token_A[core].sub(_amount);
        emit burnA_event(_amount);
    }
    function burnB(address _to, uint16 _class, uint _id) onlyPlatform public{
        uint256 num_trac = _findTransaction(_to, _class, _id); //取得該筆交易
        TokenB memory _tokenB = token_B[_to][_class][num_trac];
        require(_tokenB.amount == _tokenB.par);
        _tokenB.status = "finished"; //完成該筆交易
        if (_tokenB.level>1){
            uint256 trac = _findTransaction(_tokenB.parent, _tokenB.former_class, _tokenB.former_id);
            token_B[_tokenB.parent][ _tokenB.former_class][trac].amount = token_B[_tokenB.parent][ _tokenB.former_class][trac].amount.add(_tokenB.par);
        }
        else{
            token_A[core] = token_A[core].add(_tokenB.par); //將核心企業的tokenA數量修正
            token_A[platform] = token_A[platform].sub(_tokenB.par); //並將平台的tokenA還給核心
        }
        token_B[_to][_class][num_trac] = _tokenB;
        emit burnB_event(_id, _class, _to);
    }
    function partial_burnB(address _to, uint16 _class, uint _id, uint256 _amount) onlyPlatform public{
        //還利息時多還的部分要扣掉本金
        uint256 num_trac = _findTransaction(_to, _class, _id); //取得該筆交易
        TokenB memory _tokenB = token_B[_to][_class][num_trac];
        _tokenB.par = _tokenB.par.sub(_amount);
        _tokenB.amount = _tokenB.amount.sub(_amount);
        if (_tokenB.level>1){
            uint256 trac = _findTransaction(_tokenB.parent, _tokenB.former_class, _tokenB.former_id);
            token_B[_tokenB.parent][ _tokenB.former_class][trac].amount = token_B[_tokenB.parent][ _tokenB.former_class][trac].amount.add(_amount);
        }
        else{
            token_A[core] = token_A[core].add(_amount); //將核心企業的tokenA數量修正
            token_A[platform] = token_A[platform].sub(_amount); //並將平台的tokenA還給核心
        }
        token_B[_to][_class][num_trac] = _tokenB;
        emit partial_burnB_event(_id, _class, _to, _amount);//tokenB_id, tokenB class, 本次完成的數量及目前的持有人

    }
    function loan (address _loaner, uint256 _amount, uint16 _class, uint _id, uint256 _interest, uint256 _date) onlyPlatform public {
        _BToPlatform(_loaner, _amount, _class, _id);
        TokenB memory loan_token;
        loan_token.core = core;
        loan_token.parent = _loaner; //來源者，之後還錢用來記錄
        loan_token.amount = _amount;
        loan_token.interest = _interest;
        loan_token.id = uint(keccak256(abi.encodePacked(block.timestamp))); //ID的建立
        loan_token.former_id = _id;//將用來借錢tokenB的ID記錄在這裡
        loan_token.class = 4; //將tokenB分為四類（應收、訂單、轉移、貸款)
        loan_token.former_class = _class; //將用來借錢tokenB的的class記錄在這
        loan_token.date = _date;
        uint256 loan_trac = _addTransaction(_loaner,4); //取得加上這次融資的tracsaction number
        token_B[_loaner][4][loan_trac] = loan_token;
        emit loan_event(_loaner ,loan_token.id, loan_token.amount, loan_token.interest, loan_token.date); //貸款人、loan_token id, 數量、 利息
    }
    
    //kill
    function kill() onlyPlatform public {
        address payable addr = payable(platform);
        selfdestruct(addr);
    }
    //fallback function 
    
    
}