from django.db import models
from django.db.models.fields import BooleanField
from django.contrib.auth.models import User
import datetime

RATE_CHOICES = (
    (6, '6%'),
    (8, '8%'),
    (10,'10%'),
    (12,'12%'),
)
STATE_CHOICES = (
    (1, '憑證未發出'), ## for orders
    (2, '訂單準備中'),## for orders
    (3, '訂單已完成'),## for orders
    (4, '違約'),  ## for all type
    (5, '未驗證'), ## for verification
    (6, '完成驗證'),## for verification
    (7, '尚未付款'), ## for account payable/receivable
    (8, '發出應付'), ## for account payable/receivable
    (9, '帳款已結清') ## for account payable/receivable
)

LOAN_STATE = (
    (1, '融資中'),
    (2, '融資成功'),
    (3, '融資失敗'),
    (4, '融資結束'),
    (5, '違約')
)
CLASS_CHOICES = (
    (1, '應收'),
    (2, '訂單'),
    (3, '移轉'),
    (4, '貸款'),
    (5, '驗證抵押')
) 
CLASS_CHOICES_2000 = (
    (1, '應收'),
    (2, '訂單'),
    (3, '存貨'),
)
TRANCHE_CHOICES =(
    (1, 'A'),
    (2, 'B'),
    (3, 'C')
)
ARA_CHOICES = (
    (1,'出售中'),
    (2,'成交'),
)
class Invest_user(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) ## user foriegn key
    public_address = models.CharField(max_length=42) ##公鑰
    amount_865 = models.DecimalField(max_digits=12, decimal_places=0, null=True) #核心企業平台幣數量

class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) ## user foriegn key
    uni_num = models.CharField(max_length=100) ##統一編號
    public_address = models.CharField(max_length=42) ##公鑰
    core = models.BooleanField() #是否為核心企業
    amount_a = models.DecimalField(max_digits=12, decimal_places=1, null=True) #核心企業token_A數量
    amount_865 = models.DecimalField(max_digits=12, decimal_places=0, null=True) #核心企業平台幣數量
    create_time = models.DateTimeField(auto_now_add= True) #進入時間
    contract_address = models.CharField(max_length=42,null=True,blank=True) ##合約地址
    company_type = models.CharField(max_length=42,null=True,blank=True) #行業別
    capital = models.DecimalField(max_digits=12, decimal_places=0, null=True) #資本額
    chairman = models.CharField(max_length=42,null=True,blank=True) #董事長
    company_location =  models.CharField(max_length=42,null=True,blank=True) #公司地址
    supervisor = models.CharField(max_length=42,null=True,blank=True) #登記機關
    establish_date = models.CharField(max_length=42,null=True,blank=True) #成立日期
    responsible_person = models.CharField(max_length=42,null=True,blank=True) #負責人
    image = models.ImageField(upload_to='static/image/', blank=True, null=True)  ##logo
    


class Deposit(models.Model):
    deposit_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='deposit_company')
    deposit_amount = models.CharField(max_length=100, null=True, blank=True)  ## 因為使用者可能存超多錢，所已用string存，取用時要先cast成int
    deposit_time = models.DateTimeField(default=datetime.datetime.now) #進入時間
    transactionHash = models.CharField(max_length=66, null=True, blank=True)


class TokenA(models.Model):
    tokenA_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='tokenA_company')
    tokenA_amount = models.CharField(max_length=100, null=True, blank=True)  ## 因為使用者可能存超多錢，所已用string存，取用時要先cast成int
    tokenA_time = models.DateTimeField(default=datetime.datetime.now) #進入時間
    transactionHash = models.CharField(max_length=66, null=True, blank=True)

## temporary for testing 
class Company_orders(models.Model):
    ##设置related_name参数来覆盖名字entry_set以起到相同的作用
    ##範例 c = Company.objects.get(id=1)
    ##    c.send_company.all() returns all order objects related to Company.
    send_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='send_company') ## 一個發出Company 對多 orders
    receive_compamy = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='receive_comapny') ## 一個接收Company 對多 orders
    product  = models.CharField(max_length=40) ##訂單項目
    price = models.IntegerField(null=True, blank=True) ##訂單價格
    start_date = models.DateField(auto_now_add = True ,null=True) ## 發起時間
    end_date = models.DateField() ## 結束時間
    state = models.IntegerField(choices=STATE_CHOICES, default=1) ##狀態
    rate = models.IntegerField(choices=RATE_CHOICES, null=True,  blank=True) ##利息
    transactionHash = models.CharField(max_length=66, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank = True) ##數量 onlyfor 驗證
    class_type = models.IntegerField(choices=CLASS_CHOICES_2000, null=True, blank=True) ##tokenB (應收, 訂單, 移轉, 貸款)



# loan (address _loaner, uint256 _amount, uint16 _class, uint _id, uint256 _interest, uint256 _date)
# bToC (address _from, address _to, uint256 _amount, uint256 _interest, uint _id, uint16 _class, uint16 c_class, uint256 _date)
class TokenB(models.Model):
    amount = models.CharField(max_length=100, null=True, blank=True) ##tokenB金額
    class_type = models.IntegerField(choices=CLASS_CHOICES, null=True, blank=True) ##tokenB (應收, 訂單, 移轉, 貸款)
    token_id = models.CharField(max_length=100, null=True, blank=True) ## tokenB的id, 因為太長所以用charfield
    interest = models.IntegerField(null=True, blank=True)
    date_span = models.IntegerField(null=True, blank=True)
    transfer_count = models.IntegerField(null=True, blank=True) ##移轉次數

    initial_order = models.ForeignKey(Company_orders, on_delete=models.CASCADE, related_name='initial_order', null=True,  blank=True) #指向最一開始的訂單
    pre_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='pre_company', null=True,  blank=True)
    curr_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='curr_company', null=True,  blank=True)
    transactionHash = models.CharField(max_length=66, null=True, blank=True)

    tokenB_balance = models.DecimalField(max_digits=12, decimal_places=0 , default=0, blank=True)##tokenB可使用餘額
    already_transfer = models.DecimalField(max_digits=12, decimal_places=0,  default=0,  blank=True)## 已移轉amount
    already_loan = models.DecimalField(max_digits=12, decimal_places=0 , default=0,   blank=True)## 已借款amount

    pmt = models.IntegerField(null=True, blank=True)

    state = models.IntegerField(choices=LOAN_STATE, null=True, blank=True)

# loancertificate資料表
# mintCertificate (_loan_id, _borrow_company, _principle, _interest, _datespan, _class)
class LoanCertificate(models.Model):
    tokenB  = models.ForeignKey(TokenB,on_delete=models.CASCADE ,related_name='from_tokenB', null=True,  blank=True) ## 來自哪個tokenB 'kevin'
    loan_id = models.CharField(max_length=100, null=True, blank=True) ## tokenB的id, 因為太長所以用charfield
    loan_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='loan_company', null=True,  blank=True) ## 借錢企業
    principle = models.CharField(max_length=100, null=True, blank=True) ## 融資多少錢
    avail_amount = models.CharField(max_length=100, null=True, blank=True) 
    interest = models.IntegerField(null=True, blank=True)
    date_span = models.IntegerField(null=True, blank=True) ## 這裡要紀錄期數（單位為月）
    curr_span = models.IntegerField(null=True, blank=True) ## 剩餘期數
    riskClass = models.IntegerField(choices=TRANCHE_CHOICES, null=True, blank=True)  ## 分券種類
    transactionHash = models.CharField(max_length=66, null=True, blank=True)

# tranche資料表

class Tranche(models.Model):
    # (address _investor, uint _loan_id, uint _class, uint _amount)
    loanCertificate = models.ForeignKey(LoanCertificate,on_delete=models.CASCADE ,related_name='from_certificate', null=True,  blank=True) ##來自哪比loan_certificate 'kevin'
    investor = models.ForeignKey(User,on_delete=models.CASCADE ,related_name='investor', null=True,  blank=True)
    loan_id = models.CharField(max_length=100, null=True, blank=True) ## tokenB的id, 因為太長所以用charfield
    riskClass = models.IntegerField(choices=TRANCHE_CHOICES, null=True, blank=True)  ## 分券種類
    amount = models.CharField(max_length=100, null=True, blank=True) ##tokenB金額
    accu_earning = models.CharField(max_length=100, null=True, default='0') ## 融資多少錢



# investorDividend 資料表
class LoanPayable(models.Model):
    tokenB = models.ForeignKey(TokenB, on_delete=models.CASCADE ,related_name='loan_id', null=True,  blank=True)
    term_principle = models.TextField(null=True, blank=True)
    term_interest = models.TextField(null=True, blank=True)
    term = models.IntegerField(null=True, blank=True)


class Acc_rec_for_sale(models.Model):
    tokenB = models.ForeignKey(TokenB, on_delete=models.CASCADE ,related_name='acc_recB_id', null=True,  blank=True)
    opening_price = models.IntegerField(null=True, blank=True)
    core_company = models.ForeignKey(Company, on_delete=models.CASCADE ,related_name='core_company', null=True,  blank=True)
    pre_own = models.ForeignKey(Company, on_delete=models.CASCADE ,related_name='pre_own', null=True,  blank=True)
    state =  models.IntegerField(choices=ARA_CHOICES, null=True, blank=True)

class Payback_record(models.Model):
    tokenB = models.ForeignKey(TokenB, on_delete=models.CASCADE ,related_name='payback_loan_id', null=True,  blank=True)
    term = models.IntegerField(null=True, blank=True) ## 還錢的期數
    amount = models.TextField(null=True, blank=True)  ## 還錢的金額
