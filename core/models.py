from django.db import models
from django.db.models.fields import BooleanField
from django.contrib.auth.models import User
import datetime

RATE_CHOICES = (
    (0.03, '3%'),
    (0.04, '4%'),
    (0.05, '5%'),
    (0.06, '6%'),
    (0.07, '7%'),
    (0.08, '8%'),
    (0.09, '9%'),
    (0.10,'10%'),
    (0.11,'11%'),
    (0.12,'12%'),
    (0.13,'13%'),
)
STATE_CHOICES = (
    (1, '憑證未發出'),
    (2, '訂單準備中'),
    (3, '訂單已完成'),
    (4, '違約'),
    (5, '未驗證'),
    (6, '已完成驗證')
)
CLASS_CHOICES = (
    (1, '應收'),
    (2, '訂單'),
    (3, '移轉'),
    (4, '貸款')
)

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
    rate = models.FloatField(choices=RATE_CHOICES, null=True,  blank=True) ##利息
    transactionHash = models.CharField(max_length=66, null=True, blank=True)


# loan (address _loaner, uint256 _amount, uint16 _class, uint _id, uint256 _interest, uint256 _date)
# bToC (address _from, address _to, uint256 _amount, uint256 _interest, uint _id, uint16 _class, uint16 c_class, uint256 _date)
class TokenB(models.Model):
    amount = models.CharField(max_length=100, null=True, blank=True) ##tokenB金額
    class_type = models.IntegerField(choices=CLASS_CHOICES, null=True, blank=True) ##tokenB (應收, 訂單, 移轉, 貸款)
    token_id = models.CharField(max_length=100, null=True, blank=True) ## tokenB的id, 因為太長所以用charfield
    interest = models.FloatField(null=True, blank=True)
    date_span = models.IntegerField(null=True, blank=True)
    transfer_count = models.IntegerField(null=True, blank=True) ##移轉次數

    initial_order = models.ForeignKey(Company_orders, on_delete=models.CASCADE, related_name='initial_order', null=True,  blank=True) #指向最一開始的訂單
    pre_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='pre_company', null=True,  blank=True)
    curr_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='curr_company', null=True,  blank=True)
    transactionHash = models.CharField(max_length=66, null=True, blank=True)

    tokenB_balance = models.DecimalField(max_digits=12, decimal_places=0 , default=0, blank=True)##tokenB可使用餘額
    already_transfer = models.DecimalField(max_digits=12, decimal_places=0,  default=0,  blank=True)## 已移轉amount
    already_loan = models.DecimalField(max_digits=12, decimal_places=0 , default=0,   blank=True)## 已借款amount




