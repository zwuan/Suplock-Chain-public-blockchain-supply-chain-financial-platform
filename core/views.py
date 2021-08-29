import decimal
from django import forms
from web3 import contract, exceptions
from django.shortcuts import render
from django.http import HttpResponse 
from web3 import Web3
import web3
from .models import Company, Company_orders, TokenB, Deposit, TokenA, LoanCertificate, Tranche, LoanPayable, Invest_user, Acc_rec_for_sale
from core.solidity.abi import abi
from core.solidity.erc865_abi import erc865_abi
from core.solidity.bytecode import bytecode
from core.solidity.erc865_bytecode import erc865_bytecode
from core.solidity.invest_abi import invest_abi
from core.solidity.llss_abi import llss_abi
from core.solidity.llss_bytecode import llss_bytecode
from core.solidity.invest_bytecode import invest_bytecode
import json
from django.views import generic
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from .forms import user_login, user_register, deposit, set_order_rate, companyListForm, set_loan,send_account_pay, buyTranche, paybackForm, acc_rec_form, buy_acc_rec
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
import math
from decimal import Context, Decimal

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
## erc865合約地址
erc865_contract_address = '0xcb8565c6eeb98fc8c441b5e07c1d6e7cb200b277'
erc865_contract_address = w3.toChecksumAddress(erc865_contract_address)
##投資人合約地址
invest_contract_address = '0x7Dc19321399571c9675A74eB19d892544D83B397'
invest_contract_address = w3.toChecksumAddress(invest_contract_address)
Invest = w3.eth.contract(invest_contract_address, abi=invest_abi)

# term = Invest.functions.getTermPriPayable(591602879944030688459223811289325581353205954224232358337702651604628753545, 0).call({'from': account_from['address']})
# print(term/D)
# print(Invest.functions.getTotalPrincipleNotPaid(83631474871684062124992096394957904277424839154576564214097959304864797659213).call({'from': account_from['address']}))
# _investor = w3.toChecksumAddress('0xA3E58464444bC66b5bb7FB8e76D7F4fDE52126F2')
# print(Invest.functions.investorTranche(_investor, 24056184600878995381399587181737493561548335230280751938782696962070537802085 , 1).call({'from': account_from['address']}))
# print(Invest.functions.getTermInvestorDiv(_investor, 83631474871684062124992096394957904277424839154576564214097959304864797659213 , 2, 0).call({'from': account_from['address']}))
# print(Invest.functions.getTermInvestorDiv(_investor, 83631474871684062124992096394957904277424839154576564214097959304864797659213 , 3, 0).call({'from': account_from['address']}))

##1155合約地址
llss_contract_address = '0x3F4d19e0750F2eC9B0908cC880ddA5f940Dbb29E'
llss_contract_address = w3.toChecksumAddress(llss_contract_address)
# 廠商登入/註冊（template有兩個form，而且user&company分開，需要兩個modelForm，因此用formView太複雜）

def calculatePmt(interest, principle, term):
	return interest * principle / (1-(1+interest)**-term)

class invest_wallet(generic.ListView):
    model = Tranche
    template_name = 'invest_wallet.html'
    context_object_name = 'tranche'
    paginate_by = 6
    def get(self, request, *args, **kwargs):
        user = self.request.user
        '''
        user 改成 company or Investor -kevin
        '''
        if user.groups.filter(name = 'firm').exists():
            company = Company.objects.get(user=user)
            com_addr = company.public_address
            com_addr = w3.toChecksumAddress(com_addr)
            company_erc865 = int(call_ERC865(com_addr)  / DECIMALS)

        else:
            investor = Invest_user.objects.get(user=user)
            investor_addr = investor.public_address
            investor_addr = w3.toChecksumAddress(investor_addr)
            company_erc865 = int(call_ERC865(investor_addr)  / DECIMALS)  
        tranche_bought = Tranche.objects.filter(investor = user).order_by('-id')
        sum=0
        for t in tranche_bought:
            curr_accu = Decimal(t.accu_earning)
            sum+=curr_accu
        
        context = {'tranche': tranche_bought, 'past_earning':round(sum, 4), 'user':user, 'erc856':company_erc865}
        return render(request, 'invest_wallet.html',context) 

class index(generic.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'index.html')

class invest_index(generic.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'invest_index.html')

### 投資選項首頁
# @method_decorator(login_required, name='dispatch')
class invest_option(generic.ListView):
    model = LoanCertificate
    template_name = 'invest_option.html'
    context_object_name = 'invest_option'
    paginate_by = 6
    def get_queryset(self):
        user = self.request.user
        invest_option = TokenB.objects.filter(Q(class_type = 4)).order_by('-id')
        return invest_option 

    def get_context_data(self, **kwargs):
        unique_card_arr = []
        context =  super(invest_option,self).get_context_data(**kwargs)
        user = self.request.user
        tokenB_detail = TokenB.objects.filter(Q(class_type = 4)).order_by('-id')
        # 合約編號, 融資金額, 年化利率, 融資期間, 每月還款, 區塊鏈證明
        for tokenB in tokenB_detail:
            certificate = LoanCertificate.objects.filter(loan_id = tokenB.token_id)[0]
            termPri = Invest.functions.getTermPriPayable(int(tokenB.token_id), certificate.date_span - certificate.curr_span).call({'from': account_from['address']})
            curr_dic = {}
            curr_dic['id'] = tokenB.id
            curr_dic['principle'] = tokenB.amount
            curr_dic['interest'] = tokenB.interest
            curr_dic['start_date'] = tokenB.initial_order.start_date
            curr_dic['end_date'] = tokenB.initial_order.end_date
            curr_dic['term_pri'] = termPri / DECIMALS
            curr_dic['tx_hash'] = tokenB.transactionHash
            unique_card_arr.append(curr_dic)

        context['unique_card_arr'] = unique_card_arr
        return context   

### 轉erc buytranche
@method_decorator(login_required, name='dispatch')
class invest_loan(generic.View):
    def get(self, request, *args, **kwargs):
        context={}
        id=kwargs['pk']
        
        ## 更新帳號餘額
        user = request.user
        if user.groups.filter(name = 'firm').exists():
            company = Company.objects.get(user = user)
            core_address = company.public_address ##公司錢包地址
            core_address = Web3.toChecksumAddress(core_address) #轉換成checksum address
            amount_865 =int(call_ERC865(core_address)  / DECIMALS) ## 先 view 餘額
        else:
            Investor = Invest_user.objects.get(user=user)
            investor_address = Investor.public_address ##公司錢包地址
            investor_address = Web3.toChecksumAddress(investor_address) #轉換成checksum address
            amount_865 = int(call_ERC865(investor_address)  / DECIMALS) ## 先 view 餘額

        # 編號, 利率, 申購金額餘額, 生效,截止日期
        tokenB = TokenB.objects.get(pk=id)
        context['id'] = id
        context['token_id'] = tokenB.token_id
        trancheA = LoanCertificate.objects.filter(loan_id = tokenB.token_id)[0]
        context['a_interest'] = trancheA.interest
        
        trancheB = LoanCertificate.objects.filter(loan_id = tokenB.token_id)[1]
        context['b_interest'] = trancheB.interest
        
        trancheC = LoanCertificate.objects.filter(loan_id = tokenB.token_id)[2]
        context['c_interest'] = trancheC.interest

        context['avail_arr'] = [trancheA.avail_amount, trancheB.avail_amount, trancheC.avail_amount]

        context['start_date'] = tokenB.initial_order.start_date
        context['end_date'] = tokenB.initial_order.end_date
        
        context['amount_865'] = amount_865 ## 先 view 餘額

        return render(request, 'invest_loan.html', context)
    
    def post(self, request, *args, **kwargs):
        allUser = auth.get_user_model() # return all user
        user = self.request.user
        form = buyTranche(request.POST)
        if user.groups.filter(name = 'firm').exists():
            company = Company.objects.filter(user = user)[0]
        else:
            company = Invest_user.objects.filter(user = user)[0] ##偷懶
    
        if form.is_valid():
            print(form.cleaned_data)
            _investor = Web3.toChecksumAddress(company.public_address)
            _loan_id = int(form.cleaned_data['_loan_id'])
            _amount = int(Decimal(form.cleaned_data['_amount'])*DECIMALS)
            _class = int(form.cleaned_data['_class'])

            tx_receipt = buyTranche_method(_investor, _loan_id, _class, _amount)
            logs = Invest.events.BuyTranche().processReceipt(tx_receipt) #拿log
            # BuyTranche(_investor, _loan_id, _class, _amount)
            print(logs)
            event = logs[0]['args']

            investor = event['_investor']
            loan_id = event['_loan_id']
            riskClass = event['_class']
            amount = event['_amount']

            # 更新db裡剩餘可投資
            curr_loan = LoanCertificate.objects.get(loan_id=loan_id, riskClass=riskClass)
            curr_avail = int(curr_loan.avail_amount)- int(amount)
            curr_loan.avail_amount = curr_avail
            curr_loan.save()
            # 更新tokenB的tokenB_balance
            curr_tokenB = TokenB.objects.get(token_id=loan_id, class_type=4)
            curr_tokenB.already_loan -= Decimal(int(amount)/DECIMALS)
            curr_tokenB.save()

            if Tranche.objects.filter(investor=user, loan_id=loan_id, riskClass=riskClass).exists():
                tranche_owned = Tranche.objects.get(investor=user, loan_id=loan_id, riskClass=riskClass)
                tranche_owned.amount = int(tranche_owned.amount) + int(amount)
                tranche_owned.save()
            else:
                new_tranche_res = Tranche.objects.create(
                    investor = user,
                    loan_id = loan_id,
                    riskClass = riskClass,
                    amount = amount,
                    loanCertificate = curr_loan
                )

            
            
            return redirect(reverse_lazy('invest_wallet'))

            



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
                if user.groups.filter(name = 'firm').exists():
                    return redirect(reverse_lazy('company_index'))
                else:
                    return redirect(reverse_lazy('invest_index'))

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
                firm = Group.objects.get(name='firm')
                firm.user_set.add(user)
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
            ## 待發出和已發出訂單數量
            order_send_count = company.send_company.filter(Q(state = 1)|Q(state = 2)|Q(state = 3)).count()
            ##訂單接收量
            company_orders_rec = Company_orders.objects.filter(state = 2) ##找出應收
            order_receive_count = TokenB.objects.filter(Q(initial_order__in = company_orders_rec) & Q(curr_company = company) & (Q(class_type = 2) | Q(class_type =3))).order_by('date_span').count()
            ## 尚未付款和已發出應付數量
            account_payable_count = company.send_company.filter(Q(state = 7)|Q(state = 8)|Q(state = 10)).count()
            ##應收接收量   
            account_rec_orders = Company_orders.objects.filter(state = 8) ##找出應收
            account_receivable_count = TokenB.objects.filter(Q(initial_order__in = account_rec_orders) & Q(curr_company = company) & (Q(class_type = 1) | Q(class_type =3))).order_by('date_span').count()
            context = {'msg':company,'tokenA':tokenA,'deposit':deposit,'order_send_count':order_send_count,"order_receive_count":order_receive_count,'account_payable_count':account_payable_count,'account_receivable_count':account_receivable_count}
            return render(request, 'company_index.html',context)
        else:
            return redirect(reverse_lazy('login_company'))
    ##存入保證金(平台幣)
    def post(self, request, *args, **kwargs):
        # if 'confirm' in request.POST:
        # print(request.POST)
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
                tx_receipt = deploy_contract(core_address, add_amount_a)
                contract_addr = tx_receipt['contractAddress'] ##取得部署的合約地址
                txhash = tx_receipt['transactionHash'].hex()
                construct_amount = call_tokenA(contract_addr,core_address) ##查看首次部署的tokenA數量
                deploy_company.update(amount_a = construct_amount, core = True ,contract_address = contract_addr) ##修改資料庫
                content = {"txhash":txhash} ##顯示到前端
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
                content = {"txhash":txhash} ##顯示到前端
            return render(request, 'tx_result.html', content)

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
    def get_context_data(self, **kwargs):
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
        # print(context)
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
            
            '''
            這裡的amount看看要不要記很大
            '''

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
            ###############消息模組
            receiver = order.receive_compamy.user ## 找到訂單接收者
            notify.send(user, recipient=receiver, verb='發送了訂單') ## 向訂單接收者發送消息
            ######################## 這裡要一個頁面説訂單已發出 ########################
            content = {"txhash":logs[0]['transactionHash'].hex()} ##顯示到前端
            return render(request, 'tx_result.html', content)
        


@method_decorator(login_required, name='dispatch')
class company_order_rec(generic.ListView):
    model = TokenB
    template_name = 'company_orders_rec.html'
    context_object_name = 'rec_orders'
    paginate_by = 6
    def get_queryset(self):
        user = self.request.user
        company = Company.objects.get(user = user)
        company_orders_rec = Company_orders.objects.filter(state = 2) ##找出應收
        tokenB_is_company_orders_rec = TokenB.objects.filter(Q(initial_order__in = company_orders_rec) & Q(curr_company = company) & (Q(class_type = 2) | Q(class_type =3))).order_by('date_span')
            ######################## 已改為用tokenB的資料庫做filter ########################
        return  tokenB_is_company_orders_rec   

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
                
                '''暫時先這樣'''
                _month_span = (date_span // 30)+1
                '''資料庫看之後怎麼改'''
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
                interest = int(event['interest'])
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
                    already_loan = amount,
                    tokenB_balance = amount
                ) 
                ## update tokenB
                tokenB_balance = tokenB.tokenB_balance - amount
                already_loan = tokenB.already_loan+amount
                tokenB.already_loan = already_loan # update tokenB already loan
                tokenB.tokenB_balance =  tokenB_balance
                tokenB.save()

                # update完tokenB 便mintCertificate(實際上是做出tranche讓投資人投資)
                # 用for iterate 3個class
                
                class_principle = [math.floor(amount/4), math.floor(amount/4), math.floor(amount/2)]
                interest_dict = {'10':[6, 8, 10], '8':[4,6,8], '6':[2,4,6], '12':[8,10,12]}
                interest_arr = interest_dict[str(interest)]
                for i in range(3):
                    _pmt = int(math.floor(calculatePmt(interest_arr[i]/1200, class_principle[i]*10**8, _month_span))*10**10)
                    tx_receipt = mintCertificate(token_id, _loaner, class_principle[i]*DECIMALS, interest_arr[i], _month_span, i+1, _pmt)
                    logs = Invest.events.MintCertificate().processReceipt(tx_receipt) #拿log
                    print(logs)
                    event = logs[0]['args']

                    loan_id = event['_loan_id']
                    principle = event['_principle']
                    curr_interest = int(event['_interest'])
                    date_span = int(event['_datespan'])
                    riskClass = int(event['_riskClass'])
                    pmt = int(event['_pmt'])

                    # 新增一個tokenB物件
                    new_Cer = LoanCertificate.objects.create(
                        tokenB = new_tknB,
                        loan_id = loan_id,
                        loan_company=loan_company, 
                        principle=principle, 
                        interest=curr_interest, 
                        date_span=date_span, 
                        curr_span=date_span,
                        riskClass=riskClass, 
                        transactionHash=str(logs[0]['transactionHash'].hex()),
                        avail_amount=principle,
                    ) 
                ''' 之後這段要寫在buy tranche 買到滿時才觸發 '''
                ### 建立loan payable資料表
                pri_left = amount
                pmt_for_company = math.floor(calculatePmt(interest/1200, amount, _month_span))
                for i in range(_month_span):
                    term_interest = pri_left*interest/1200
                    term_principle = pmt_for_company - term_interest
                    
                    new_payable = LoanPayable.objects.create(
                        tokenB = new_tknB,
                        term_principle = term_principle,
                        term_interest = term_interest,
                        term = i
                    )

                    pri_left -= term_principle
                ''' #################################### '''
                
                content = {"txhash":logs[0]['transactionHash'].hex()} ##顯示到前端
                return render(request, 'tx_result.html', content)

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
               
                tx_receipt = bToC(contract_address, _from, _to ,_amount, _interest, _id, _class, c_class,  _date)
           
                # 解析event
                Core = w3.eth.contract(contract_address, abi=abi)
                logs = Core.events.tokenB_event().processReceipt(tx_receipt) #拿log
                event = logs[0]['args']
                log_amount = event['amount']
                transactionHash = str(logs[0]['transactionHash'].hex())
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
                tokenB_balance = tokenB.tokenB_balance - log_amount
                already_transfer = tokenB.already_transfer + log_amount
                tokenB.already_transfer = already_transfer
                tokenB.tokenB_balance =  tokenB_balance
                transfer_count = tokenB_transfer_count+1
                tokenB.transfer_count = transfer_count
                tokenB.save()
                content = {"txhash":logs[0]['transactionHash'].hex()} ##顯示到前端
                return render(request, 'tx_result.html', content)

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
            ###############消息模組
            receiver = order.receive_compamy.user ## 找到訂單接收者
            notify.send(user, recipient=receiver, verb='發送了應收帳款') ## 向訂單接收者發送消息
            ######################## 這裡要一個頁面説訂單已發出 ########################
            content = {"txhash":logs[0]['transactionHash'].hex()} ##顯示到前端
            return render(request, 'tx_result.html', content)

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
        ## initial_order__in 用於filter 集合
        tokenB_is_account_rec = TokenB.objects.filter(Q(initial_order__in = account_rec_orders) & Q(curr_company = company) & (Q(class_type = 1) | Q(class_type =3))).order_by('date_span')

        return  tokenB_is_account_rec 
    def get_context_data(self, **kwargs):
        _company_list = []
        context =  super(company_account_rec,self).get_context_data(**kwargs)
        company_list = list(Company.objects.all())
        for com in company_list:
            _company_list.append(com.user.username)
        form = acc_rec_form()
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
            form = acc_rec_form(request.POST)
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
                    interest=_rate, 
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

                # update完tokenB 便mintCertificate(實際上是做出tranche讓投資人投資)
                # 用for iterate 3個class
                ###### 比例先 A:25%, B:25%, C:50%
                ###### 利率   A:6%, B:8%, C:10%
                '''暫時先這樣'''
                _month_span = (date_span // 30)+1
                '''資料庫看之後怎麼改'''

                class_principle = [math.floor(amount/4), math.floor(amount/4), math.floor(amount/2)]
                interest_arr = [6, 8, 10]
                for i in range(3):
                    tx_receipt = mintCertificate(token_id, _loaner, class_principle[i]*DECIMALS, interest_arr[i], _month_span, i+1)
                    logs = Invest.events.MintCertificate().processReceipt(tx_receipt) #拿log
                    print(logs)
                    event = logs[0]['args']

                    loan_id = event['_loan_id']
                    # principle = int(int(event['_principle'])/DECIMALS)
                    principle = event['_principle']
                    interest = int(event['_interest'])
                    date_span = int(event['_datespan'])
                    riskClass = int(event['_riskClass'])

                    # 新增一個tokenB物件
                    new_Cer = LoanCertificate.objects.create(
                        tokenB = new_tknB,
                        loan_id = loan_id,
                        loan_company=loan_company, 
                        principle=principle, 
                        interest=interest, 
                        date_span=date_span, 
                        curr_span=date_span,
                        riskClass=riskClass, 
                        transactionHash=str(logs[0]['transactionHash'].hex()),
                        avail_amount=principle,
                    ) 


                content = {"txhash":logs[0]['transactionHash'].hex()} ##顯示到前端
                return render(request, 'tx_result.html', content)

            # return HttpResponse('good')
            elif form.cleaned_data['optype'] == 'bToC':
                bToC_id = int(form.cleaned_data['bToC_id'])
                TOKENB_id = int(form.cleaned_data['bToC_TOKENB_id'])
                _rate = int(form.cleaned_data['rate']) ##票貼
                notes_rate = (100 - _rate) ## 實拿比例
                opening_price = int(form.cleaned_data['actual_price']) ##開價
                order = Company_orders.objects.filter(id = bToC_id)[0] ##找到資料庫的這筆訂單
                tokenB = TokenB.objects.filter(id = TOKENB_id)[0]  
                tokenB_transfer_count = int(tokenB.transfer_count)
                tokenB_id = int(tokenB.token_id)
                now = datetime.date.today() ## 透過平台融資日
                end = order.end_date ## 結束日
                date_span = end - now ## 時間段
                date_span = date_span.days
                core_company = order.send_company
                contract_address = order.send_company.contract_address
                to_company = Company.objects.get(id = 4) 
                ### contract manipulation
                _from = Web3.toChecksumAddress(company.public_address)
                _to = account_from['address']
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
                transactionHash = str(logs[0]['transactionHash'].hex()),
                # db manipulation
                token_id = event['id']
                new_tknB = TokenB.objects.create(
                    amount=_amount, 
                    class_type=3, 
                    token_id=token_id, 
                    interest=notes_rate,  
                    date_span=date_span, 
                    transfer_count=tokenB_transfer_count+1, 
                    initial_order=order,
                    curr_company = to_company,
                    pre_company = company,
                    transactionHash = str(logs[0]['transactionHash'].hex()),
                    tokenB_balance = log_amount
                ) 
                ##紀錄出售的應收帳款
                new_Acc_rec_for_sale = Acc_rec_for_sale.objects.create(
                    tokenB = new_tknB,
                    opening_price = opening_price, ## 開價
                    core_company = core_company, ##應付的公司
                    pre_own = company, ##目前出售的公司,
                    state = 1 ##出售中
                )

                tokenB_balance = tokenB.tokenB_balance - log_amount
                already_transfer = tokenB.already_transfer + log_amount
                tokenB.already_transfer = already_transfer
                tokenB.tokenB_balance = tokenB_balance
                transfer_count = tokenB_transfer_count+1
                tokenB.transfer_count = transfer_count
                tokenB.save()
                content = {"txhash":logs[0]['transactionHash'].hex()} ##顯示到前端
                return render(request, 'tx_result.html', content)

class acc_rec_auction(generic.ListView):
    model = Acc_rec_for_sale
    template_name = 'acc_rec_auction.html'
    context_object_name = 'acc_rec'
    paginate_by = 6
    def get_queryset(self):
        return Acc_rec_for_sale.objects.all()

class buy_acc_rec(generic.View):
    def get(self, request, *args, **kwargs):
        context={}
        id=kwargs['pk']
        core_address = Company.objects.get(user = request.user).public_address
        core_address =  w3.toChecksumAddress(core_address)
        AR_for_sale = Acc_rec_for_sale.objects.get(id = id)
        opening_price = AR_for_sale.opening_price
        today = datetime.date.today().strftime('%Y-%m-%d')
        actual_price = AR_for_sale.tokenB.amount
        end_date = AR_for_sale.tokenB.initial_order.end_date
        amount_865 =int(call_ERC865(core_address)  / DECIMALS)
        context['id'] = id
        context['opening_price'] = opening_price
        context['today'] = today
        context['actual_price'] = actual_price
        context['end_date'] = end_date
        context['amount_865'] = amount_865
        return render(request, 'buy_acc_rec.html', context) 
    def post(self, request, *args, **kwargs):
        context = {}
        company = Company.objects.get(user = request.user)
        company_address =  w3.toChecksumAddress(company.public_address)
        buy_acc_rec_id = request.POST.get('arc_rec_id')
        price = int(request.POST.get('_amount')) * DECIMALS
        fee = 30 *DECIMALS
        tokenB_for_transfer = Acc_rec_for_sale.objects.get(id = buy_acc_rec_id).tokenB
        Acc_rec_sold = Acc_rec_for_sale.objects.get(id = buy_acc_rec_id)
        tokenB_transfer_count = int(tokenB_for_transfer.transfer_count)
        tokenB_id = int(tokenB_for_transfer.token_id)
        initial_order = tokenB_for_transfer.initial_order
        end = initial_order.end_date
        now = datetime.date.today() 
        date_span = end-now
        date_span = date_span.days
        core_contract = initial_order.send_company.contract_address
        ##上鏈資料
        _from = Web3.toChecksumAddress(account_from['address'])
        _to = Web3.toChecksumAddress(company.public_address)
        _interest = tokenB_for_transfer.interest
        _amount = int(tokenB_for_transfer.amount)
        _id = tokenB_id
        _class = tokenB_for_transfer.class_type
        c_class = 3
        _date = date_span
        ##上鏈資料
        ##contract manipulation
        transfer_event = transfer_865(company_address, price, fee) ##先轉錢
        transfer_tx_receipt = bToC(core_contract, _from, _to ,_amount, _interest, _id, _class, c_class,  _date)
        ##
        Core = w3.eth.contract(core_contract, abi=abi)
        logs = Core.events.tokenB_event().processReceipt(transfer_tx_receipt) #拿log
        event = logs[0]['args']
        log_amount = event['amount']
        transactionHash = str(logs[0]['transactionHash'].hex())
        token_id = event['id']
        new_tknB = TokenB.objects.create(
            amount=_amount, 
            class_type=3, 
            token_id=token_id, 
            interest=_interest, 
            date_span=date_span, 
            transfer_count=tokenB_transfer_count+1, 
            initial_order= initial_order,
            curr_company = company,
            pre_company = Acc_rec_sold.pre_own, 
            transactionHash = transactionHash,
            tokenB_balance = log_amount
        ) 
        tokenB_balance = tokenB_for_transfer.tokenB_balance - log_amount
        already_transfer = tokenB_for_transfer.already_transfer + log_amount
        transfer_count = tokenB_transfer_count+1
        tokenB_for_transfer.already_transfer = already_transfer
        tokenB_for_transfer.tokenB_balance =  tokenB_balance
        tokenB_for_transfer.transfer_count = transfer_count
        tokenB_for_transfer.save()

       
        Acc_rec_sold.state = 2 
        Acc_rec_sold.save() ##更新出售的應收帳款

        content = {"txhash":logs[0]['transactionHash'].hex()} ##顯示到前端
        return render(request, 'tx_result.html', content)
##通知
@method_decorator(csrf_exempt, name='dispatch')
class my_notification(generic.View):
    def get(self, request, *args, **kwargs):
        ##大於9個通知刪除##
        company = Company.objects.get(user = request.user)
        context = {'msg':company}
        return render(request,'my_notification.html',context)
    def post(self, request, *args, **kwargs):
        notify_ID = request.POST.get("notify_ID")
        unread_obj = Notification.objects.get(pk = notify_ID)
        unread_obj.mark_as_read()        
        context = {'notify_ID':notify_ID}
        return HttpResponse(json.dumps(context),content_type="application/json")
## 基本資料
class company_info(generic.View):
    def get(self, request, *args, **kwargs):
        user = request.user
        company = Company.objects.get(user = user)
        context = {'msg':company}

        return render(request, 'company_info.html',context)
    def post(self, request, *args, **kwargs):
        user = request.user
        company = Company.objects.get(user = user)
        company_number = request.POST.get('company_number')
        company_type = request.POST.get('company_type')
        company_capital = request.POST.get('company_capital')
        company_chairman = request.POST.get('company_chairman')
        company_address = request.POST.get('company_address')
        company_supervisor = request.POST.get('company_supervisor')
        company_start_date = request.POST.get('company_start_date')
        company_responsible_person = request.POST.get('company_responsible_person')
        company_responsible_person_email = request.POST.get('company_responsible_person_email')
        company_img = request.FILES['logo']
        
        company.uni_num = company_number
        company.company_type = company_type
        company.capital = company_capital
        company.chairman = company_chairman
        company.company_location = company_address
        company.supervisor = company_supervisor
        company.establish_date = company_start_date
        company.responsible_person = company_responsible_person
        user.email = company_responsible_person_email
        company.image = company_img

        company.save()
        user.save()

        context = {'msg':company}
        return render(request, 'company_info.html',context)
        



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
        if (company_all_tokenB):
            context['sum_receive_order'] = json.dumps(int(sum_receive_order['tokenB_sum']))
        else:
            context['sum_receive_order'] = 0
        context['msg'] = company
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

    def post(self, request, *args, **kwargs):
        form = set_order_rate(request.POST)
        if form.is_valid():
            inventory_id = form.cleaned_data['orders_id']
            #前端還沒改 名字不一 羽
            unitPrice = form.cleaned_data['rec_company_name']
            quantities = form.cleaned_data['rec_com_address']         
            #訂單-->貨物認證
            order = Company_orders.objects.filter(id = inventory_id)[0] ##找到資料庫的這筆訂單
            order_for_update = Company_orders.objects.filter(id = inventory_id) ## update 只支援queryset
            
            user = self.request.user
            end = order.end_date ## 結束日
            now = datetime.date.today() ## 透過平台的發訂單日
            date_span = end - now ## 時間段
            date_span = date_span.days 
            company = Company.objects.filter(user = user)[0] ##發出的公司
            company_for_update = Company.objects.filter(user = user)
            contract_address = company.contract_address ##發出的公司合約地址
            core_address = Web3.toChecksumAddress(company.public_address) ## 核心 公鑰 checksumaddresss

            #製造1155
            log_addNew = llss_addNew(quantities,unitPrice, core_address)
            event_addNew = log_addNew[0]['args']
            log_1155id = event_addNew['id']
            transactionHash_addNew = str(log_addNew[0]['transactionHash'].hex())

            # 1155 換成tokenB之前的轉移
            log_transfer1155 = llss_transferFrom(core_address, Web3.toChecksumAddress(account_from['address']), log_1155id, quantities)
            event__transfer1155 = log_transfer1155[0]['args']
            transactionHash_transfer1155 = str(log_transfer1155[0]['transactionHash'].hex())

            # 1155轉移後 產生tokenB
            amount_1155toB = int(unitPrice)*int(quantities)
            rate_1155toB = 10
            

            log_1155toB = core_1155ToB(contract_address, amount_1155toB, rate_1155toB, date_span)
            event_1155toB = log_1155toB[0]['args']
            log_1155toB_amount, log_1155toB_rate, log_1155toB_id, log_1155toB_receiver=  event_1155toB['amount'], event_1155toB['interest'], event_1155toB['id'], event_1155toB['receiver']
            transactionHash = str(log_1155toB[0]['transactionHash'].hex())

            # db manipulation  
            order_for_update.update(rate = 10 , start_date = datetime.date.today(), state = 6) ##更新設定利率 起始時間 狀態變為完成驗證 tokenB_balance = amount 移到TokenB紀錄
            core_amount_a = float(call_tokenA(contract_address, core_address)) ## 拿到最新的tokenA數量
            company_for_update.update(amount_a = core_amount_a) ##更新資料庫

            new_tknB = TokenB.objects.create(
                amount=log_1155toB_amount, 
                class_type=5, 
                token_id=log_1155toB_id, 
                interest=log_1155toB_rate, 
                date_span=date_span, 
                transfer_count=0, 
                initial_order=order,
                curr_company = company,
                pre_company = company,
                transactionHash = transactionHash,
                tokenB_balance = log_1155toB_amount,   ## 原本在Company_orders資料表下
            )
            #下四不知道對不對
            context = {"log_amount":log_1155toB_amount,"log_rate":log_1155toB_rate,"log_receiver":log_1155toB_receiver}
            receiver = order.receive_compamy.user ## 找到訂單接收者
            notify.send(user, recipient=receiver, verb='發送了訂單') ## 向訂單接收者發送消息
            
            content = {"txhash":transactionHash} ##顯示到前端
            return render(request, 'tx_result.html', content)



##驗證成功
@method_decorator(csrf_exempt, name='dispatch')
class verification_OK(generic.ListView):
    model = TokenB
    template_name = 'verification_OK.html'
    context_object_name = 'rec_orders'
    paginate_by = 6

    def get_queryset(self):
        user = self.request.user
        company = Company.objects.get(user = user)
        verification_complete = Company_orders.objects.filter(state = 6)
        order_tokenB = TokenB.objects.filter(Q(initial_order__in = verification_complete) & Q(curr_company = company) & (Q(class_type = 5) | Q(class_type =3))).order_by('date_span')
        return  order_tokenB 


    def get_context_data(self, **kwargs):
        _company_list = []
        context =  super(verification_OK,self).get_context_data(**kwargs)
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

                contract_address = initial_company_contract_address

                ### contract manipulation
                _loaner = Web3.toChecksumAddress(company.public_address)
                _amount = int(form.cleaned_data['orders_price'])
                _class =  tokenB.class_type
                _id = int(tokenB.token_id)
                _interest = int(form.cleaned_data['orders_interest'][:-1])
                _date = date_span

               
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
                tokenB.already_loan = already_loan # update company_orders already loan
                tokenB.tokenB_balance =  tokenB_balance
                tokenB.save()

                content = {"txhash":transactionHash} ##顯示到前端
                return render(request, 'tx_result.html', content)

            # return HttpResponse('good')
            elif form.cleaned_data['optype'] == 'bToC':
                bToC_id = int(form.cleaned_data['bToC_id'])
                TOKENB_id = int(form.cleaned_data['bToC_TOKENB_id']) 
                order = Company_orders.objects.filter(id = bToC_id)[0] ##找到資料庫的這筆訂單
                order_for_update = Company_orders.objects.get(id = bToC_id)  ##ERP要更新的訂單
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
                transactionHash =  str(logs[0]['transactionHash'].hex())

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
                content = {"txhash":transactionHash} ##顯示到前端
                return render(request, 'tx_result.html', content)

##還錢頁面
class payback_loan(generic.View):
    def get(self, request, *args, **kwargs):
        user = self.request.user
        company = Company.objects.get(user = user)
        company_address = company.public_address   ##請求頁面的核心地址
        company_address = w3.toChecksumAddress(company_address)
        loan_tokenB = TokenB.objects.filter(class_type = 4, curr_company = company) ##filter所有融資tokenB
        parent_tokenB = [] ## 來源
        payback_token = {}  ## payback_tokenB包成dict
        all_payback_token = [] ## 包成大list
        
        all_uni_token_div = []
        uni_payback ={}


        context = {}
        for ele in loan_tokenB:
            contract_address = ele.initial_order.send_company.contract_address ##找到初始發出者的合約
            tokenB_token_id = int(ele.token_id)   ##所有融資tokenB的鏈上id
            former_tokenB_id = loan_former_tokenB(contract_address,company_address,tokenB_token_id)
            parent_tokenB.append(former_tokenB_id)
            payback_token['state'] = ele.get_state_display ## 融資token的狀態 index 0
            payback_token['loan_amount'] = ele.amount ##融資金額
            payback_token['notyet_paypack'] = ele.tokenB_balance
            all_payback_token.append(payback_token)  ##包進大list
            payback_token = {}

            ## 小卡
            curr_cer = LoanCertificate.objects.filter(loan_id = ele.token_id)[0]
            curr_span = curr_cer.date_span - curr_cer.curr_span
            uni_payback['curr_span'] = curr_span

            uni_payback['token_id'] = tokenB_token_id
            all_loan_payable = LoanPayable.objects.filter(tokenB = ele)
            uni_payback['payback'] = all_loan_payable
            all_uni_token_div.append(uni_payback)
            uni_payback = {}


        former_token = TokenB.objects.filter(token_id__in = parent_tokenB) ##!!!!來自同一筆會被算成一筆 
        former_token_list = []
        for ele in parent_tokenB:
            former_token = TokenB.objects.get(token_id = ele)
            former_token_list.append(former_token)

        for idx, ele in enumerate(former_token_list):
            update_payback_token = all_payback_token[idx]
            update_payback_token['former_id'] = ele.id ## 資料庫裡的自動id
            update_payback_token['product'] = ele.initial_order.product ###最一開始的項目名稱
            update_payback_token['class_type'] = ele.get_class_type_display ##來源的種類
            update_payback_token['date_span'] = ele.date_span//30 + 1 ## 前端改期數
            update_payback_token['num_class_type'] = ele.class_type ##來源的種類
            all_payback_token[idx] = update_payback_token ##取代原本的

        context['my_pay_back'] = all_payback_token
        context['uni_payback_card'] = all_uni_token_div
        return  render(request,'payback.html',context)
    
    def post(self, request, *args, **kwargs):
        allUser = auth.get_user_model() # return all user
        user = self.request.user
        company = Company.objects.filter(user = user)[0]
        form = paybackForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            _loan_id = int(form.cleaned_data['_loan_id'])
            _amount = int(form.cleaned_data['_amount'])
            ### 操控invest token合約
            ### 若比較多，則分配給核心及平台(未完成)
            ### 在tokenB將本金扣掉
            curr_tokenB = TokenB.objects.get(token_id = _loan_id)
            curr_tokenB.tokenB_balance -= _amount
            curr_tokenB.save()
            # curr_cer是為了取得當前期數
            curr_cer = LoanCertificate.objects.filter(loan_id = curr_tokenB.token_id)[0]
            # 當前期數
            curr_term = curr_cer.date_span - curr_cer.curr_span
            curr_loan = LoanPayable.objects.get(tokenB = curr_tokenB, term = curr_term)
            curr_term_int = Decimal(curr_loan.term_interest)
            curr_term_pri = Decimal(curr_loan.term_principle)
            # 當期應還
            curr_total_payable = curr_term_pri + curr_term_int
            print(curr_total_payable)
            ### 檢查這次還款金額
            # 大於本金加利息
            '''
            這邊還要加上erc865的部分 及 鏈上鏈下差額部分 及 吳紹宏core
            '''                
            # if _amount < curr_term_int:
            #     tx_receipt = paybackDividend(_loan_id, int(_amount*DECIMALS))
            #     print('<利息')
            #     print(tx_receipt)
            # else:
            amount = _amount - curr_term_int
            tx_receipt = payback(_loan_id, int(amount*DECIMALS))
            print('>利息')
            print(tx_receipt)

            ### 更改loan_certificate的期數
            update_cer_set = LoanCertificate.objects.filter(loan_id = curr_tokenB.token_id)
            for cer in update_cer_set:
                ### 分潤給投資人
                '''
                暫時用company當user
                '''
                for tranche in Tranche.objects.filter(loanCertificate=cer):
                    tranche_owner = tranche.investor
                    # 這裡之後要改，用user就可以拿到public address
                    if tranche_owner.groups.filter(name = 'firm').exists():
                        tranche_owner = Company.objects.filter(user = tranche_owner)[0]
                    else:
                        tranche_owner = Invest_user.objects.filter(user = tranche_owner)[0] ##偷懶

                    company = Web3.toChecksumAddress(tranche_owner.public_address)
                    ###########
                    _term = cer.date_span - cer.curr_span
                    term_interest = Invest.functions.getTermInvestorDiv(company, int(tranche.loan_id) , cer.riskClass, _term).call({'from': account_from['address']})
                    print(term_interest)
                    pre_accu = Decimal(tranche.accu_earning)
                    tranche.accu_earning = pre_accu + Decimal(term_interest/DECIMALS)
                    tranche.save()
        
                cer.curr_span -= 1
                cer.save()


            ### 更新interest arr
            #因為鏈上已經到下一期 所以練下也要，curr_term代表當前期數
            curr_term += 1
            principle_left = Invest.functions.getTotalPrincipleNotPaid(int(curr_tokenB.token_id)).call({'from': account_from['address']})/DECIMALS
            span_left = LoanCertificate.objects.filter(loan_id = curr_tokenB.token_id)[0].curr_span
            date_span = LoanCertificate.objects.filter(loan_id = curr_tokenB.token_id)[0].date_span
            pmt = calculatePmt(curr_interest/1200, principle_left, span_left)
            for i in range(LoanPayable.objects.count()):
                pay = LoanPayable.objects.get(tokenB = curr_tokenB, term=i)
                curr_interest = pay.tokenB.interest
                if i < curr_term:
                    pay.term_principle = 0
                    pay.term_interest = 0
                    pay.save()
                else: 
                    term_interest = principle_left*curr_interest/1200
                    pay.term_interest = term_interest
                    pay.term_principle = pmt - term_interest
                    pay.save()
                    principle_left -= term_principle

            context = {"txhash":tx_receipt['transactionHash'].hex()}
            return render(request, 'tx_result.html', context)

### 這裏loan tokenB的query給你下

def tx_result(request):
    return render(request,'tx_result.html')

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
        txhash = tx_receipt['transactionHash'].hex()
        event = logs[0]['args']

        ## db manpulation

       
        if  Company.objects.filter(public_address = res['CustomField1']).exists():
            company = Company.objects.filter(public_address = res['CustomField1'])[0]
            transactionHash = str(logs[0]['transactionHash'].hex())
            new_deposit = Deposit.objects.create(
                deposit_company = company,
                deposit_amount = int(int(event['value'])/DECIMALS),
                transactionHash = transactionHash
            )
        else:
            investor = Invest_user.objects.get(public_address = res['CustomField1'])
            investor_addr = w3.toChecksumAddress(investor.public_address)
            amount =  int(call_ERC865(investor_addr)  / DECIMALS)
            investor.amount_865 = int(int(event['value'])/DECIMALS)
            investor.save()

        content = {"txhash":txhash,'res':res} ##顯示到前端
        return render(request, 'tx_result.html', content)

## 保證金扣款
def transfer_865( _from, _value, fee):
    erc865Contract = w3.eth.contract(address=erc865_contract_address, abi=erc865_abi)
    transaction = erc865Contract.functions.transferToPlatform(_from, _value, fee).buildTransaction({
        'from': account_from['address'],
        'gas': 3000000,
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

'''ERC-865 contract manipulate end'''

'''core contract manipulate'''
##查看tokenA數量
def call_tokenA(_contract_addr, _core_address):
    Core = w3.eth.contract(_contract_addr,abi=abi)
    tokenA_amount = Core.functions.token_A(_core_address).call()
    return tokenA_amount

##部署核心合約
def deploy_contract(_core_address,_amount):
    print('deploy_contract_nonce:', w3.eth.getTransactionCount(account_from['address']))
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
                'gas':4000000,
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
            'gas':4000000,
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

'''core contract manipulate end'''

''' invest contract manipulation '''
## mintCertificate (uint _loan_id, address _borrow_company, uint _principle, uint _interest, uint _datespan, uint _class)
def mintCertificate(_loan_id, _borrow_company, _principle, _interest, _monthspan, _class, _pmt):
    # print('mintCertificate--nonce:', w3.eth.getTransactionCount(account_from['address']))
    # Invest = w3.eth.contract(address=invest_contract_address, abi=invest_abi)
    construct_txn = Invest.functions.mintCertificate(_loan_id, _borrow_company, _principle, _interest, _monthspan, _class, _pmt).buildTransaction(
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

def buyTranche_method(_investor, _loan_id, _class, _amount):
    # Invest = w3.eth.contract(address=invest_contract_address, abi=invest_abi)
    construct_txn = Invest.functions.buyTranche(_investor, _loan_id, _class, _amount).buildTransaction(
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

def payback(_loan_id, _amount):
    construct_txn = Invest.functions.payback(_loan_id, _amount).buildTransaction(
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
    
    ##接到normalpayback的event
    nor_logs = Invest.events.NormalPayback().processReceipt(tx_receipt)
    for event in nor_logs:
        _loan_id = int(event['args']['_loan_id'])
        _class = int(event['args']['_class'])
        _principle_not_paid = int(event['args']['_principleNotPaid'])
        _termLeft = int(event['args']['_termLeft'])
        _interest = int(event['args']['_interest'])/1200
        _pmt = int(math.floor(calculatePmt(_interest, _principle_not_paid, _termLeft)))
        
        invest_txn = Invest.functions.updateAndAllocate(_loan_id, _class, _principle_not_paid, _pmt).buildTransaction(
            {
                'from': account_from['address'],
                'nonce': w3.eth.getTransactionCount(account_from['address']),
            }
        )
        # 簽名
        update_tx_create = w3.eth.account.signTransaction(invest_txn, account_from['private_key'])
        # transaction送出並且等待回傳
        update_tx_hash = w3.eth.sendRawTransaction(update_tx_create.rawTransaction)
        update_tx_receipt = w3.eth.waitForTransactionReceipt(update_tx_hash ,timeout=600)

    ear_logs = Invest.events.EarlyPayback().processReceipt(tx_receipt)
    if ear_logs:
        for event in ear_logs:
            _loan_id = int(event['args']['_loan_id'])
            _class = int(event['args']['_class'])
            _principle = int(event['args']['_principle'])
            _termLeft = int(event['args']['_termLeft'])
            _interest = int(event['args']['_interest'])/1200
            _pmt = int(math.floor(calculatePmt(_interest, _principle_not_paid, _termLeft)))

            Invest.functions.earlyUpdateInterestArr(_loan_id, _class, _principle, _pmt).buildTransaction(
                {
                    'from': account_from['address'],
                    'nonce': w3.eth.getTransactionCount(account_from['address']),
                }
            )
            # 簽名
            update_tx_create = w3.eth.account.signTransaction(invest_txn, account_from['private_key'])
            # transaction送出並且等待回傳
            update_tx_hash = w3.eth.sendRawTransaction(update_tx_create.rawTransaction)
            update_tx_receipt = w3.eth.waitForTransactionReceipt(update_tx_hash ,timeout=600)
    return tx_receipt    

def paybackDividend(_loan_id, _amount):
    construct_txn = Invest.functions.paybackDividend(_loan_id, _amount).buildTransaction(
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
    if user.groups.filter(name = 'firm').exists():
        company = Company.objects.filter(user = user)[0]
    else:
        company = Invest_user.objects.filter(user = user)[0]

    curr_user_addr = company.public_address
    curr_user_addr = w3.toChecksumAddress(curr_user_addr)
    if request.POST:
        check_addr = w3.toChecksumAddress(request.POST['check_addr'])
        if check_addr == curr_user_addr:
            context['check'] = 'passed'
            print('context:',context)
            if 'fallback' in request.session.keys():
                del request.session['fallback']
            return HttpResponse(json.dumps(context), content_type="application/json")
        else: 
            request.session['fallback'] = '非本人'
            context['check'] = 'reject'
            return HttpResponse(json.dumps(context), content_type="application/json")



##將貨物驗證上鏈製造1155
def llss_addNew(_initialSupply, _unitPrice, _receiver):
    llss = w3.eth.contract(address = llss_contract_address, abi=llss_abi)
    construct_txn = llss.functions.addNew(int(_initialSupply), int(_unitPrice), _receiver).buildTransaction(
        {
            'from': account_from['address'],
            'gas':300000,
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )    
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])

    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash,timeout=600)
    logs = llss.events.TransferSingle().processReceipt(tx_receipt) 

    return logs
    
## 1155的轉移
def llss_transferFrom(_from, _to, _id, _quantites):
    llss = w3.eth.contract(address = llss_contract_address, abi=llss_abi)
    construct_txn = llss.functions.transferFrom(_from, _to, _id, int(_quantites)).buildTransaction(
         {
            'from': account_from['address'],
            'gas':400000,
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash,timeout=600)
    logs = llss.events.TransferSingle().processReceipt(tx_receipt) 

    return logs

## core合約 1155轉移後call的 製造tokenB 的 function
def core_1155ToB(_contract_addr, _amount, _interest, _date):
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    construct_txn = Core.functions.llssToB(_amount, _interest, _date).buildTransaction(
        {
            'from': account_from['address'],
            'nonce': w3.eth.getTransactionCount(account_from['address']),
        }
    )
    tx_create = w3.eth.account.signTransaction(construct_txn, account_from['private_key'])
    tx_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash,timeout=600)
    logs = Core.events.tokenB_event().processReceipt(tx_receipt) 

    return logs



## 尋找成功融資的來源tokenB

def loan_former_tokenB(_contract_addr,company_address,_tokenB_token_id):
    Core = w3.eth.contract(address = _contract_addr, abi=abi)
    curr_tx_count = Core.functions._findTransaction(company_address, 4, _tokenB_token_id).call({'from': account_from['address']})
    former_tokenB = Core.functions.token_B(company_address, 4, curr_tx_count).call({'from': account_from['address']})
    former_tokenB_id = former_tokenB[7]
    return former_tokenB_id
    
