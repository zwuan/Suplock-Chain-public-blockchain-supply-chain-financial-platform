from django.urls import path,include
from django.contrib import admin
from core import views
import notifications.urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('welcome/',views.index.as_view(),name = 'welcome'),
    path('invest_index/',views.invest_index.as_view(),name = 'invest_index'),
    path('invest_option/',views.invest_option.as_view(),name = 'invest_option'),
    path('invest_option/<int:pk>',views.invest_loan.as_view(),name = 'invest_loan'),
    path('invest_wallet/',views.invest_wallet.as_view(),name = 'invest_wallet'),
    path('login_company/' ,views.login_company.as_view(), name='login_company'),
    path('company_index/', views.company_index.as_view(), name = 'company_index'),
    path('logout/', views.logout, name="logout"),
    path('temp/', views.temp, name="temp"),
    path('company_orders/',views.company_order.as_view(), name='company_orders'),
    path('company_orders_rec/',views.company_order_rec.as_view(), name='company_orders_rec'),
    path('', views.hello_world,name='add_erc865'),
    path('getAbiBytecode/', views.getAbiBytecode),
    path('buyERC865/', views.buyERC865),
    path('frontend/return/', views.PaymentReturnView.as_view()),
    path('checkUser/', views.checkUser),
    path('wallet/' ,views.wallet.as_view(), name='wallet'),
    path('company_info/', views.company_info.as_view(), name = 'company_info'),
    path('company_account_pay/', views.company_account_pay.as_view(), name = 'company_account_pay'),
    path('company_account_rec/', views.company_account_rec.as_view(), name = 'company_account_rec'),
    path('notifications/', include(notifications.urls, namespace='notifications')),
    path('my_notification/', views.my_notification.as_view(),name='my_notification'),
    path('verification_ERP/', views.verification_ERP.as_view(),name='verification_ERP'),
    path('verification_OK/', views.verification_OK.as_view(),name='verification_OK'),

]
