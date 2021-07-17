from django.db import models
from django.db.models.fields import BooleanField
from django.contrib.auth.models import User

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

## temporary for testing 
class Company_orders(models.Model):
    ##设置related_name参数来覆盖名字entry_set以起到相同的作用
    ##範例 c = Company.objects.get(id=1)
    ##    c.send_company.all() returns all order objects related to Company.
    send_company = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='send_company') ## 一個發出Company 對多 orders
    receive_compamy = models.ForeignKey(Company,on_delete=models.CASCADE ,related_name='receive_comapny') ## 一個接收Company 對多 orders
    product  = models.CharField(max_length=40) ##訂單項目
    price = models.DecimalField(max_digits=12, decimal_places=1) ##訂單價格
    start_date = models.DateField(auto_now_add = True ,null=True) ## 發起時間
    end_date = models.DateField() ## 結束時間
    state = models.IntegerField(choices=STATE_CHOICES, default=1) ##狀態
    rate = models.FloatField(choices=RATE_CHOICES, null=True,  blank=True) ##利息
    tokenB_balance = models.DecimalField(max_digits=12, decimal_places=0 , null=True, blank=True)##tokenB可使用餘額
    already_transfer = models.DecimalField(max_digits=12, decimal_places=0,  null=True,  blank=True)## 已移轉amount
    already_loan = models.DecimalField(max_digits=12, decimal_places=0 , null=True,   blank=True)## 已借款amount



