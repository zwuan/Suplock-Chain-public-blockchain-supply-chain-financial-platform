from django import forms
from web3 import exceptions
from django.shortcuts import render
from django.http import HttpResponse 
from web3 import Web3
import web3
from .models import Company, Company_orders
from core.solidity.abi import abi
from core.solidity.erc865_abi import erc865_abi
from core.solidity.bytecode import bytecode
from core.solidity.erc865_bytecode import erc865_bytecode
import json
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .forms import user_login, user_register, deposit, set_order_rate, companyListForm, set_loan
from django.contrib import auth
from django.shortcuts import render ,redirect
from django.urls import reverse_lazy
import time
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.http import JsonResponse
from django.template.loader import get_template
import urllib
import hashlib
import datetime
from collections import OrderedDict
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.template import loader
from django.db.models import Q
#預留空位給其他testnet
provider_rpc = {
    'development': 'https://ropsten.infura.io/v3/396094052a124676a222214bd8a3bab8',
} #設定節點
w3 = Web3(Web3.HTTPProvider(provider_rpc['development'])) #將web3連上節點，這邊用測試的Ropsten
#平台帳號資訊
account_from = {
    'private_key': '6af669c4f0c75961cd006a970c8839ea122612c85305ff2da1edb3eff39ffaf7',
    'address': '0xA3E58464444bC66b5bb7FB8e76D7F4fDE52126F2',
}
fee = 30 ##手續費
DECIMALS = 10**18
erc865_contract_address = '0xcb8565c6eeb98fc8c441b5e07c1d6e7cb200b277'
erc865_contract_address = w3.toChecksumAddress(erc865_contract_address)
# 廠商登入/註冊（template有兩個form，而且user&company分開，需要兩個modelForm，因此用formView太複雜）
class login_company(generic.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'login_company.html')

    def post(self, request, *args, **kwargs):
        if 'log_in' in request.POST: ## 登入表單
            form = user_login(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = auth.authenticate(username=username, password=password)
            if user and user.is_active:
                auth.login(request, user)
                return redirect(reverse_lazy('company_index'))
                

        if 'register' in request.POST: ##註冊表單
            form = user_register(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                email = form.cleaned_data['email']
                user = User.objects.create(
                        username=username,
                        password=make_password(password), # 密碼加密
                        email = email,
                    )
                uni_num = form.cleaned_data['uni_num']
                public_address = form.cleaned_data['address']
                company = Company.objects.create(
                        uni_num = uni_num,
                        public_address = public_address,
                        core = False,
                        amount_a = 0,
                        amount_865 = 0,
                        user = user,
                )
            return render(request, 'login_company.html') 
        return render(request, 'login_company.html') 

##廠商首頁
class company_index(generic.View):
    ## get頁面 
    def get(self, request, *args, **kwargs):
        context = {}
        if request.user.is_authenticated:
            if 'fallback' in request.session.keys():
                del request.session['fallback']
            user = request.user
            company = Company.objects.filter(user = user)
            context = {'msg':company}
            return render(request, 'company_index.html',context)
        else:
            return redirect(reverse_lazy('login_company'))
    ##存入保證金(平台幣)
    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            form = deposit(request.POST)
            company = Company.objects.filter(user = request.user)[0]
            deploy_company = Company.objects.filter(id = company.id)
            if form.is_valid():
                core_address = company.public_address ##公司錢包地址
                core_address = Web3.toChecksumAddress(core_address) #轉換成checksum address
                check_enough_balalce = call_ERC865(core_address)  / DECIMALS ## 先 view 餘額
                content = {}
                add_amount = int(form.cleaned_data['amount_a'] )
                if check_enough_balalce < add_amount:
                    request.session['fallback'] = '餘額不足請儲值'
                    return redirect(reverse_lazy('add_erc865')) ##導回儲值頁
                add_amount_a =  add_amount * 10 ## 儲值金額
                transfer_event = transfer_865(core_address, add_amount*DECIMALS , fee*DECIMALS)
                actual_payment_on_chain = transfer_event['value'] / DECIMALS
                user_ERC865_balance = call_ERC865(core_address)  / DECIMALS## 查看廠商的865餘額
                deploy_company.update(amount_865 = user_ERC865_balance) ##更新資料庫865金額
                ##如果不是核心 deploy新合約
                if  not company.core:
                    contract_addr = deploy_contract(core_address, add_amount_a)['contractAddress'] ##取得部署的合約地址
                    construct_amount = call_tokenA(contract_addr,core_address) ##查看首次部署的tokenA數量
                    deploy_company.update(amount_a = construct_amount, core = True ,contract_address = contract_addr) ##修改資料庫
                    content = {"address":contract_addr, "mintA": construct_amount, 'company':company} ##顯示到前端
                #是核心 mint & 更新資料庫
                else:
                    tx_receipt = mint_tokenA(company.contract_address, add_amount_a)  ##交易資料
                    txhash = tx_receipt['transactionHash'].hex()
                    logs = get_tokenA_event(company.contract_address, tx_receipt)  ## log
                    deposit_amount = logs[0]['args']['amount'] ##確認數量
                    all_deposit_amount = call_tokenA(company.contract_address,core_address) ## view mapping tokenA
                    deploy_company.update(amount_a = all_deposit_amount) ##更新資料庫
                    content = {"address":txhash, "mintA": deposit_amount, 'company':company,'payment':actual_payment_on_chain} ##顯示到前端
                return render(request, 'temp.html', content)

## 公司訂單頁面
@method_decorator(login_required, name='dispatch')
class company_order(generic.ListView):
    model = Company_orders
    template_name = 'company_orders.html'
    context_object_name = 'orders'
    paginate_by = 6
    ##回傳每筆訂單
    def get_queryset(self):
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        return  company.send_company.all()
    ## 回傳Comoany 
    def get_context_data(self, **kwargs) :
        form = set_order_rate()
        company_addr_dict = {}
        rec_com_list = []
        context =  super(company_order,self).get_context_data(**kwargs)
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        all_company = company.send_company.all()
        for rec_com in all_company:
            rec_com_list.append(rec_com.receive_compamy)
        for c in rec_com_list:
            company_addr_dict[c.user.username] = c.public_address
        context['company_addr_dict'] = json.dumps(company_addr_dict)
        context['form'] = form
        return context
    ## Do token A to b
    def post(self, request, *args, **kwargs):
        form = set_order_rate(request.POST)
        if form.is_valid():
            orders_id = form.cleaned_data['orders_id'] ##訂單編號
            rec_com_address = form.cleaned_data['rec_com_address'] ##接收的公司的地址 
            rec_com_address = Web3.toChecksumAddress(rec_com_address) 
            rate = float(form.cleaned_data['rate']) ## 訂單發出可貸款利率
            user = self.request.user ##請求的使用者
            order = Company_orders.objects.filter(id = orders_id)[0] ##找到資料庫的這筆訂單
            order_for_update = Company_orders.objects.filter(id = orders_id) ## update 只支援queryset
            amount = int(order.price) ##訂單價值
            end = order.end_date ## 結束日
            now = datetime.date.today() ## 透過平台的發訂單日
            date_span = end - now ## 時間段
            date_span = date_span.days 
            company = Company.objects.filter(user = user)[0] ##發出的公司
            company_for_update = Company.objects.filter(user = user)
            contract_address = company.contract_address ##發出的公司合約地址
            core_address = Web3.toChecksumAddress(company.public_address) ## 核心 公鑰 checksumaddresss
            token_A_to_B_event = token_A_to_B(contract_address, rec_com_address, amount, int(rate*DECIMALS), date_span, 1) ##訂單 class = 1 上鏈
            order_for_update.update(rate = rate , start_date = datetime.date.today(), state = 2, tokenB_balance = amount) ##更新設定利率 起始時間 狀態變為準備中 新增可使用tokenB
            core_amount_a = call_tokenA(contract_address, core_address) ## 拿到最新的tokenA數量
            company_for_update.update(amount_a = core_amount_a) ##更新資料庫
            log_amount, log_rate, log_receiver =  token_A_to_B_event['amount'], token_A_to_B_event['interest']/DECIMALS, token_A_to_B_event['receiver']
            context = {"log_amount":log_amount,"log_rate":log_rate,"log_receiver":log_receiver}
            return render(request, 'company_orders.html', context)
        
    
   
@method_decorator(login_required, name='dispatch')
class company_order_rec(generic.ListView):
    model = Company_orders
    template_name = 'company_orders_rec.html'
    context_object_name = 'rec_orders'
    paginate_by = 6
    def get_queryset(self):
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        return  company.receive_comapny.filter(Q(state =2) | Q(state =3) |Q(state = 4))   ##收到 顯示除了憑證未發出的所有訂單

    def get_context_data(self, **kwargs):
        _company_list = []
        context =  super(company_order_rec,self).get_context_data(**kwargs)
        user = self.request.user
        company_list = list(Company.objects.filter(~Q(user = user)))
        for com in company_list:
            _company_list.append(com.user.username)
        form = companyListForm(data_list = _company_list)
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        allUser = auth.get_user_model() # return all user
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        contract_address = company.contract_address ##發出的公司合約地址

        optype = request.POST['optype'] # optype decides which form to catch
        if optype == 'loan':
            form = set_loan(request.POST)
        elif optype =='bToC':
            form = companyListForm(request.POST)

        if form.is_valid():
            if form.cleaned_data['optype'] == 'loan':
                orders_id = int(form.cleaned_data['orders_id'])
                order = Company_orders.objects.filter(id = orders_id)[0] ##找到資料庫的這筆訂單
                now = datetime.date.today() ## 透過平台融資日
                end = order.end_date ## 結束日
                date_span = end - now ## 時間段
                date_span = date_span.days

                ### contract manipulation
                _loaner = Web3.toChecksumAddress(company.public_address)
                _amount = int(form.cleaned_data['orders_price'])
                _class = 2 #代表為訂單
                _id = orders_id
                _interest = int(form.cleaned_data['orders_interest'][:-1])
                _date = date_span
                try: 
                    tx_receipt = loan(contract_address, _loaner, _amount ,_class, _id, _interest, _date)
                except exceptions.SolidityError as error:
                    print(error)
                Core = w3.eth.contract(contract_address, abi=abi)
                txhash = tx_receipt['transactionHash'].hex()
                logs = Core.events.loan_event().processReceipt(tx_receipt) #拿log
                event = logs[0]['args']
                ### 寫一個tokenB的table?
                # order.update(rate = rate , start_date = datetime.date.today(), state = 2, tokenB_balance = amount) ##更新設定利率 起始時間 狀態變為準備中
                print(event)

            # return HttpResponse('good')
            elif form.cleaned_data['optype'] == 'bToC':
                bToC_id = int(form.cleaned_data['bToC_id'])
                order = Company_orders.objects.filter(id = bToC_id)[0] ##找到資料庫的這筆訂單
                now = datetime.date.today() ## 透過平台融資日
                end = order.end_date ## 結束日
                date_span = end - now ## 時間段
                date_span = date_span.days
                to_company = form.cleaned_data['bToC_to_company_name'] # 被移轉的公司
                to_company = allUser.objects.filter(username = to_company)[0]

                ### contract manipulation
                _from = Web3.toChecksumAddress(company.public_address)
                _to = Web3.toChecksumAddress(to_company.public_address)
                _interest = form.cleaned_data['bToC_interest']
                _amount = form.cleaned_data['bToC_price']
                _id = bToC_id
                _class = 2
                c_class = 3
                _date = date_span
                try: 
                    tx_receipt = bToC(contract_address, _from, _to ,_amount, _interest, _id, _class, c_class,  _date)
                except exceptions.SolidityError as error:
                    print(error)
                Core = w3.eth.contract(contract_address, abi=abi)
                txhash = tx_receipt['transactionHash'].hex()
                logs = Core.events.loan_event().processReceipt(tx_receipt) #拿log
                event = logs[0]['args']
                pass
                #(address _from, address _to, uint256 _amount, uint256 _interest, uint _id, uint16 _class, uint16 c_class, uint256 _date)
##################我的部分結束########################


class wallet(generic.View):
     def get(self, request, *args, **kwargs):
        return render(request, 'wallet.html')

    


def temp(request):
    return render(request,'temp.html')

##登出
def logout(request):
    auth.logout(request)
    return redirect(reverse_lazy('login_company'))

'''ERC-865 contract manipulate'''


@csrf_exempt
def getAbiBytecode(request):
    # if request.POST:
    context = {'erc865_abi':erc865_abi, 'erc865_contract_addr':erc865_contract_address,'erc865_bytecode':erc865_bytecode}
    return HttpResponse(json.dumps(context), content_type="application/json")

def hello_world(request):
    return render(request, 'hello_world.html')

# 檢查碼演算法
def createCheckValue(data):
    data = OrderedDict(data)
    data = OrderedDict(sorted(data.items()))

    orderedDict = OrderedDict()
    orderedDict['HashKey'] = settings.ECPAY_API_HASH_KEY
    for field in data:
        orderedDict[field] = data[field]
    orderedDict['HashIV'] = settings.ECPAY_API_HASH_IV

    dataList = []
    for k, v in orderedDict.items():
        dataList.append("%s=%s" % (k, v))
    dataStr = u"&".join(dataList)
    
    
    encodeStr = urllib.parse.urlencode({'data': dataStr,})[5:]
    checkValue = hashlib.md5(encodeStr.lower().encode()).hexdigest().upper()

    return checkValue

@csrf_exempt
def buyERC865(request):
    context = {}
    if request.POST:
        payment_data = {
            # === 必填欄位 ===
            # 付款資訊
            "MerchantID": settings.ECPAY_MERCHEAT_ID,
            "ReturnURL": "http://127.0.0.1:8000/payment/backend/return/",
            "ChoosePayment": "ALL",
            "PaymentType": "aio",
            
            # 訂單資訊
            "MerchantTradeNo": hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[0:20], # 訂單號
            "MerchantTradeDate": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), # 訂單建立日期
            
            
            # 商品資訊
            "TotalAmount": request.POST.get('ERC_amount'),
            "TradeDesc": "ecapy 購物商城",
            "ItemName": "林奕辰的engine",

            
            # === 選填欄位 ===
            "CustomField1": request.POST.get('address'),
            "CustomField2": request.POST.get('ERC_address'),
            "OrderResultURL": "http://127.0.0.1:8000/frontend/return/", # 用這個 view 接結果
        }
        print(payment_data)
        # 檢查碼機制，參考 15.檢查碼機制
        payment_data["CheckMacValue"] = createCheckValue(payment_data)
        context.update({
            "ECPAY_API_URL": settings.ECPAY_API_URL,
            "formData": payment_data,
        })
        # print(context)
        # return render(request, "hello_world.html", context)
        return HttpResponse(json.dumps(context), content_type="application/json")


@method_decorator(csrf_exempt, name='dispatch')        
class PaymentReturnView(View):
    def post(self, request, *args, **kwargs):
        context = {}

        # request.POST 就是由綠界回傳的付款結果
        print(request.POST)
        res = request.POST.dict()

        # 根據付款結果做後續處理，EX: 設定訂單為已付款、付款失敗時的處理...等等
        erc_address = w3.toChecksumAddress(res['CustomField2'])
        to_address = w3.toChecksumAddress(res['CustomField1'])
        amount = int(res['TradeAmt'])*DECIMALS

        erc865Contract = w3.eth.contract(address=erc_address, abi=erc865_abi)
        # make transaction
        transaction = erc865Contract.functions.transferFromPlatform(to_address, amount).buildTransaction({  # 測試帳號，將erc20發給他
            'gas':700000,
            'from': account_from['address'],
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        })
        # transaction.update({'gas': appropriate_gas_amount})
        # transaction.update(
        #     {'nonce': w3.eth.get_transaction_count('0x8144749b02BD30885B11c20789F115D58ffC0AED')})

        signed_tx = w3.eth.account.signTransaction(transaction,  account_from['private_key'])

        # get transaction receipt
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash ,timeout=600)
        logs = erc865Contract.events.Transfer().processReceipt(tx_receipt)
        transfer_event = logs[0]['args']

        t = loader.get_template('payment_success.html')
        context.update({ 
            "res": res,
            "receipt": tx_receipt,
            "event":transfer_event,
        })
        return HttpResponse(t.render(context, request))

## 保證金扣款
def transfer_865( _from, _value, fee):
    erc865Contract = w3.eth.contract(address=erc865_contract_address, abi=erc865_abi)
    transaction = erc865Contract.functions.transferToPlatform(_from, _value, fee).buildTransaction({
        'from': account_from['address'],
        'gas': 300000,
        'nonce': w3.eth.getTransactionCount(account_from['address']),
    })
    signed_tx = w3.eth.account.signTransaction(transaction,  account_from['private_key'])
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash,timeout=600)
    logs = erc865Contract.events.Transfer().processReceipt(tx_receipt)
    transfer_event = logs[0]['args']
    return transfer_event

def call_ERC865(_user_address):
    erc865Contract = w3.eth.contract(address = erc865_contract_address,abi=erc865_abi)
    ERC865_balance = erc865Contract.functions.balanceOf(_user_address).call()
    return ERC865_balance

'''core contract manipulate'''
##查看tokenA數量
def call_tokenA(_contract_addr, _core_address):
    Core = w3.eth.contract(_contract_addr,abi=abi)
    tokenA_amount = Core.functions.token_A(_core_address).call()
    return tokenA_amount

##部署核心合約
def deploy_contract(_core_address,_amount):
    # 開始部署合約
    print(f'Attempting to deploy from account: { account_from["address"] }')
    # 設定合約資訊
    Core = w3.eth.contract(abi=abi, bytecode=bytecode)
    # 創建出交易
    construct_txn = Core.constructor(_core_address,_amount).buildTransaction(
        {

            'from': account_from['address'],
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )
    # 簽名
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])

    # transaction送出並且等待回傳
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash,timeout=600)
    return tx_receipt

## 鑄幣(已部署過) (核心合約地址, 儲值金額)
def mint_tokenA(_contract_addr,_amount): 
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    construct_txn = Core.functions.mintTokenA(_amount).buildTransaction(
            {
                'from': account_from['address'],
                'gas':400000,
                'nonce': w3.eth.getTransactionCount(account_from['address']),
            }
    )
    # 簽名
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    # transaction送出並且等待回傳
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash ,timeout=600)
    return tx_receipt


## 儲值tokenA event
def get_tokenA_event(_contract_addr,_receipt):
    Core = w3.eth.contract(address = _contract_addr,abi=abi)
    rich_logs = Core.events.minttokenA_event().processReceipt(_receipt)
    return rich_logs

##核心發出訂單
def token_A_to_B(_contract_addr, _receive_addr ,_amount, _interest, _date, _class):
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    construct_txn = Core.functions.AToB(_receive_addr, _amount, _interest, _date, _class).buildTransaction(
        {
            'from': account_from['address'],
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )
    # 簽名
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    # transaction送出並且等待回傳
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash,timeout=600)
    logs = Core.events.tokenB_event().processReceipt(tx_receipt) #拿log
    token_A_to_B_event = logs[0]['args']
    return token_A_to_B_event


def loan(_contract_addr, _loaner, _amount ,_class, _id, _interest, _date):
#(address _loaner, uint256 _amount, uint16 _class, uint _id, uint256 _interest, uint256 _date)
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    '''

    testnet version

    '''
    # construct_txn = Core.functions.loan(_loaner, _amount, _class, _id, _interest, _date).buildTransaction(
    #     {
    #         'from': account_from['address'],
    #         'nonce': w3.eth.getTransactionCount(account_from['address']),
    #     }
    # )
    # # 簽名
    # tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    # # transaction送出並且等待回傳
    # tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)

    '''
    
    ganache version
    
    '''
    construct_txn = Core.functions.loan(_loaner, _amount, _class, _id, _interest, _date).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(construct_txn)
    return tx_receipt

def bToC(_contract_addr, _from, _to ,_amount, _interest, _id, _class, c_class,  _date):
    # (address _from, address _to, uint256 _amount, uint256 _interest, uint _id, uint16 _class, uint16 c_class, uint256 _date)
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    '''

    testnet version

    '''
    # construct_txn = Core.functions.BtoC(_from, _to ,_amount, _interest, _id, _class, c_class,  _date).buildTransaction(
    #     {
    #         'from': account_from['address'],
    #         'nonce': w3.eth.getTransactionCount(account_from['address']),
    #     }
    # )
    # # 簽名
    # tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    # # transaction送出並且等待回傳
    # tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)

    '''
    
    ganache version
    
    '''
    construct_txn = Core.functions.BtoC(_from, _to ,_amount, _interest, _id, _class, c_class,  _date).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(construct_txn)
    return tx_receipt




