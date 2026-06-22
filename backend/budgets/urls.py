from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalysisRunViewSet,
    BudgetLineItemViewSet,
    BudgetScenarioViewSet,
    LLMProviderConfigViewSet,
    ScenarioLineItemViewSet,
)


router = DefaultRouter()
router.register("scenarios", BudgetScenarioViewSet, basename="scenario")
router.register("line-items", BudgetLineItemViewSet, basename="line-item")
router.register("analysis-runs", AnalysisRunViewSet, basename="analysis-run")
router.register("provider-configs", LLMProviderConfigViewSet, basename="provider-config")

line_item_list = ScenarioLineItemViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    path("", include(router.urls)),
    path(
        "scenarios/<int:scenario_pk>/line-items/",
        line_item_list,
        name="scenario-line-items",
    ),
]
