from django.contrib import admin

from utils.generals import get_model

Skill = get_model('master', 'Skill')
Scope = get_model('master', 'Scope')


# .........................................................
# Extend Scope
# .........................................................
class SkillInline(admin.StackedInline):
    model = Skill


class ScopeExtend(admin.ModelAdmin):
    model = Scope
    inlines = [SkillInline,]


admin.site.register(Scope, ScopeExtend)
