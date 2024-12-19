"""Surgical fee-related models for the application."""

from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar, Optional, Tuple, cast

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from surgeries.models import SurgeryBundle


class SurgicalService(models.Model):
    """Surgical service with associated procedure code."""

    objects: ClassVar[models.Manager["SurgicalService"]]

    surgery_bundle = models.ForeignKey(  # type: ignore
        SurgeryBundle, on_delete=models.CASCADE, related_name="surgical_services"
    )
    procedure_code = models.CharField(  # type: ignore
        max_length=5, help_text=_("CPT/HCPCS code")
    )
    description = models.TextField(  # type: ignore
        blank=True, help_text=_("Service description")
    )
    is_active = models.BooleanField(  # type: ignore
        default=True, help_text=_("Whether this service is active")
    )
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.procedure_code} - {self.surgery_bundle.name}"


class SurgicalFee(models.Model):
    """Fee schedule for surgical services."""

    objects: ClassVar[models.Manager["SurgicalFee"]]

    surgical_service = models.OneToOneField(  # type: ignore
        SurgicalService, on_delete=models.CASCADE, related_name="surgical_fee"
    )
    is_active = models.BooleanField(  # type: ignore
        default=True, help_text=_("Whether this fee schedule is active")
    )

    # Medicare fee percentiles
    med_fee_50 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("50th percentile Medicare fee"),
    )
    med_fee_75 = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("75th percentile Medicare fee"),
    )

    def get_range(self, low_percentile: str = "50") -> Tuple[Decimal, Decimal]:
        """Get fee range based on percentiles."""
        low_fee = getattr(self, f"med_fee_{low_percentile}")
        high_fee = self.med_fee_75
        return cast(Decimal, low_fee), cast(Decimal, high_fee)

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.surgical_service} - Fee Schedule"


class AnesthesiaFee(models.Model):
    """Stores anesthesia fees for surgical procedures."""

    objects: ClassVar[models.Manager["AnesthesiaFee"]]

    surgical_service = models.OneToOneField(  # type: ignore
        SurgicalService, on_delete=models.CASCADE, related_name="anesthesia_fee"
    )
    is_active = models.BooleanField(  # type: ignore
        default=True, help_text=_("Whether this fee is active")
    )
    base_units = models.DecimalField(  # type: ignore
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Base units for anesthesia"),
    )
    time_units = models.DecimalField(  # type: ignore
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Time units for anesthesia"),
    )
    conversion_factor = models.DecimalField(  # type: ignore
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("ASA conversion factor"),
    )

    def calculate_fee(self) -> Decimal:
        """Calculate anesthesia fee based on units and conversion factor."""
        total_units = self.base_units + self.time_units
        return cast(Decimal, total_units * self.conversion_factor)

    def __str__(self) -> str:
        """Return string representation."""
        return f"Anesthesia - {self.surgical_service}"


class FacilityFee(models.Model):
    """Stores facility fees for surgical procedures."""

    objects: ClassVar[models.Manager["FacilityFee"]]

    surgical_service = models.OneToOneField(  # type: ignore
        SurgicalService, on_delete=models.CASCADE, related_name="facility_fee"
    )
    is_active = models.BooleanField(  # type: ignore
        default=True, help_text=_("Whether this fee is active")
    )
    low_fee = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Low-end facility fee"),
    )
    high_fee = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("High-end facility fee"),
    )

    def get_range(self) -> Tuple[Decimal, Decimal]:
        """Return the low and high facility fee range."""
        return cast(Decimal, self.low_fee), cast(Decimal, self.high_fee)

    def __str__(self) -> str:
        """Return string representation."""
        return f"Facility Fee - {self.surgical_service}"

    class Meta:
        """Model metadata."""

        verbose_name = _("Facility Fee")
        verbose_name_plural = _("Facility Fees")
        indexes = [
            models.Index(fields=["surgical_service"]),  # type: ignore
            models.Index(fields=["is_active"]),  # type: ignore
        ]
