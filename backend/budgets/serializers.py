from rest_framework import serializers

from .models import AnalysisRun, BudgetLineItem, BudgetScenario, LLMProviderConfig
from .services.provider_catalog import provider_choices
from .services.secrets import decrypt_secret, encrypt_secret
from .services.variance import money_string, percent


class BudgetLineItemSerializer(serializers.ModelSerializer):
    variance = serializers.SerializerMethodField()
    variance_percent = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = BudgetLineItem
        fields = [
            "id",
            "scenario",
            "department",
            "category",
            "description",
            "budget_amount",
            "actual_amount",
            "variance",
            "variance_percent",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "scenario", "created_at", "updated_at"]

    def get_variance(self, obj):
        return money_string(obj.variance)

    def get_variance_percent(self, obj):
        return percent(obj.variance_percent)

    def get_status(self, obj):
        return obj.status


class BudgetScenarioSerializer(serializers.ModelSerializer):
    line_item_count = serializers.SerializerMethodField()
    total_budget = serializers.SerializerMethodField()
    total_actual = serializers.SerializerMethodField()
    total_variance = serializers.SerializerMethodField()
    line_items = BudgetLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = BudgetScenario
        fields = [
            "id",
            "name",
            "period",
            "description",
            "line_item_count",
            "total_budget",
            "total_actual",
            "total_variance",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_line_item_count(self, obj):
        return obj.line_items.count()

    def get_total_budget(self, obj):
        return money_string(sum((item.budget_amount for item in obj.line_items.all()), 0))

    def get_total_actual(self, obj):
        return money_string(sum((item.actual_amount for item in obj.line_items.all()), 0))

    def get_total_variance(self, obj):
        return money_string(sum((item.variance for item in obj.line_items.all()), 0))


class AnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = [
            "id",
            "scenario",
            "provider_config",
            "question",
            "provider",
            "model",
            "input_snapshot",
            "result",
            "created_at",
        ]
        read_only_fields = fields


class AnalysisFollowUpRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)


class LLMProviderConfigSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    clear_api_key = serializers.BooleanField(write_only=True, required=False, default=False)
    has_api_key = serializers.SerializerMethodField()
    masked_api_key = serializers.SerializerMethodField()

    class Meta:
        model = LLMProviderConfig
        fields = [
            "id",
            "name",
            "provider",
            "api_key",
            "clear_api_key",
            "has_api_key",
            "masked_api_key",
            "base_url",
            "selected_model",
            "model_catalog",
            "is_active",
            "last_model_sync_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "has_api_key",
            "masked_api_key",
            "model_catalog",
            "last_model_sync_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        validated_data.pop("clear_api_key", False)
        api_key = validated_data.pop("api_key", "")
        instance = super().create(validated_data)
        if api_key:
            instance.api_key_encrypted = encrypt_secret(api_key)
            instance.save(update_fields=["api_key_encrypted"])
        if instance.is_active:
            _set_single_active(instance)
        return instance

    def update(self, instance, validated_data):
        clear_api_key = validated_data.pop("clear_api_key", False)
        api_key = validated_data.pop("api_key", None)
        instance = super().update(instance, validated_data)
        if clear_api_key:
            instance.api_key_encrypted = ""
            instance.save(update_fields=["api_key_encrypted"])
        elif api_key:
            instance.api_key_encrypted = encrypt_secret(api_key)
            instance.save(update_fields=["api_key_encrypted"])
        if instance.is_active:
            _set_single_active(instance)
        return instance

    def get_has_api_key(self, obj):
        return bool(decrypt_secret(obj.api_key_encrypted))

    def get_masked_api_key(self, obj):
        secret = decrypt_secret(obj.api_key_encrypted)
        if not secret:
            return ""
        if len(secret) <= 8:
            return "*" * len(secret)
        return f"{secret[:4]}...{secret[-4:]}"


class ProviderOptionSerializer(serializers.Serializer):
    provider = serializers.CharField()
    name = serializers.CharField()
    default_model = serializers.CharField(allow_blank=True)
    default_base_url = serializers.CharField(allow_blank=True)
    requires_api_key = serializers.BooleanField()


def _set_single_active(instance):
    LLMProviderConfig.objects.exclude(pk=instance.pk).filter(is_active=True).update(
        is_active=False
    )
