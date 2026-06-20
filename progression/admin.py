from django.contrib import admin
from .models import ProgressionStage, MemberProgression


class MemberProgressionInline(admin.TabularInline):
    model = MemberProgression
    extra = 0


@admin.register(ProgressionStage)
class ProgressionStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'organisation', 'order')
    list_filter = ('organisation',)
    search_fields = ('name', 'organisation__name')


@admin.register(MemberProgression)
class MemberProgressionAdmin(admin.ModelAdmin):
    list_display = ('member', 'stage', 'achieved_date')
    list_filter = ('stage__organisation', 'stage')
    search_fields = ('member__name',)
    date_hierarchy = 'achieved_date'
