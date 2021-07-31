from django.contrib import admin
from .models import Company ,Company_orders, TokenB, Deposit, TokenA, LoanCertificate
# Register your models here.
admin.site.register(Company)
admin.site.register(Company_orders)
admin.site.register(TokenB)
admin.site.register(Deposit)
admin.site.register(TokenA)
admin.site.register(LoanCertificate)