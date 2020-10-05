from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from utils.generals import get_model

Attachment = get_model('resume', 'Attachment')
Education = get_model('resume', 'Education')
Experience = get_model('resume', 'Experience')
Certificate = get_model('resume', 'Certificate')
Expertise = get_model('resume', 'Expertise')


# .........................................................
# Inlined Attachment
# .........................................................
class AttachmentInline(GenericTabularInline):
    model = Attachment
    extra = 1
    ct_fk_field = 'object_id'
    ct_field = 'content_type'


# .........................................................
# Extend Education
# .........................................................
class EducationExtend(admin.ModelAdmin):
    model = Education
    inlines = [AttachmentInline]


# .........................................................
# Extend Experience
# .........................................................
class ExperienceExtend(admin.ModelAdmin):
    model = Experience
    inlines = [AttachmentInline]


# .........................................................
# Extend Certificate
# .........................................................
class CertificateExtend(admin.ModelAdmin):
    model = Certificate
    inlines = [AttachmentInline]


admin.site.register(Attachment)
admin.site.register(Education, EducationExtend)
admin.site.register(Experience, ExperienceExtend)
admin.site.register(Certificate, CertificateExtend)
admin.site.register(Expertise)
