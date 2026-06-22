from django.http import Http404, HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AnalysisRun, BudgetLineItem, BudgetScenario, LLMProviderConfig
from .serializers import (
    AnalysisFollowUpRequestSerializer,
    AnalysisRunSerializer,
    BudgetLineItemSerializer,
    BudgetScenarioSerializer,
    LLMProviderConfigSerializer,
    ProviderOptionSerializer,
)
from .services.ai_analysis import analyze_scenario
from .services.analysis_export import (
    build_markdown_export,
    build_pdf_export,
    export_filename,
)
from .services.follow_up import answer_follow_up
from .services.provider_catalog import provider_choices
from .services.provider_clients import list_models
from .services.secrets import decrypt_secret


class BudgetScenarioViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetScenarioSerializer

    def get_queryset(self):
        return BudgetScenario.objects.prefetch_related("line_items", "analysis_runs")

    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        scenario = self.get_object()
        provider_config = None
        provider_config_id = request.data.get("provider_config_id")
        if provider_config_id:
            provider_config = LLMProviderConfig.objects.filter(pk=provider_config_id).first()
            if not provider_config:
                return Response(
                    {"detail": "Provider config not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        run = analyze_scenario(
            scenario,
            request.data.get("question"),
            provider_config=provider_config,
        )
        return Response(AnalysisRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="analysis-runs")
    def analysis_runs(self, request, pk=None):
        scenario = self.get_object()
        runs = scenario.analysis_runs.all()
        return Response(AnalysisRunSerializer(runs, many=True).data)


class ScenarioLineItemViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetLineItemSerializer

    def get_queryset(self):
        return BudgetLineItem.objects.filter(
            scenario_id=self.kwargs["scenario_pk"]
        ).select_related("scenario")

    def perform_create(self, serializer):
        serializer.save(scenario_id=self.kwargs["scenario_pk"])


class BudgetLineItemViewSet(viewsets.ModelViewSet):
    queryset = BudgetLineItem.objects.select_related("scenario")
    serializer_class = BudgetLineItemSerializer


class AnalysisRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnalysisRun.objects.select_related("scenario")
    serializer_class = AnalysisRunSerializer

    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request, pk=None):
        try:
            run = self.get_queryset().get(pk=pk)
        except AnalysisRun.DoesNotExist as exc:
            raise Http404 from exc
        export_format = (request.query_params.get("file_format") or "md").lower()

        if export_format == "pdf":
            payload = build_pdf_export(run)
            response = HttpResponse(payload, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{export_filename(run, "pdf")}"'
            )
            return response

        if export_format == "md":
            payload = build_markdown_export(run)
            response = HttpResponse(payload, content_type="text/markdown; charset=utf-8")
            response["Content-Disposition"] = (
                f'attachment; filename="{export_filename(run, "md")}"'
            )
            return response

        return Response(
            {"detail": "Unsupported export format. Use md or pdf."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"], url_path="follow-up")
    def follow_up(self, request, pk=None):
        serializer = AnalysisFollowUpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = self.get_object()
        result = answer_follow_up(run, serializer.validated_data["question"])
        return Response(result, status=status.HTTP_200_OK)


class LLMProviderConfigViewSet(viewsets.ModelViewSet):
    queryset = LLMProviderConfig.objects.all()
    serializer_class = LLMProviderConfigSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.provider == "ollama" and not instance.base_url:
            instance.base_url = "http://host.docker.internal:11434"
            instance.save(update_fields=["base_url"])

    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request):
        serializer = ProviderOptionSerializer(provider_choices(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        active_config = self.get_queryset().filter(is_active=True).first()
        if not active_config:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(self.get_serializer(active_config).data)

    @action(detail=True, methods=["post"], url_path="set-active")
    def set_active(self, request, pk=None):
        instance = self.get_object()
        self.get_queryset().update(is_active=False)
        instance.is_active = True
        instance.save(update_fields=["is_active"])
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], url_path="refresh-models")
    def refresh_models(self, request, pk=None):
        instance = self.get_object()
        instance.api_key = decrypt_secret(instance.api_key_encrypted)
        models = list_models(instance)
        instance.model_catalog = models
        instance.last_model_sync_at = timezone.now()
        if not instance.selected_model and models:
            instance.selected_model = models[0]["id"]
        instance.save(
            update_fields=["model_catalog", "last_model_sync_at", "selected_model"]
        )
        return Response(self.get_serializer(instance).data)
