from django.core.management.base import BaseCommand

from budgets.models import BudgetLineItem, BudgetScenario


SCENARIOS = [
    {
        "name": "Q2 Operating Budget",
        "period": "2026 Q2",
        "description": "Demo operating budget with typical review variances.",
        "items": [
            ("Marketing", "Paid Ads", "50000.00", "65000.00", "Campaign spend increased after an unplanned product launch."),
            ("Sales", "Travel", "20000.00", "27500.00", "More onsite customer visits than forecast."),
            ("Engineering", "Tools", "30000.00", "28500.00", "Annual developer tools renewal came in slightly under plan."),
            ("Customer Success", "Training", "12000.00", "18000.00", "Urgent customer onboarding sessions were added."),
            ("Operations", "Software", "15000.00", "15000.00", "On track."),
        ],
    },
    {
        "name": "FY2026 Hiring Plan",
        "period": "FY2026",
        "description": "Demo hiring support budget for recruiting, research, and support spend.",
        "items": [
            ("Engineering", "Recruiting", "25000.00", "34000.00", "Agency fees higher than expected."),
            ("Product", "Research", "10000.00", "8500.00", "Some research sessions moved to next quarter."),
            ("Sales", "Commission", "40000.00", "47000.00", "Stronger bookings drove higher commissions."),
            ("G&A", "Legal", "8000.00", "16000.00", "Unexpected contract review."),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed demo budget scenarios if the database is empty."

    def handle(self, *args, **options):
        if BudgetScenario.objects.exists():
            self.stdout.write(self.style.SUCCESS("Demo data already present."))
            return

        for scenario_data in SCENARIOS:
            scenario = BudgetScenario.objects.create(
                name=scenario_data["name"],
                period=scenario_data["period"],
                description=scenario_data["description"],
            )
            for department, category, budget, actual, notes in scenario_data["items"]:
                BudgetLineItem.objects.create(
                    scenario=scenario,
                    department=department,
                    category=category,
                    budget_amount=budget,
                    actual_amount=actual,
                    notes=notes,
                )

        self.stdout.write(self.style.SUCCESS("Seeded demo budget scenarios."))
