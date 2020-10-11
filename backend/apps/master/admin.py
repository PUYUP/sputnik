from django.contrib import admin

from utils.generals import get_model

Topic = get_model('master', 'Topic')
Scope = get_model('master', 'Scope')

admin.site.register(Topic)
admin.site.register(Scope)
