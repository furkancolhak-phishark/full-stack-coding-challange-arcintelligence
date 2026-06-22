from django.contrib import admin

from .models import AnalysisRun, BudgetLineItem, BudgetScenario, LLMProviderConfig


class BudgetLineItemInline(admin.TabularInline):
    model = BudgetLineItem
    extra = 0


@admin.register(BudgetScenario)
class BudgetScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "period", "created_at", "updated_at")
    search_fields = ("name", "period")
    inlines = [BudgetLineItemInline]


@admin.register(AnalysisRun)
class AnalysisRunAdmin(admin.ModelAdmin):
    list_display = ("scenario", "provider", "model", "created_at")
    list_filter = ("provider", "created_at")


@admin.register(LLMProviderConfig)
class LLMProviderConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "selected_model", "is_active", "updated_at")
    list_filter = ("provider", "is_active")
