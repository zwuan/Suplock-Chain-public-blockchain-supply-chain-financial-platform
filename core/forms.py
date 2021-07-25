from django import forms
from .models import Company
from django.contrib.auth.models import User
from .fields import ListTextWidget

RATE_CHOICES = (
    (3, '3%'),
    (4, '4%'),
    (5, '5%'),
    (6, '6%'),
    (7, '7%'),
    (8, '8%'),
    (9, '9%'),
    (10,'10%'),
    (11,'11%'),
    (12,'12%'),
    (13,'13%'),
)
##註冊表單  
class user_register(forms.Form):
    username = forms.CharField()
    uni_num = forms.CharField()
    email = forms.CharField()
    password = forms.CharField()
    _password = forms.CharField()
    address = forms.CharField()
    
##登入表單
class user_login(forms.Form):
    username = forms.CharField()
    password = forms.CharField()

## 課金表單
class deposit(forms.Form):
    amount_a = forms.DecimalField()

## 發訂單表單 (token A to B)
class set_order_rate(forms.Form):
    orders_id = forms.CharField()
    rec_company_name = forms.CharField()
    rec_com_address = forms.CharField()
    rate = forms.ChoiceField(choices = RATE_CHOICES ,widget = forms.Select ,required=True)


## loan表單
#(address _loaner, uint256 _amount, uint16 _class, uint _id, uint256 _interest, uint256 _date)
class set_loan(forms.Form):
    optype = forms.CharField() # use operation type to decide which view to pass this form 
    orders_interest = forms.CharField()
    loan_TOKENB_id = forms.CharField(required=True)
    orders_id = forms.CharField()
    orders_from_company_name = forms.CharField()
    orders_price = forms.CharField()
    
# 移轉表單
class companyListForm(forms.Form):
    optype = forms.CharField(required=True)
    bToC_TOKENB_id = forms.CharField(required=True)
    bToC_interest = forms.CharField(required=True)
    bToC_id = forms.CharField(required=True)
    bToC_from_company_name = forms.CharField(required=True)
    bToC_to_company_name = forms.CharField(required=True)
    bToC_price = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        _company_list = kwargs.pop('data_list', None)
        super(companyListForm, self).__init__(*args, **kwargs)
        # the "name" parameter will allow you to use the same widget more than once in the same
        # form, not setting this parameter differently will cuse all inputs display the
        # same list.
        self.fields['bToC_to_company_name'].widget = ListTextWidget(data_list=_company_list, name='bToC_to_company_name')





