from django.contrib import admin
from asha.models import Category, Page , UserProfile
# To  tell the Django admin application what
#models we wish to make available to the admin interface
class CategoryAdmin(admin.ModelAdmin):
    list_display=('name','views','likes')
admin.site.register(Category,CategoryAdmin)
class PageAdmin(admin.ModelAdmin):
    list_display=('title','category','url')
admin.site.register(Page,PageAdmin)
admin.site.register(UserProfile)
