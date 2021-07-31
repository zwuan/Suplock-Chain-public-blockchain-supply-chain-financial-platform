// SPDX-License-Identifier: GPL-3.0
pragma experimental ABIEncoderV2;      
pragma solidity >0.6.0;
library SafeMath {
    /**
    * @dev Multiplies two numbers, reverts on overflow.
    */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
        // benefit is lost if 'b' is also tested.
        // See: https://github.com/OpenZeppelin/openzeppelin-solidity/pull/522
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b);

        return c;
    }

    /**
    * @dev Integer division of two numbers truncating the quotient, reverts on division by zero.
    */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        // Solidity only automatically asserts when dividing by 0
        require(b > 0);
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold

        return c;
    }

    /**
    * @dev Subtracts two numbers, reverts on overflow (i.e. if subtrahend is greater than minuend).
    */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a);
        uint256 c = a - b;

        return c;
    }

    /**
    * @dev Adds two numbers, reverts on overflow.
    */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a);

        return c;
    }

    /**
    * @dev Divides two numbers and returns the remainder (unsigned integer modulo),
    * reverts when dividing by zero.
    */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b != 0);
        return a % b;
    }
}

// 利息上鍊
// 從web3操作合約時，input 不需乘上10**18，但接到output時要除以10**18
contract investmentToken {
  using SafeMath for uint256;
  uint public constant decimals = 10**18;

  
  address platform =  0xA3E58464444bC66b5bb7FB8e76D7F4fDE52126F2; //部署人（平台）

  enum State {financing, passed, ended}
  
  // 借錢企業融資時取得憑證
  struct Certificate {
    address borrow_company; // 借錢企業地址
    uint principle;         // 欲貸金額
    uint interest;          // 利率
    uint dateSpan;
    uint riskClass;         // 分券等級(1:A, 2:B, 3:C)
    State state;
  }
  
  // 投資人分券
  struct TrancheInv {
    uint amount;            // 持有金額
    uint[] dividendIncome;    // 利息收入
    uint riskClass;         // 分券等級(1:A, 2:B, 3:C)
  }

  // 利息
  struct InterestRec {
    uint dateSpan;          // 總共期數
    uint termLeft;          // 剩下期數    
    uint interest;          // 利率
    uint[] principleArr;    // 每期應還本金
    uint[] interestArr;     // 每期應還利息    
  }
  
  struct Investor{
    address investor;
  }
  
  // loan_id指向投資者list trancheInvestor[loan_id][class]
  mapping(uint=>mapping(uint=>Investor[])) trancheInvestor;

  // 投資人擁有的投資分券 investorToken[投資人地址][loan_id][class]
  mapping(address=>mapping(uint=>mapping(uint=>TrancheInv))) public investorTranche;
  
  // 投資人分券列表 investorTrancheCount[投資人地址]
  mapping(address=>uint[]) investorTrancheList;
  
  // 投資人分券等級列表 investorTrancheCount[投資人地址][loan_id]
  mapping(address=>mapping(uint=>uint[])) investorTrancheClassList;
  
  // certificateMapping[loan_id][class]
  mapping(uint=>mapping(uint=>Certificate)) public certificateMapping;
  
  // mapping存利息紀錄[loan_id][class] 
  mapping(uint=>mapping(uint=>InterestRec)) public interestRecMapping;
  
  modifier onlyPlatform() {
    require(msg.sender == platform, "you are not kevin");
    _;
  }
  
  modifier inStatePassed(uint _loan_id, uint _class) {
    require (certificateMapping[_loan_id][_class].state == State.passed);
    _;
  }

  modifier inStateEnded(uint _loan_id, uint _class) {
    require (certificateMapping[_loan_id][_class].state == State.ended);
    _;
  }  
  
  modifier availEnough (uint _loan_id, uint _class, uint _amount) {
    // require (certificateMapping[_loan_id][_class].principle >= getClassPrincipleNotPaid(_loan_id, _class).add(_amount.mul(decimals)));
    require (certificateMapping[_loan_id][_class].principle >= getClassPrincipleNotPaid(_loan_id, _class).add(_amount));
    _;
  }
  
  modifier termEnough (uint _loan_id) {
      require(interestRecMapping[_loan_id][1].termLeft > 0);
      _;
  }
  
  event MintCertificate(uint _loan_id, address _borrow_company, uint _principle, uint _interest, uint _datespan, uint _riskClass);
  event LoanPassed(uint _loan_id, uint _class);
  event LoanEnded(uint _loan_id, uint _class);
  event BuyTranche(address _investor, uint _loan_id, uint _class, uint _amount);
  event EarlyPayback(uint _amount, uint _loan_id);  // emit 多還的部分(若還的剛好等於債權，則會回傳0)
  event NormalPayback(uint _amount, uint _loan_id); // emit 多還的部分(若還的剛好等於債權，則會回傳0)
  event BurnCertificae(uint _loan_id, uint _class);
  event Breach(uint _amount, uint _class);
  
  constructor () public {}
  
  
  function trancheAddInvestor (uint _loan_id, uint _class, address _investor) public onlyPlatform {
    trancheInvestor[_loan_id][_class].push(Investor(_investor));
  }

  function trancheGetInvestor (uint _loan_id, uint _class, uint index) public view returns(address){
    return trancheInvestor[_loan_id][_class][index].investor;
  }
  
  // ------------------------------------------------------------------------------------------------------------------------------------------
  // getter method section
  // ------------------------------------------------------------------------------------------------------------------------------------------

  function getInvestorIndexWithLoanID (uint _loan_id, uint _class, address _investor) internal view returns (uint) {
    for (uint i=0; i<trancheInvestor[_loan_id][_class].length; i++) {
      if (trancheGetInvestor(_loan_id, _class, i) == _investor) {
        return i;
      }
    }
  }
  
  // 由loan_id 及 分券等級來看該等級還有多少本金未還
  function getClassPrincipleNotPaid (uint _loan_id, uint _class) public view onlyPlatform returns (uint) {
    uint sum = 0;
    for (uint i=0; i<trancheInvestor[_loan_id][_class].length; i++) {
      address curr_investor = trancheGetInvestor(_loan_id, _class, i);
      sum = sum.add(investorTranche[curr_investor][_loan_id][_class].amount);
    }
    return sum;
  }
  
  // 由loan_id來看總融資金額
  function getTotalPrincipleNotPaid (uint _loan_id) public view onlyPlatform returns (uint) {
      uint sum = 0;
      for(uint i=1; i<4; i++){
          sum = sum.add(getClassPrincipleNotPaid(_loan_id, i));
      }
      return sum;
  }
  
  // 由loan_id 及 分券等級來看該等級還有多少利息未還
  function getClassDividendNotPaid (uint _loan_id, uint _class) public view onlyPlatform returns (uint) {
    uint sum = 0;
    InterestRec memory inv = interestRecMapping[_loan_id][_class];
    uint[] memory curr_arr = inv.interestArr;
    for (uint i=0; i<curr_arr.length; i++) {
      sum = sum.add(curr_arr[i]);
    }
    return sum;
  }

  function getTrancheState (uint _loan_id, uint _class) public view returns (State) {
      return certificateMapping[_loan_id][_class].state;
  }
  
//   function getTrancheAvail (uint _loan_id, uint _class) public view returns (uint) {
//     // return availamount[_loan_id];
//     return certificateMapping[_loan_id][_class].availAmount;
//   }
  
  function getInvestorTrancheAmount (address _investor, uint _loan_id, uint _class) public view returns (uint) {
      return investorTranche[_investor][_loan_id][_class].amount;
  }
  
  function getPaidTrancheNum (uint _loan_id, uint _class) public view returns (uint) {
    uint count = 0;
    for (uint i=0; i< trancheInvestor[_loan_id][_class].length; i++) {
        address investor = trancheGetInvestor(_loan_id, _class, i);
        if (investorTranche[investor][_loan_id][_class].amount == 0){
            count = count.add(1);
        }
    }
    return count;
  }
  
  // return a list of investor's loan_id, for backend
  function getInvestorLoanIdList(address _investor) public view returns (uint[] memory){
    uint count = investorTrancheList[_investor].length;
    uint[] memory ret = new uint[](count);
    for (uint i = 0; i < count; i++) {
        ret[i] = investorTrancheList[_investor][i];
    }
    return ret;
  }
  
  // return a list of investor's loan_id's class, for backend
  function getInvestorLoanIdClassList(address _investor, uint _loan_id) public view returns (uint[] memory){
    uint count = investorTrancheClassList[_investor][_loan_id].length;
    uint[] memory ret = new uint[](count);
    for (uint i = 1; i < count+1; i++) {
        ret[i-1] = investorTrancheClassList[_investor][_loan_id][i];
    }
    return ret;
  }
  
  // return tranche, for backend
  function getTrancheByInvestor(address _investor, uint _loan_id, uint _class) public view returns (TrancheInv memory) {
      return investorTranche[_investor][_loan_id][_class];
  }
  
  
  function getInterestArrValue (uint _loan_id, uint _class, uint _index) public onlyPlatform view returns (uint) {
    InterestRec memory curr_interestRec = interestRecMapping[_loan_id][_class];
    uint[] memory curr_arr = curr_interestRec.interestArr;
    return curr_arr[_index];
  }
  
  function getPrincipleArrValue (uint _loan_id, uint _class, uint _index) public onlyPlatform view returns (uint) {
    InterestRec memory curr_interestRec = interestRecMapping[_loan_id][_class];
    uint[] memory curr_arr = curr_interestRec.principleArr;
    return curr_arr[_index];
  }
  
  function getTermPriPayable (uint _loan_id, uint _term) public view returns (uint) {
      uint sum = 0;
      for (uint i=1; i < 4; i++) {
        InterestRec memory curr_interestRec = interestRecMapping[_loan_id][i];
        sum = sum.add(curr_interestRec.principleArr[_term]);
      }
      return sum;
  }
  
  function getTermIntPayable (uint _loan_id, uint _term) public view returns (uint) {
      uint sum = 0;
      for (uint i=1; i < 4; i++) {
        InterestRec memory curr_interestRec = interestRecMapping[_loan_id][i];
        sum = sum.add(curr_interestRec.interestArr[_term]);
      }
      return sum;
  }
  
  function getTermInvestorDiv (address _investor, uint _loan_id, uint _class, uint _term) public view returns (uint) {
      return investorTranche[_investor][_loan_id][_class].dividendIncome[_term];
  }
  
  function getTotalClassIntPayable (uint _loan_id, uint _class) public view returns (uint) {
    uint sum = 0;
    InterestRec memory curr_interestRec = interestRecMapping[_loan_id][_class];
    uint[] memory curr_arr = curr_interestRec.interestArr;
    for (uint i = 0; i < curr_arr.length; i++) {
        sum = sum.add(curr_arr[i]);
    }
    return sum;
  }
  
  // ------------------------------------------------------------------------------------------------------------------------------------------
  // state control section
  // ------------------------------------------------------------------------------------------------------------------------------------------

  // 通過最低達標金額，將certificate的state改變
  function loanPassed (uint _loan_id, uint _class) public onlyPlatform {
    certificateMapping[_loan_id][_class].state = State.passed;
    emit LoanPassed(_loan_id, _class);
  }
  
  function loanEnded (uint _loan_id, uint _class) public onlyPlatform {
    certificateMapping[_loan_id][_class].state = State.ended;
    emit LoanEnded(_loan_id, _class);
  }
  
  // 融資未過或已還清
  function burnCertificate (uint _loan_id, uint _class) public onlyPlatform {
    certificateMapping[_loan_id][_class].state = State.ended;
  }
  
  
  // ------------------------------------------------------------------------------------------------------------------------------------------
  // manipulate section
  // ------------------------------------------------------------------------------------------------------------------------------------------
    
  function mintCertificate (uint _loan_id, address _borrow_company, uint _principle, uint _interest, uint _datespan, uint _class)
    public 
    onlyPlatform
  {
    // uint amount = _principle.mul(decimals);
    uint amount = _principle;

    Certificate memory inv;
    inv.borrow_company = _borrow_company;
    inv.principle = amount;
    inv.interest = _interest;
    inv.dateSpan = _datespan;
    inv.riskClass = _class;
    inv.state = State.financing;

    certificateMapping[_loan_id][_class] = inv;
    
    // init interestArr
    createInterestArray(_loan_id, _class, _principle, _interest, _datespan);

    emit MintCertificate(_loan_id, _borrow_company, _principle, _interest, _datespan, _class);
    
  }
  
  // 投資人申購tranche
  // 只有class及amount為使用者輸入
  function buyTranche (address _investor, uint _loan_id, uint _class, uint _amount) 
    public 
    onlyPlatform
    // inStatePassed(_loan_id, _class)
    availEnough(_loan_id, _class, _amount)
  {
    // uint amount = _amount.mul(decimals);
    uint amount = _amount;

    // 減少可申購金額
    Certificate memory curr_certificate = certificateMapping[_loan_id][_class];

    // 如果同個tranche已申購過
    if (investorTranche[_investor][_loan_id][_class].amount > 0) {
        investorTranche[_investor][_loan_id][_class].amount = investorTranche[_investor][_loan_id][_class].amount.add(amount);
    } else {
        
        uint[] memory _dividendIncome = new uint[](curr_certificate.dateSpan);

        TrancheInv memory inv;
        inv.amount = amount;
        inv.dividendIncome = _dividendIncome;
        inv.riskClass = curr_certificate.riskClass;
        
        investorTranche[_investor][_loan_id][_class] = inv;
        trancheAddInvestor(_loan_id, _class, _investor);
        investorTrancheList[_investor].push(_loan_id);
        investorTrancheClassList[_investor][_loan_id].push(_class);
    }
    emit BuyTranche(_investor, _loan_id, _class, _amount);
  }
  
 
  // ------------------------------------------------------------------------------------------------------------------------------------------
  // 償還償還本金部分
  // 每個月會觸發一次還錢，一是歸還本金，二要分配利息
  // 每月應付的公式：
  // 首期分期利息按「核准金額X分期年利率÷12」計收；次期起，每期分期利息按「每期應付分期本金X未償期數X分期年利率÷12」計收。
  // 這樣每期歸還後可以到一個剩餘未還
  // 之後用剩餘未還可以算下期應還
  // ------------------------------------------------------------------------------------------------------------------------------------------ 
  
  // 首期分期利息按「核准金額X分期年利率÷12」計收；次期起，每期分期利息按「每期應付分期本金X未償期數X分期年利率÷12」計收。
  // _principle為融資總金額
  function createInterestArray (uint _loan_id, uint _class, uint _principle, uint _interest, uint _datespan)
    public
    onlyPlatform
    returns
    (bool)
  {
    // uint amount = _principle.mul(decimals);
    uint amount = _principle;

    // 每期應還本金
    uint principlePayable = amount.div(_datespan);
    // 建立array存每期應還
    uint[] memory _principleArr = new uint[](_datespan);
    uint[] memory _interestArr = new uint[](_datespan);
    
    // 計算每期應還
    for (uint i=0; i<_datespan; i++) {
        _principleArr[i] = principlePayable;
        if(i==0){
            uint firstTerm = amount.mul(_interest).div(12).div(100);
            _interestArr[i] = firstTerm;
        } else {
            uint term = amount.sub(principlePayable.mul(i)).mul(_interest).div(12).div(100);
            _interestArr[i] = term;
        }
    }
    
    InterestRec memory inv;
    inv.dateSpan = _datespan;
    inv.termLeft = _datespan;
    inv.interest = _interest;
    inv.principleArr = _principleArr;
    inv.interestArr = _interestArr;
    
    interestRecMapping[_loan_id][_class] = inv;
    
    return true;
  }
  

  // _amount是剩下本金 (從trancheNotPaid來)，return該期應償還利息
  function updateInterestArr (uint _loan_id, uint _class, uint _amount)
    public 
    onlyPlatform
    returns
    (uint)
  {

    InterestRec storage curr_interestRec = interestRecMapping[_loan_id][_class];
    uint curr_datespan = curr_interestRec.dateSpan;
    uint curr_termLeft = curr_interestRec.termLeft.sub(1);
    uint[] memory curr_principleArr = curr_interestRec.principleArr;
    uint[] memory curr_interestArr = curr_interestRec.interestArr;
    
    uint curr_termdiv = 0;
    if (curr_termLeft > 0) {
        uint principlePayable = _amount.div(curr_termLeft);
        for (uint i=0; i< curr_datespan; i++) {
            
            if (curr_interestArr[i] == 0) continue;
            
            // 如果還完則將term更新為0，並分配利息
            if (i < curr_datespan.sub(curr_termLeft)) {
                curr_principleArr[i] = 0;
                
                curr_termdiv = curr_interestArr[i];
                curr_interestArr[i] = 0;
            } else {
                // 當期
                curr_principleArr[i] = principlePayable;
    
                uint term = principlePayable.mul(curr_datespan.sub(i)).mul(curr_interestRec.interest).div(1200); // 因interest所以要除100
                curr_interestArr[i] = term;
            }
        }
    } else {
        // curr_termLeft變0時
        curr_principleArr[curr_datespan.sub(curr_termLeft).sub(1)] = 0;
        curr_termdiv = curr_interestArr[curr_datespan.sub(curr_termLeft).sub(1)];
        curr_interestArr[curr_datespan.sub(curr_termLeft).sub(1)] = 0;
    }
    
    
    // update interestRec
    curr_interestRec.termLeft = curr_termLeft;
    curr_interestRec.interestArr = curr_interestArr;
    curr_interestRec.principleArr = curr_principleArr;

    return curr_termdiv;
  }
  
    // _amount是剩下本金 (從trancheNotPaid來)，return該期應償還利息
  function earlyUpdateInterestArr (uint _loan_id, uint _class, uint _amount)
    public 
    onlyPlatform
    returns
    (uint)
  {

    InterestRec storage curr_interestRec = interestRecMapping[_loan_id][_class];
    uint curr_datespan = curr_interestRec.dateSpan;
    uint curr_termLeft = curr_interestRec.termLeft;
    uint[] memory curr_principleArr = curr_interestRec.principleArr;
    uint[] memory curr_interestArr = curr_interestRec.interestArr;
    
    uint curr_termdiv = 0;
    if (curr_termLeft > 0) {
        uint principlePayable = _amount.div(curr_termLeft);
        for (uint i=0; i< curr_datespan; i++) {
            
            if (curr_interestArr[i] == 0) continue;
            
            // 如果還完則將term更新為0，並分配利息
            if (i < curr_datespan.sub(curr_termLeft)) {
                curr_principleArr[i] = 0;
                
                curr_termdiv = curr_interestArr[i];
                curr_interestArr[i] = 0;
            } else {
                // 當期
                curr_principleArr[i] = principlePayable;
    
                uint term = principlePayable.mul(curr_datespan.sub(i)).mul(curr_interestRec.interest).div(1200); // 因interest所以要除100
                curr_interestArr[i] = term;
            }
        }
    } else {
        // curr_termLeft變0時
        curr_principleArr[curr_datespan.sub(curr_termLeft).sub(1)] = 0;
        curr_termdiv = curr_interestArr[curr_datespan.sub(curr_termLeft).sub(1)];
        curr_interestArr[curr_datespan.sub(curr_termLeft).sub(1)] = 0;
    }
    
    // update interestRec
    curr_interestRec.interestArr = curr_interestArr;
    curr_interestRec.principleArr = curr_principleArr;

    return curr_termdiv;
  }
  
  // _amount是本期廠商所支付的利息
  function allocateDividend (uint _loan_id, uint _class, uint _amount, uint _term)
    public
    onlyPlatform
  {
    uint curr_principle = getClassPrincipleNotPaid(_loan_id, _class);

    for (uint j=0; j<trancheInvestor[_loan_id][_class].length; j++) {
        address investor = trancheGetInvestor(_loan_id, _class, j);
        uint investorCredit = investorTranche[investor][_loan_id][_class].amount;
        uint curr_inv_payback = _amount.mul(investorCredit).div(curr_principle);
        investorTranche[investor][_loan_id][_class].dividendIncome[_term] = curr_inv_payback;
    }
  }

  // 換端需先分割本金部分及利息部分，而這裡吃的_amount為本金部分，不讓使用者輸入大於應還的值
  function payback (uint _loan_id, uint _amount)
    public
    onlyPlatform
    termEnough(_loan_id)
  {
    // uint amount = _amount.mul(decimals);
    uint amount = _amount;

    // 將class abc的第一期principle加起來
    // 這裡只是為了拿到curr term(還到第幾期) ,abc都一樣
    InterestRec memory curr_interestRec = interestRecMapping[_loan_id][1];
    uint curr_term = curr_interestRec.dateSpan.sub(curr_interestRec.termLeft);

    // 當期應還本金
    uint curr_PriPayable = getTermPriPayable(_loan_id, curr_term);

    // 1. amount 大於termPayable, 多還本金  
    // 3. amount小等於, 將未還本金計入下次償還
    if (amount > curr_PriPayable) {
        normalPayback(_loan_id, curr_PriPayable);
        earlyPayback(_loan_id, amount.sub(curr_PriPayable));
    }  else {
        normalPayback(_loan_id, amount);
    }
    
  }
  
  // 正常歸還本金（少於每月應還也使用這個function），每人歸還金額為此loan_id總投資金額的佔比
  function normalPayback (uint _loan_id, uint _amount)
    public 
    onlyPlatform
    returns
    (bool)
  { 
    // uint curr_payback = _amount.mul(decimals);
    uint curr_payback = _amount;
    
    // loan_id class A, B, C的債權總金額
    uint total = getTotalPrincipleNotPaid(_loan_id);
    
    // iterate 三層並依據投資佔比分配payback
    for (uint i=1; i<4; i++){
        // require (certificateMapping[_loan_id][i].state == State.ended);
        // iterate 所有投資人
        for (uint j=0; j<trancheInvestor[_loan_id][i].length; j++) {
            address investor = trancheGetInvestor(_loan_id, i, j);
            uint investorCredit = investorTranche[investor][_loan_id][i].amount;
            uint curr_inv_payback = curr_payback.mul(investorCredit).div(total);
            investorTranche[investor][_loan_id][i].amount = investorCredit.sub(curr_inv_payback);
            // curr_payback_left = curr_payback_left.sub(curr_inv_payback);
        }
        
        InterestRec storage curr_interestRec = interestRecMapping[_loan_id][i];

        // 更新termLeft(期數減一)及interest arr的值（分配完歸零）
        uint classPrincipleNotPaid = getClassPrincipleNotPaid(_loan_id, i);
        uint currIntPayable = updateInterestArr(_loan_id, i, classPrincipleNotPaid);
        
        // 分配利息
        allocateDividend(_loan_id, i, currIntPayable, curr_interestRec.dateSpan.sub(curr_interestRec.termLeft).sub(1));

    }
    
    // emit NormalPayback(curr_payback_left, _loan_id);
    return true;
  } 
  
  // 更新本金（1. 還超過每月應還，將多餘將的的金額從從本金扣除，call earlyPayback 2. 還低於每月應每月應還還，少的金額要繼續滾利息）
  // 呼叫情境: 假設當期本金加利息廠商須還5114，而廠商還了6000，則886便為多餘本金(其中可能5%平台會收走)，因此實際只有840被帶入earlypayback
  // 提前歸還本金，從A開始還本金
  function earlyPayback (uint _loan_id, uint _amount)
    public 
    onlyPlatform
    returns
    (uint)
  { 
    uint amount = _amount;
    
    // error handling
    uint totalPrinciple = getTotalPrincipleNotPaid(_loan_id);
    if (amount > totalPrinciple) {
        amount = totalPrinciple;
    }
    
    // 由A -> C 檢查是否還有尚未還清的
    for (uint i=1;i<4;i++) {
        if (amount == 0 ) break;
        
        // 檢查還完分券等級class後是否有剩餘
        // left == 0的情況為amount不夠還或這等級已還清;
        uint left = classPayback(_loan_id, i, amount);
        // 等級class還有多少本金未償還
        uint classPrincipleNotPaid = getClassPrincipleNotPaid(_loan_id, i);
        
        if (left == 0 && classPrincipleNotPaid == 0) {
            // 等級i已經還清的情況，因此開始還下一個等級
            continue;
        } else if (left == 0 && classPrincipleNotPaid > 0){
            // 不夠還，下次還要繼續還這等級
            amount = 0;
            
            // 更新interstArr（償還部分本金）
            earlyUpdateInterestArr(_loan_id, i, classPrincipleNotPaid);

            break;
        } else {
            // 一次還玩等級i，用剩下的開始還等級i+1
            amount = left;
            
            // 更新interstArr(分券等級i的本金全部償還完)
            earlyUpdateInterestArr(_loan_id, i, 0);

            continue;
        }
        
    }
            
    emit EarlyPayback(amount, _loan_id);
    return 0;
  }
  
  function classPayback (uint _loan_id, uint _class, uint _amount)
    public 
    onlyPlatform    
    returns
    (uint)
  {
    // require (certificateMapping[_loan_id][_class].state == State.ended);
    
    // 取得_class未還清的金額
    uint classPrincipleNotPaid = getClassPrincipleNotPaid(_loan_id, _class);
    
    // 等級_class以償還
    if (classPrincipleNotPaid == 0) return 0;
    
    // uint curr_payback = _amount.mul(decimals);
    uint curr_payback = _amount;
    
    // 根據loan_id來得到分券等級_class的持有人數目
    uint loanCount = trancheInvestor[_loan_id][_class].length;
    
    // 檢查這次還錢有沒有大於總欠金額，若大於則會進入下個class
    if (curr_payback > classPrincipleNotPaid) {
        for (uint j=0; j < loanCount; j++) {
            address investor = trancheGetInvestor(_loan_id, _class, j);
            // 投資人債權歸0
            investorTranche[investor][_loan_id][_class].amount = 0;
        }
        return curr_payback.sub(classPrincipleNotPaid);
    } else {
        // 這層class還不完，分配給投資人
        for (uint j=0; j < loanCount; j++) {
            // 投資人
            address investor = trancheGetInvestor(_loan_id, _class, j);
            // 投資人債權金額
            uint investorCredit = investorTranche[investor][_loan_id][_class].amount;
            // 償還投資人金額->curr_payback乘以投資金額佔總投資金額比
            uint curr_inv_payback = curr_payback.mul(investorCredit).div(classPrincipleNotPaid);
    
            investorTranche[investor][_loan_id][_class].amount = investorCredit.sub(curr_inv_payback);
        }
        return 0;
    }
        
  }
  
  // 當廠商本期償還金額小於該期應付利息
  function paybackDividend (uint _loan_id, uint _amount)
    public 
    onlyPlatform
  {
    // uint amount = _amount.mul(decimals);
    uint amount = _amount;

    
    InterestRec memory interestRecForTerm = interestRecMapping[_loan_id][1];
    uint curr_term = interestRecForTerm.dateSpan.sub(interestRecForTerm.termLeft);

    uint addToPrinciple = getTermIntPayable(_loan_id, curr_term).sub(amount);
    
    uint[4] memory uintArr = [
        getInterestArrValue(_loan_id, 1, curr_term),
        getInterestArrValue(_loan_id, 1, curr_term),
        getInterestArrValue(_loan_id, 3, curr_term),
        getTermIntPayable(_loan_id, curr_term)
    ];
    // uint classNumerA = getInterestArrValue(_loan_id, 1, curr_term);
    // uint classNumerB = getInterestArrValue(_loan_id, 2, curr_term);
    // uint classNumerC = getInterestArrValue(_loan_id, 3, curr_term);
    // uint base = classNumerA.add(classNumerB).add(classNumerC);

    // 償還金額(利息)先分給投資人
    for (uint i=1; i<4; i++) {
        // 就算還玩期數也要減一
        if (getClassPrincipleNotPaid(_loan_id, i) == 0) {
            InterestRec storage curr_interestRec = interestRecMapping[_loan_id][i];
            curr_interestRec.termLeft = curr_interestRec.termLeft.sub(1);
            continue;
        }

        uint currInt;
        uint currAddtoPrinciple;
        // 不同class會有不同佔比，在這裡計算每個class佔比
        if (i == 1) {
            currInt = amount.mul(uintArr[0]).div(uintArr[3]);
            currAddtoPrinciple = addToPrinciple.mul(uintArr[0]).div(uintArr[3]);
        } else if (i == 2) {
            currInt = amount.mul(uintArr[1]).div(uintArr[3]);
            currAddtoPrinciple = addToPrinciple.mul(uintArr[1]).div(uintArr[3]);
        } else if (i == 3) {
            currInt = amount.mul(uintArr[2]).div(uintArr[3]);
            currAddtoPrinciple = addToPrinciple.mul(uintArr[2]).div(uintArr[3]);
        }
        // 在投資人tranche上紀錄該期獲得多少利息
        allocateDividend(_loan_id, i, currInt, curr_term);
        
        // 因為沒有還到該期應還利息，因此少的利息要加入本金計算下期循環利率
        addInvestorPrinciple(_loan_id, i, currAddtoPrinciple);

        // 更新下期應付利息及本金
        updateInterestArr(_loan_id, i, getClassPrincipleNotPaid(_loan_id, i));
        
    }
    
  }
  
  function addInvestorPrinciple (uint _loan_id, uint _class, uint _amount)
    internal
    onlyPlatform
  {
    // 先將應付利息減去廠商所償還，得到的數字要平分給投資人，以繼續循環利率
    uint classPrincipleNotPaid = getClassPrincipleNotPaid(_loan_id, _class);
    
    for (uint j=0; j<trancheInvestor[_loan_id][_class].length; j++) {
        address investor = trancheGetInvestor(_loan_id, _class, j);
        uint investorCredit = investorTranche[investor][_loan_id][_class].amount;
        uint curr_inv_payback = _amount.mul(investorCredit).div(classPrincipleNotPaid);
        investorTranche[investor][_loan_id][_class].amount = investorCredit.add(curr_inv_payback);
    }  
    
  }
  
  
  // 還到一半不還，而違約，從C開始減少債權到A
  // 與eralyPayback相同，只是清償方向相反
  function breach (uint _loan_id, uint _amount)
    public 
    onlyPlatform
    returns
    (bool)
  {
    uint amount = _amount;
    // 由C -> A 檢查是否還有尚未還清的
    for (uint i=3;i>0;i--) {
        if (amount == 0 ) break;
        
        uint left = classPayback(amount, _loan_id, i);
        
        if (left == 0 && getClassPrincipleNotPaid(_loan_id, i) == 0) {
            continue;
        } else if (left == 0 && getClassPrincipleNotPaid(_loan_id, i) > 0){
            amount = 0;
            break;
        } else {
            amount = left;
            continue;
        }
    }
    
    emit Breach(_amount, _loan_id);
    return true;     
  }
  
  

  
  
  



}