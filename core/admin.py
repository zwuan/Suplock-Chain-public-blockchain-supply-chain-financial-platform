from django.contrib import admin
from .models import Company ,Company_orders, TokenB, Deposit, TokenA, LoanCertificate,Tranche,LoanPayable, Invest_user,Acc_rec_for_sale, Payback_record,Dividend_record
# Register your models here.
admin.site.register(Company)
admin.site.register(Company_orders)
admin.site.register(TokenB)
admin.site.register(Deposit)
admin.site.register(TokenA)
admin.site.register(LoanCertificate)
admin.site.register(Tranche)
admin.site.register(LoanPayable)
admin.site.register(Invest_user)
admin.site.register(Acc_rec_for_sale)
admin.site.register(Payback_record)
admin.site.register(Dividend_record)