from django import forms
from web3 import exceptions
from django.shortcuts import render
from django.http import HttpResponse 
from web3 import Web3
import web3
from .models import Company, Company_orders, TokenB, Deposit, TokenA
from core.solidity.abi import abi
from core.solidity.erc865_abi import erc865_abi
from core.solidity.bytecode import bytecode
from core.solidity.erc865_bytecode import erc865_bytecode
import json
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .forms import user_login, user_register, deposit, set_order_rate, companyListForm, set_loan,send_account_pay
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
from notifications.signals import notify ## 通知模組
from notifications.models import Notification ##通知模組
from django.db.models import Avg,Count,Max,Min,Sum
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
class index(generic.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'index.html')
class invest_index(generic.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'invest_index.html')
class invest_option(generic.View):
     def get(self, request, *args, **kwargs):
        return render(request, 'invest_option.html')
class invest_loan(generic.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'invest_loan.html')
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
            all_notify = request.user.notifications.all()
            redundant = all_notify.count() - 9
            if redundant > 0:
                last_notify = all_notify.reverse()[:redundant]
                for del_ele in last_notify:
                    del_ele.delete()
            user = request.user
            company = Company.objects.get(user = user)
            tokenA = TokenA.objects.filter(tokenA_company = company).order_by('-tokenA_time')  ##從最新的開始 -tokenA_time 是decending
            deposit = Deposit.objects.filter(deposit_company = company).order_by('-deposit_time')
            order_send_count = company.send_company.filter(Q(state = 1)|Q(state = 2)|Q(state = 3)).count()
            order_receive_count = TokenB.objects.filter(Q(curr_company = company) & (Q(class_type = 2) | Q(class_type =3))).count()
            account_payable_count = company.send_company.filter(Q(state = 7)|Q(state = 8)|Q(state = 10)).count()
            account_receivable_count = TokenB.objects.filter(Q(curr_company = company) & (Q(class_type = 1) | Q(class_type =3))).count()
            context = {'msg':company,'tokenA':tokenA,'deposit':deposit,'order_send_count':order_send_count,"order_receive_count":order_receive_count,'account_payable_count':account_payable_count,'account_receivable_count':account_receivable_count}
            return render(request, 'company_index.html',context)
        else:
            return redirect(reverse_lazy('login_company'))
    ##存入保證金(平台幣)
    def post(self, request, *args, **kwargs):
        # if 'confirm' in request.POST:
        form = deposit(request.POST)
        company = Company.objects.filter(user = request.user)[0]
        deploy_company = Company.objects.filter(id = company.id)
        if form.is_valid():
            core_address = company.public_address ##公司錢包地址
            core_address = Web3.toChecksumAddress(core_address) #轉換成checksum address
            check_enough_balalce = call_ERC865(core_address) / DECIMALS ## 先 view 餘額
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

                # 紀錄mintTokenA進資料庫
                new_tknA = TokenA.objects.create(
                    tokenA_company=company,
                    tokenA_amount=deposit_amount,
                    transactionHash=str(logs[0]['transactionHash'].hex())
                )

                all_deposit_amount = call_tokenA(company.contract_address,core_address) ## 去鏈上拿tokenA數量view mapping tokenA
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
        return  company.send_company.filter(Q(state = 1)|Q(state = 2)|Q(state = 3))
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
        allUser = auth.get_user_model() # return all user
        form = set_order_rate(request.POST)
        if form.is_valid():
            orders_id = form.cleaned_data['orders_id'] ##訂單編號
            rec_com_address = form.cleaned_data['rec_com_address'] ##接收的公司的地址 
            rec_company = Company.objects.filter(public_address = rec_com_address)[0] ##接收的公司object
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

            # 先上鏈再操縱資料庫
            # (address _to, uint256 _amount, uint256 _interest, uint256 _date, uint16 _class)
            logs = token_A_to_B(contract_address, rec_com_address, amount, int(rate), date_span, 2) ##訂單 class = 2 上鏈
            # tokenAtoB的 event
            event = logs[0]['args']

            print(logs)
            
            log_amount, log_rate, log_receiver, log_id=  event['amount'], event['interest'], event['receiver'], event['id']
            transactionHash = str(logs[0]['transactionHash'].hex())

            # db manipulation
            order_for_update.update(rate = rate , start_date = datetime.date.today(), state = 2) ##更新設定利率 起始時間 狀態變為準備中 tokenB_balance = amount 移到TokenB紀錄
            core_amount_a = float(call_tokenA(contract_address, core_address)) ## 拿到最新的tokenA數量
            company_for_update.update(amount_a = core_amount_a) ##更新資料庫

            new_tknB = TokenB.objects.create(
                amount=log_amount, 
                class_type=2, 
                token_id=log_id, 
                interest=log_rate, 
                date_span=date_span, 
                transfer_count=0, 
                initial_order=order,
                curr_company = rec_company,
                pre_company = company,
                transactionHash = transactionHash,
                tokenB_balance = log_amount,   ## 原本在Company_orders資料表下
            )

            context = {"log_amount":log_amount,"log_rate":log_rate,"log_receiver":log_receiver}
            ###############消息模組
            receiver = order.receive_compamy.user ## 找到訂單接收者
            notify.send(user, recipient=receiver, verb='發送了訂單') ## 向訂單接收者發送消息
            ######################## 這裡要一個頁面説訂單已發出 ########################
            return redirect(reverse_lazy('company_index'))
        
    
   
@method_decorator(login_required, name='dispatch')
class company_order_rec(generic.ListView):
    model = TokenB
    template_name = 'company_orders_rec.html'
    context_object_name = 'rec_orders'
    paginate_by = 6
    def get_queryset(self):
        user = self.request.user
        company = Company.objects.get(user = user)
        order_tokenB = TokenB.objects.filter(Q(curr_company = company) & (Q(class_type = 2) | Q(class_type =3))).order_by('date_span')   ## filter 該公司所擁有的tokenB
            ######################## 已改為用tokenB的資料庫做filter ########################
        return  order_tokenB   

    def get_context_data(self, **kwargs):
        _company_list = []
        context =  super(company_order_rec,self).get_context_data(**kwargs)
        user = self.request.user
        company_list = list(Company.objects.all())
        for com in company_list:
            _company_list.append(com.user.username)
        form = companyListForm(data_list = _company_list)
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        allUser = auth.get_user_model() # return all user
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        optype = request.POST['optype'] # optype decides which form to catch

        if optype == 'loan':
            form = set_loan(request.POST)
        elif optype =='bToC':
            form = companyListForm(request.POST)
        print(form.errors)
        if form.is_valid():
            if form.cleaned_data['optype'] == 'loan':
                ## tokenb會有相同的initial order, 但會有不同的tokenid
                orders_id = int(form.cleaned_data['orders_id'])
                TOKENB_id = int(form.cleaned_data['loan_TOKENB_id'])
                order = Company_orders.objects.get(id = orders_id) ##找到資料庫的這筆訂單
                order_for_update = Company_orders.objects.get(id = orders_id)
                tokenB = TokenB.objects.get(id = TOKENB_id)   ##取得訂單tokenB
                initial_company_contract_address = tokenB.initial_order.send_company.contract_address
                now = datetime.date.today() ## 透過平台融資日
                end = order.end_date ## 結束日
                date_span = end - now ## 時間段
                date_span = date_span.days
                '''沒問題了'''
                contract_address = initial_company_contract_address
                ''''''
                ### contract manipulation
                _loaner = Web3.toChecksumAddress(company.public_address)
                _amount = int(form.cleaned_data['orders_price'])
                _class =  tokenB.class_type
                _id = int(tokenB.token_id)
                _interest = int(form.cleaned_data['orders_interest'][:-1])
                _date = date_span

                print("---------",contract_address, _loaner, _amount ,_class, _id, _interest, _date,'--------')
                try: 
                    tx_receipt = loan(contract_address, _loaner, _amount ,_class, _id, _interest, _date)
                except exceptions.SolidityError as error:
                    print(error)
                
                # 解析event
                Core = w3.eth.contract(contract_address, abi=abi)
                logs = Core.events.loan_event().processReceipt(tx_receipt) #拿log
                event = logs[0]['args']
                
                print(logs)

                ### db manipulation
                loan_company = company
                token_id = event['id']
                amount = int(event['amount'])
                interest = int(event['interest'])/100
                date_span = int(event['date'])
                transactionHash = str(logs[0]['transactionHash'].hex())
                
                # 新增一個tokenB物件
                new_tknB = TokenB.objects.create(
                    curr_company = loan_company,
                    amount=amount, 
                    class_type=4, 
                    token_id=token_id, 
                    interest=interest, 
                    date_span=date_span, 
                    transfer_count=0, 
                    initial_order=order,
                    transactionHash=transactionHash,
                    tokenB_balance = amount
                ) 
                ## update tokenB
                tokenB_balance = tokenB.tokenB_balance - amount
                already_loan = tokenB.already_loan+amount
                tokenB.already_loan = already_loan # update tokenB already loan
                tokenB.tokenB_balance =  tokenB_balance
                tokenB.save()

                return render(request, 'company_index.html')

            # return HttpResponse('good')
            elif form.cleaned_data['optype'] == 'bToC':
                bToC_id = int(form.cleaned_data['bToC_id'])
                TOKENB_id = int(form.cleaned_data['bToC_TOKENB_id']) 
                order = Company_orders.objects.filter(id = bToC_id)[0] ##找到資料庫的這筆訂單
                tokenB = TokenB.objects.filter(id = TOKENB_id)[0]  
                tokenB_transfer_count = int(tokenB.transfer_count)
                tokenB_id = int(tokenB.token_id)
                now = datetime.date.today() ## 透過平台融資日
                end = order.end_date ## 結束日
                date_span = end - now ## 時間段
                date_span = date_span.days
                to_company = form.cleaned_data['bToC_to_company_name'] # 被移轉的公司
                to_company = allUser.objects.filter(username = to_company)[0]
                to_company = Company.objects.filter(user = to_company)[0]
                contract_address = order.send_company.contract_address
                
                ### contract manipulation
                _from = Web3.toChecksumAddress(company.public_address)
                _to = Web3.toChecksumAddress(to_company.public_address)
                _interest = int(form.cleaned_data['bToC_interest'][:-1])
                _amount = int(form.cleaned_data['bToC_price'])
                _id = tokenB_id
                _class = tokenB.class_type
                c_class = 3
                _date = date_span
                try:
                    tx_receipt = bToC(contract_address, _from, _to ,_amount, _interest, _id, _class, c_class,  _date)
                except exceptions.SolidityError as error:
                    print(error)

                # 解析event
                Core = w3.eth.contract(contract_address, abi=abi)
                logs = Core.events.tokenB_event().processReceipt(tx_receipt) #拿log
                event = logs[0]['args']
                log_amount = event['amount']

                # db manipulation
                token_id = event['id']

                new_tknB = TokenB.objects.create(
                    amount=_amount, 
                    class_type=3, 
                    token_id=token_id, 
                    interest=_interest, 
                    date_span=date_span, 
                    transfer_count=tokenB_transfer_count+1, 
                    initial_order=order,
                    curr_company = to_company,
                    pre_company = company,
                    transactionHash = str(logs[0]['transactionHash'].hex()),
                    tokenB_balance = log_amount
                ) 
                already_transfer = tokenB.already_transfer + log_amount
                tokenB.already_transfer = already_transfer
                transfer_count = tokenB_transfer_count+1
                tokenB.transfer_count = transfer_count
                tokenB.save()
                return render(request, 'company_index.html')

##應付
class company_account_pay(generic.ListView):
    model = Company_orders
    template_name = 'company_account_pay.html'
    context_object_name = 'orders'
    paginate_by = 6
    ##回傳每筆訂單
    def get_queryset(self):
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        return  company.send_company.filter(Q(state = 7)|Q(state = 8)|Q(state = 10))
    def get_context_data(self, **kwargs) :
        form = set_order_rate()
        company_addr_dict = {}
        rec_com_list = []
        context =  super(company_account_pay,self).get_context_data(**kwargs)
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
    
    def post(self, request, *args, **kwargs):
        allUser = auth.get_user_model() # return all user
        form = send_account_pay(request.POST)
        if form.is_valid():
            orders_id = form.cleaned_data['orders_id'] ##訂單編號
            rec_com_address = form.cleaned_data['rec_com_address'] ##接收的公司的地址 
            rec_company = Company.objects.filter(public_address = rec_com_address)[0] ##接收的公司object
            rec_com_address = Web3.toChecksumAddress(rec_com_address) 
            ##rate = float(form.cleaned_data['rate']) ## 票貼利率  
            ##rate_to_percent = (100 - rate) / 100    #票貼後實拿百分比
            user = self.request.user ##請求的使用者
            order = Company_orders.objects.filter(id = orders_id)[0] ##找到資料庫的這筆訂單
            order_for_update = Company_orders.objects.filter(id = orders_id) ## update 只支援queryset
            amount = int(order.price)  ##訂單價值 票貼等loan或
            print(amount,'--------')
            end = order.end_date ## 結束日
            now = datetime.date.today() ## 透過平台的發訂單日
            date_span = end - now ## 時間段
            date_span = date_span.days 
            company = Company.objects.filter(user = user)[0] ##發出的公司
            company_for_update = Company.objects.filter(user = user)
            contract_address = company.contract_address ##發出的公司合約地址
            core_address = Web3.toChecksumAddress(company.public_address) ## 核心 公鑰 checksumaddresss

            # 先上鏈再操縱資料庫
            # (address _to, uint256 _amount, uint256 _interest, uint256 _date, uint16 _class)
            logs = token_A_to_B(contract_address, rec_com_address, amount, 0, date_span, 1) ##應收 class = 1 應收上鏈
            # tokenAtoB的 event
            event = logs[0]['args']

            print(logs)
            
            log_amount, log_rate, log_receiver, log_id=  event['amount'], event['interest'], event['receiver'], event['id']
            transactionHash = str(logs[0]['transactionHash'].hex())

            # db manipulation
            order_for_update.update( start_date = datetime.date.today(), state = 8) ##更新 起始時間 狀態變為發出應付 
            core_amount_a = float(call_tokenA(contract_address, core_address)) ## 拿到最新的tokenA數量
            company_for_update.update(amount_a = core_amount_a) ##更新資料庫

            new_tknB = TokenB.objects.create(
                amount=log_amount, 
                class_type=1, 
                token_id=log_id, 
                interest=log_rate, 
                date_span=date_span, 
                transfer_count=0, 
                initial_order=order,
                curr_company = rec_company,
                pre_company = company,
                transactionHash = transactionHash,
                tokenB_balance = log_amount,   ## 原本在Company_orders資料表下
            )

            context = {"log_amount":log_amount,"log_rate":log_rate,"log_receiver":log_receiver}
            ###############消息模組
            receiver = order.receive_compamy.user ## 找到訂單接收者
            notify.send(user, recipient=receiver, verb='發送了應收帳款') ## 向訂單接收者發送消息
            ######################## 這裡要一個頁面説訂單已發出 ########################
            return render(request, 'invest_option.html')

##應收
class company_account_rec(generic.ListView):
    model = TokenB
    template_name = 'company_account_rec.html'
    context_object_name = 'rec_orders'
    paginate_by = 6
    def get_queryset(self):
        user = self.request.user
        company = Company.objects.get(user = user)
        account_rec_orders = Company_orders.objects.filter(state = 8) ##找出應收
        ## initial_order__in 用於filte 集合
        tokenB_is_account_rec = TokenB.objects.filter(Q(initial_order__in = account_rec_orders) & Q(curr_company = company) & (Q(class_type = 1) | Q(class_type =3))).order_by('date_span')

        return  tokenB_is_account_rec 
    def get_context_data(self, **kwargs):
        _company_list = []
        context =  super(company_account_rec,self).get_context_data(**kwargs)
        company_list = list(Company.objects.all())
        for com in company_list:
            _company_list.append(com.user.username)
        form = companyListForm(data_list = _company_list)
        form_loan = set_loan()
        context['form'] = form
        context['form_loan'] = form_loan
        return context
    def post(self, request, *args, **kwargs):
        allUser = auth.get_user_model() # return all user
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        optype = request.POST['optype'] # optype decides which form to catch

        if optype == 'loan':
            form = set_loan(request.POST)
        elif optype =='bToC':
            form = companyListForm(request.POST)
        print(form.errors)
        if form.is_valid():
            if form.cleaned_data['optype'] == 'loan':
                ## tokenb會有相同的initial order, 但會有不同的tokenid
                orders_id = int(form.cleaned_data['orders_id'])
                TOKENB_id = int(form.cleaned_data['loan_TOKENB_id'])
                _rate = int(form.cleaned_data['rate']) ##借貸自行設定比例
                order = Company_orders.objects.get(id = orders_id) ##找到資料庫的這筆訂單
                tokenB = TokenB.objects.get(id = TOKENB_id)   ##取得訂單tokenB
                initial_company_contract_address = tokenB.initial_order.send_company.contract_address
                now = datetime.date.today() ## 透過平台融資日
                end = order.end_date ## 結束日
                date_span = end - now ## 時間段
                date_span = date_span.days
                contract_address = initial_company_contract_address
                ### contract manipulation
                _loaner = Web3.toChecksumAddress(company.public_address)
                _amount = int(form.cleaned_data['orders_price'])
                _class =  tokenB.class_type
                _id = int(tokenB.token_id)
                _date = date_span
                print("---------",contract_address, _loaner, _amount ,_class, _id, _rate, _date,'--------')
                try: 
                    tx_receipt = loan(contract_address, _loaner, _amount ,_class, _id, _rate, _date)
                except exceptions.SolidityError as error:
                    print(error)
                
                # 解析event
                Core = w3.eth.contract(contract_address, abi=abi)
                logs = Core.events.loan_event().processReceipt(tx_receipt) #拿log
                event = logs[0]['args']
                
                print(logs)

                ### db manipulation
                loan_company = company
                token_id = event['id']
                amount = int(event['amount'])
                interest = int(event['interest'])/100
                date_span = int(event['date'])
                transactionHash = str(logs[0]['transactionHash'].hex())
                
                # 新增一個tokenB物件
                new_tknB = TokenB.objects.create(
                    curr_company = loan_company,
                    amount=amount, 
                    class_type=4, 
                    token_id=token_id, 
                    interest=interest, 
                    date_span=date_span, 
                    transfer_count=0, 
                    initial_order=order,
                    transactionHash=transactionHash,
                    tokenB_balance = amount
                ) 
                ## update tokenB
                tokenB_balance = tokenB.tokenB_balance - amount
                already_loan = tokenB.already_loan+amount
                tokenB.already_loan = already_loan # update tokenB already loan
                tokenB.tokenB_balance =  tokenB_balance
                tokenB.save()

                return render(request, 'company_index.html')

            # return HttpResponse('good')
            elif form.cleaned_data['optype'] == 'bToC':
                bToC_id = int(form.cleaned_data['bToC_id'])
                TOKENB_id = int(form.cleaned_data['bToC_TOKENB_id'])
                _rate = int(form.cleaned_data['rate']) ##票貼
                notes_rate = (100 - _rate) ## 實拿比例
                order = Company_orders.objects.filter(id = bToC_id)[0] ##找到資料庫的這筆訂單
                tokenB = TokenB.objects.filter(id = TOKENB_id)[0]  
                tokenB_transfer_count = int(tokenB.transfer_count)
                tokenB_id = int(tokenB.token_id)
                now = datetime.date.today() ## 透過平台融資日
                end = order.end_date ## 結束日
                date_span = end - now ## 時間段
                date_span = date_span.days
                to_company = form.cleaned_data['bToC_to_company_name'] # 被移轉的公司
                to_company = allUser.objects.filter(username = to_company)[0]
                to_company = Company.objects.filter(user = to_company)[0]
                contract_address = order.send_company.contract_address
                
                ### contract manipulation
                _from = Web3.toChecksumAddress(company.public_address)
                _to = Web3.toChecksumAddress(to_company.public_address)
                _interest = int(form.cleaned_data['bToC_interest'][:-1])
                _amount = int(form.cleaned_data['bToC_price'])
                _id = tokenB_id
                _class = tokenB.class_type
                c_class = 3
                _date = date_span
                try:
                    tx_receipt = bToC(contract_address, _from, _to ,_amount, notes_rate, _id, _class, c_class,  _date)
                except exceptions.SolidityError as error:
                    print(error)

                # 解析event
                Core = w3.eth.contract(contract_address, abi=abi)
                logs = Core.events.tokenB_event().processReceipt(tx_receipt) #拿log
                event = logs[0]['args']
                log_amount = event['amount']

                # db manipulation
                token_id = event['id']

                new_tknB = TokenB.objects.create(
                    amount=_amount, 
                    class_type=3, 
                    token_id=token_id, 
                    interest=notes_rate,  ##票貼比例 賣給下一家企業的價錢 ＝ amount * notes_rate
                    date_span=date_span, 
                    transfer_count=tokenB_transfer_count+1, 
                    initial_order=order,
                    curr_company = to_company,
                    pre_company = company,
                    transactionHash = str(logs[0]['transactionHash'].hex()),
                    tokenB_balance = log_amount
                ) 
                already_transfer = tokenB.already_transfer + log_amount
                tokenB.already_transfer = already_transfer
                transfer_count = tokenB_transfer_count+1
                tokenB.transfer_count = transfer_count
                tokenB.save()
                return render(request, 'company_index.html')

##通知
@method_decorator(csrf_exempt, name='dispatch')
class my_notification(generic.View):
    def get(self, request, *args, **kwargs):
        ##大於9個通知刪除##
        return render(request,'my_notification.html')
    def post(self, request, *args, **kwargs):
        notify_ID = request.POST.get("notify_ID")
        unread_obj = Notification.objects.get(pk = notify_ID)
        unread_obj.mark_as_read()        
        context = {'notify_ID':notify_ID}
        return HttpResponse(json.dumps(context),content_type="application/json")
## 基本資料
class company_info(generic.View):
     def get(self, request, *args, **kwargs):
        return render(request, 'company_info.html')
##各項目餘額
class wallet(generic.View):
     def get(self, request, *args, **kwargs):
        context = {}
        company = Company.objects.get(user = request.user)
        core_address = company.public_address ##公司錢包地址
        core_address = Web3.toChecksumAddress(core_address) #轉換成checksum address
        amount_865 = call_ERC865(core_address)  / DECIMALS ## 先 view 餘額
        core_amount_a = float(call_tokenA(company.contract_address, core_address))
        company_all_tokenB = TokenB.objects.filter(Q(curr_company = company) & (Q(class_type = 1)|Q(class_type = 2)| Q(class_type = 3)|Q(class_type = 5)))
        sum_receive_order = company_all_tokenB.aggregate(tokenB_sum = Sum('tokenB_balance'))
        context['amount_865'] = json.dumps(amount_865)
        context['amount_a'] = json.dumps(core_amount_a)
        context['sum_receive_order'] = json.dumps(int(sum_receive_order['tokenB_sum']))
        return render(request, 'wallet.html',context)


##驗證
@method_decorator(csrf_exempt, name='dispatch')
class verification_ERP(generic.ListView):
    model = Company_orders
    template_name = 'verification_ERP.html'
    context_object_name = 'orders'
    paginate_by = 6
    def get_queryset(self):
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        return  company.send_company.filter(Q(state = 5)|Q(state = 6))
    def get_context_data(self, **kwargs) :
        form = set_order_rate()
        context =  super(verification_ERP,self).get_context_data(**kwargs)
        context['form'] = form
        return context

##驗證成功
@method_decorator(csrf_exempt, name='dispatch')
class verification_OK(generic.ListView):
    model = Company_orders
    template_name = 'verification_OK.html'
    context_object_name = 'orders'
    paginate_by = 6





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
        event = logs[0]['args']

        ## db manpulation
        company = Company.objects.filter(public_address = res['CustomField1'])[0]
        transactionHash = str(logs[0]['transactionHash'].hex())

        new_deposit = Deposit.objects.create(
            deposit_company = company,
            deposit_amount = int(int(event['value'])/DECIMALS),
            transactionHash = transactionHash
        )

        t = loader.get_template('payment_success.html')
        context.update({ 
            "res": res,
            "receipt": tx_receipt,
            "event":event,
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
            'gas':300000,
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )
    # 簽名
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    # transaction送出並且等待回傳
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash,timeout=600)
    logs = Core.events.tokenB_event().processReceipt(tx_receipt) #拿log

    return logs


def loan(_contract_addr, _loaner, _amount ,_class, _id, _interest, _date):
#(address _loaner, uint256 _amount, uint16 _class, uint _id, uint256 _interest, uint256 _date)
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    construct_txn = Core.functions.loan(_loaner, _amount, _class, _id, _interest, _date).buildTransaction(
        {
            'from': account_from['address'],
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )
    # 簽名
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    # transaction送出並且等待回傳
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash ,timeout=600)

    return tx_receipt

def bToC(_contract_addr, _from, _to ,_amount, _interest, _id, _class, c_class,  _date):
    # (address _from, address _to, uint256 _amount, uint256 _interest, uint _id, uint16 _class, uint16 c_class, uint256 _date)
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    construct_txn = Core.functions.BtoC(_from, _to ,_amount, _interest, _id, _class, c_class, _date).buildTransaction(
        {
            'from': account_from['address'],
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )
    # 簽名
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    # transaction送出並且等待回傳
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash ,timeout=600)

    return tx_receipt




#### 檢查前端發起交易者
@csrf_exempt
def checkUser(request):
    context={}
    user = request.user
    company = Company.objects.filter(user = user)[0]
    curr_user_addr = company.public_address
    
    if request.POST:
        if request.POST['check_addr'] == curr_user_addr:
            context['check'] = 'passed'
            if 'fallback' in request.session.keys():
                del request.session['fallback']
            return HttpResponse(json.dumps(context), content_type="application/json")
        else: 
            request.session['fallback'] = '非本人'
            context['check'] = 'reject'
            return HttpResponse(json.dumps(context), content_type="application/json")




