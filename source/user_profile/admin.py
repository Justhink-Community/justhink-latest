from django.contrib import admin
from .models import Profile

# Register your models here.


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('get_account', 'web_theme', 'shop_bought_products', 'login_count', 'last_logged_in', 'total_point', 'get_created_date')
    list_filter = ('web_theme', 'shop_bought_products', 'login_count', 'last_logged_in', 'total_point')
    
    @staticmethod
    def get_readonly_fields(request, obj=None):
        if request.user.username == "FurkanEsen":
            return [f.name for f in obj._meta.fields if not f.editable]
        return [f.name for f in obj._meta.fields if not f.editable and f.name != "ip_addresses"]
 
    @admin.display(ordering='account', description='Account')
    def get_account(self, obj):
        return obj.account.username
    
     
    @admin.display(ordering='get_created_date', description='get_created_date')
    def get_created_date(self, obj):
        return obj.account.date_joined.strftime('%d.%m.%Y')


admin.site.register(Profile, ProfileAdmin)
