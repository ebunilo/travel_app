from django.core.management.base import BaseCommand
from django.db import transaction
from listings.models import Listing
from decimal import Decimal
from django.utils import timezone
from django.db.models import (
    CharField, TextField, IntegerField, FloatField, DecimalField, BooleanField,
    DateField, DateTimeField, ForeignKey
)

class Command(BaseCommand):
    help = "Seed the database with sample Listing data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing listings before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get("clear"):
            self.stdout.write(self.style.WARNING("Clearing existing listings..."))
            Listing.objects.all().delete()

        samples = [
            {
                "title": "Beachfront Bungalow",
                "description": "Cozy bungalow by the sea with stunning sunsets.",
                "location": "Malibu, CA",
            },
            {
                "title": "Mountain Cabin Retreat",
                "description": "Rustic cabin with fireplace and hiking trails nearby.",
                "location": "Aspen, CO",
            },
            {
                "title": "City Center Apartment",
                "description": "Modern apartment close to museums and restaurants.",
                "location": "New York, NY",
            },
            {
                "title": "Safari Lodge",
                "description": "Experience wildlife from a comfortable lodge.",
                "location": "Maasai Mara, Kenya",
            },
        ]

        # Determine valid, concrete field names for Listing
        fields = [
            f for f in Listing._meta.get_fields()
            if hasattr(f, "attname") and not f.many_to_many and not f.one_to_many
        ]
        valid_names = {f.name for f in fields}
        excluded = {"id", "pk"}
        valid_names -= excluded

        # Identify required fields (no null, no default, not auto)
        required_fields = []
        for f in fields:
            has_default = getattr(f, "default", None) is not None
            is_auto = getattr(f, "auto_created", False) or getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False)
            if f.name in excluded:
                continue
            # ForeignKeys: respect nullability similarly
            if not getattr(f, "null", True) and not has_default and not is_auto:
                required_fields.append(f)

        def placeholder_for_field(f):
            if isinstance(f, (CharField, TextField)):
                return "N/A"
            if isinstance(f, IntegerField):
                return 0
            if isinstance(f, FloatField):
                return 0.0
            if isinstance(f, DecimalField):
                # Use 0 with correct quantization
                return Decimal("0")
            if isinstance(f, BooleanField):
                return False
            if isinstance(f, DateField) and not isinstance(f, DateTimeField):
                return timezone.now().date()
            if isinstance(f, DateTimeField):
                return timezone.now()
            if isinstance(f, ForeignKey):
                # Try to use first available related instance if exists
                rel_model = f.remote_field.model
                obj = rel_model.objects.order_by("pk").first()
                if obj:
                    return obj
                # If none exists and FK is required, we cannot auto-fill
                return None
            # Fallback
            return None

        created = 0
        for data in samples:
            # Filter to valid fields
            filtered = {k: v for k, v in data.items() if k in valid_names}

            # Ensure required fields exist
            missing_errors = []
            for f in required_fields:
                if f.name not in filtered or filtered[f.name] in (None, ""):
                    val = placeholder_for_field(f)
                    if val is None and isinstance(f, ForeignKey) and not getattr(f, "null", True):
                        missing_errors.append(f.name)
                    else:
                        filtered[f.name] = val

            if missing_errors:
                self.stdout.write(self.style.WARNING(
                    f"Skipping '{data.get('title', 'unknown')}' due to missing required ForeignKey(s): {', '.join(missing_errors)}"
                ))
                continue

            if "title" not in filtered:
                # Skip entries without a title field available
                continue

            obj, was_created = Listing.objects.get_or_create(
                title=filtered["title"],
                defaults=filtered,
            )
            created += 1 if was_created else 0

        self.stdout.write(
            self.style.SUCCESS(f"Seeding complete. Created {created} listings.")
        )