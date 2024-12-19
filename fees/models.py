"""Fee-related models for the application."""

from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar, Optional, Tuple

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import ProcedureCode


class FeeSchedule(models.Model):
    """Fee schedule model for procedure codes."""

    objects: ClassVar[models.Manager["FeeSchedule"]]

    # type: ignore
    name = models.CharField(  # type: ignore
        max_length=255, help_text=_("Schedule name")
    )
    description = models.TextField(  # type: ignore
        blank=True, help_text=_("Schedule description")
    )
    effective_date = models.DateField(  # type: ignore
        help_text=_("Date when schedule becomes effective")
    )
    expiration_date = models.DateField(  # type: ignore
        null=True, blank=True, help_text=_("Date when schedule expires")
    )
    is_active = models.BooleanField(  # type: ignore
        default=True, help_text=_("Whether this schedule is active")
    )
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore

    def __str__(self) -> str:
        """Return string representation."""
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({self.effective_date}) - {status}"

    def get_fee_schedule_by_name(self, name: str) -> Optional["FeeSchedule"]:
        """Get fee schedule by name."""
        return type(self).objects.filter(name=name).first()

    class Meta:
        """Model metadata."""

        verbose_name = _("Fee Schedule")
        verbose_name_plural = _("Fee Schedules")
        ordering = ["-effective_date"]
        indexes = [
            models.Index(fields=["name"]),  # type: ignore
            models.Index(fields=["effective_date"]),  # type: ignore
            models.Index(fields=["is_active"]),  # type: ignore
        ]


class FeeScheduleItem(models.Model):
    """Individual item within a fee schedule."""

    objects: ClassVar[models.Manager["FeeScheduleItem"]]

    fee_schedule = models.ForeignKey(  # type: ignore
        FeeSchedule, on_delete=models.CASCADE, related_name="items"
    )
    code = models.ForeignKey(  # type: ignore
        ProcedureCode, on_delete=models.PROTECT, related_name="fee_items"
    )
    fee = models.DecimalField(  # type: ignore
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    notes = models.TextField(  # type: ignore
        blank=True, help_text=_("Additional notes")
    )
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.fee_schedule.name} - {self.code.code}: ${self.fee}"

    class Meta:
        """Model metadata."""

        verbose_name = _("Fee Schedule Item")
        verbose_name_plural = _("Fee Schedule Items")
        ordering = ["fee_schedule", "code"]
        indexes = [
            models.Index(fields=["fee_schedule", "code"]),  # type: ignore
            models.Index(fields=["created_at"]),  # type: ignore
        ]


class PhysicianFeeReference(models.Model):
    """
    Stores physician fee references with percentile-based calculations.
    Maps to the PhysicianFeeReferences table in the white paper.
    """

    objects: ClassVar[models.Manager["PhysicianFeeReference"]]

    service_name = models.CharField(  # type: ignore
        max_length=255,
        help_text=_(
            "Name of the service (e.g., 'Follow-up Physician Visit', 'Orthopedic Consultation')"
        ),
    )
    procedure_code = models.ForeignKey(  # type: ignore
        ProcedureCode, on_delete=models.CASCADE, related_name="physician_fee_references"
    )
    # MFUS values at different percentiles
    m50 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("50th percentile MFUS value"),
    )
    m75 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("75th percentile MFUS value"),
    )
    m80 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("80th percentile MFUS value"),
    )
    m85 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("85th percentile MFUS value"),
    )
    # PFR values at different percentiles
    p50 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("50th percentile PFR value"),
    )
    p75 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("75th percentile PFR value"),
    )
    p80 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("80th percentile PFR value"),
    )
    p85 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("85th percentile PFR value"),
    )

    def get_range(
        self, low_percentile: str = "50", high_percentile: str = "75"
    ) -> Tuple[Decimal, Decimal]:
        """Calculate low and high range based on specified percentiles."""
        m_low = getattr(self, f"m{low_percentile}")
        p_low = getattr(self, f"p{low_percentile}")
        m_high = getattr(self, f"m{high_percentile}")
        p_high = getattr(self, f"p{high_percentile}")

        low_range = (m_low + p_low) / Decimal("2.0")
        high_range = (m_high + p_high) / Decimal("2.0")

        return low_range, high_range

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.service_name} ({self.procedure_code.code})"

    class Meta:
        """Model metadata."""

        verbose_name = _("Physician Fee Reference")
        verbose_name_plural = _("Physician Fee References")
        indexes = [
            models.Index(fields=["service_name"]),  # type: ignore
            models.Index(fields=["procedure_code"]),  # type: ignore
        ]


class MedicationPrice(models.Model):
    """
    Stores medication information and prices.
    Maps to the MedicationPrices table in the white paper.
    """

    objects: ClassVar[models.Manager["MedicationPrice"]]

    medication_name = models.CharField(  # type: ignore
        max_length=255, db_index=True, help_text=_("Name of the medication")
    )
    created_at = models.DateTimeField(default=timezone.now)  # type: ignore
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore

    def get_range(self) -> Tuple[Decimal, Decimal]:
        """Get the min and max price range from all quotes."""
        quotes = self.price_quotes.filter(is_active=True)  # type: ignore
        if not quotes.exists():
            return Decimal("0.00"), Decimal("0.00")

        prices = [q.quoted_price for q in quotes]
        return min(prices), max(prices)

    def __str__(self) -> str:
        """Return string representation."""
        min_price, max_price = self.get_range()
        return f"{self.medication_name} (${min_price} - ${max_price})"

    class Meta:
        """Model metadata."""

        verbose_name = _("Medication Price")
        verbose_name_plural = _("Medication Prices")
        indexes = [
            models.Index(fields=["medication_name"]),  # type: ignore
            models.Index(fields=["created_at"]),  # type: ignore
        ]


class MedicationPriceQuote(models.Model):
    """
    Stores individual price quotes for medications.
    Maps to the MedicationPriceQuotes table in the white paper.
    """

    objects: ClassVar[models.Manager["MedicationPriceQuote"]]

    medication = models.ForeignKey(  # type: ignore
        MedicationPrice, on_delete=models.CASCADE, related_name="price_quotes"
    )
    quoted_price = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Quoted price for the medication"),
    )
    source = models.CharField(  # type: ignore
        max_length=100,
        help_text=_("Source of the price quote (e.g., 'GoodRx', local pharmacy name)"),
    )
    quote_date = models.DateField(  # type: ignore
        default=timezone.now, help_text=_("Date the price was quoted")
    )
    is_active = models.BooleanField(  # type: ignore
        default=True, help_text=_("Whether this quote is currently active")
    )
    created_at = models.DateTimeField(default=timezone.now)  # type: ignore
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore

    def __str__(self) -> str:
        """Return string representation."""
        return (
            f"{self.medication.medication_name} - ${self.quoted_price} ({self.source})"
        )

    class Meta:
        """Model metadata."""

        verbose_name = _("Medication Price Quote")
        verbose_name_plural = _("Medication Price Quotes")
        indexes = [
            models.Index(fields=["medication", "quote_date"]),  # type: ignore
            models.Index(fields=["source"]),  # type: ignore
            models.Index(fields=["is_active"]),  # type: ignore
        ]


class FeeAdjustment(models.Model):
    """Model for fee adjustments."""

    objects: ClassVar[models.Manager["FeeAdjustment"]]

    ADJUSTMENT_TYPES = [
        ("PERCENTAGE", _("Percentage")),
        ("FIXED", _("Fixed Amount")),
        ("MULTIPLIER", _("Multiplier")),
    ]

    fee_schedule = models.ForeignKey(  # type: ignore
        FeeSchedule, on_delete=models.CASCADE, related_name="adjustments"
    )
    adjustment_type = models.CharField(  # type: ignore
        max_length=50, choices=ADJUSTMENT_TYPES
    )
    adjustment_value = models.DecimalField(  # type: ignore
        max_digits=5, decimal_places=2
    )
    notes = models.TextField(blank=True)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore

    def __str__(self) -> str:
        """Return string representation."""
        return (
            f"{self.fee_schedule.name} - "
            f"{self.get_adjustment_type_display()}"  # type: ignore
            f": {self.adjustment_value}"
        )

    class Meta:
        """Model metadata."""

        verbose_name = _("Fee Adjustment")
        verbose_name_plural = _("Fee Adjustments")
        ordering = ["fee_schedule", "adjustment_type"]
        indexes = [
            models.Index(fields=["fee_schedule", "adjustment_type"]),  # type: ignore
            models.Index(fields=["created_at"]),  # type: ignore
        ]
