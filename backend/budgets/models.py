from decimal import Decimal

from django.db import models


class LLMProviderConfig(models.Model):
    PROVIDER_CHOICES = [
        ("gemini", "Gemini"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("ollama", "Ollama"),
    ]

    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    api_key_encrypted = models.TextField(blank=True)
    base_url = models.URLField(blank=True)
    selected_model = models.CharField(max_length=255, blank=True)
    model_catalog = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=False)
    last_model_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "provider", "name"]

    def __str__(self):
        return f"{self.name} [{self.provider}]"


class BudgetScenario(models.Model):
    name = models.CharField(max_length=255)
    period = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "name"]

    def __str__(self):
        return f"{self.name} ({self.period})"


class BudgetLineItem(models.Model):
    scenario = models.ForeignKey(
        BudgetScenario, related_name="line_items", on_delete=models.CASCADE
    )
    department = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    budget_amount = models.DecimalField(max_digits=14, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["department", "category", "id"]

    @property
    def variance(self):
        return Decimal(self.actual_amount) - Decimal(self.budget_amount)

    @property
    def variance_percent(self):
        budget_amount = Decimal(self.budget_amount)
        if budget_amount == Decimal("0"):
            return None
        return (self.variance / budget_amount) * Decimal("100")

    @property
    def status(self):
        if self.variance > 0:
            return "over_budget"
        if self.variance < 0:
            return "under_budget"
        return "on_track"

    def __str__(self):
        return f"{self.department} / {self.category}"


class AnalysisRun(models.Model):
    DEFAULT_QUESTION = (
        "Review this budget scenario and identify the most important variances and risks."
    )

    scenario = models.ForeignKey(
        BudgetScenario, related_name="analysis_runs", on_delete=models.CASCADE
    )
    provider_config = models.ForeignKey(
        LLMProviderConfig,
        related_name="analysis_runs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    question = models.CharField(max_length=500, default=DEFAULT_QUESTION)
    provider = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True)
    input_snapshot = models.JSONField()
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.scenario} analysis at {self.created_at:%Y-%m-%d %H:%M}"
