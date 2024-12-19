"""
Core Models Module

This module defines the core models for the application.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, Union, cast

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ProcedureCode(models.Model):
    """
    Represents a medical procedure code.
    """

    CODE_TYPES = [
        ("CPT", "CPT"),
        ("HCPCS", "HCPCS"),
        ("ASA", "ASA"),
    ]

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text=_("Procedure code (CPT, HCPCS, ASA)"),
    )
    code_type = models.CharField(
        max_length=5,
        choices=CODE_TYPES,
        help_text=_("Type of procedure code"),
    )
    description = models.TextField(
        help_text=_("Description of the procedure"),
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Category of the procedure"),
    )
    base_units = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Base units for ASA codes"),
    )
    phys_fee_25 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("25th percentile physician fee"),
    )
    phys_fee_50 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("50th percentile physician fee"),
    )
    phys_fee_75 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("75th percentile physician fee"),
    )
    med_fee_25 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("25th percentile medical fee"),
    )
    med_fee_50 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("50th percentile medical fee"),
    )
    med_fee_75 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("75th percentile medical fee"),
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text=_("When this code was created"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When this code was last updated"),
    )

    class Meta:
        ordering = ["code"]
        verbose_name = _("Procedure Code")
        verbose_name_plural = _("Procedure Codes")
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["code_type"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.description}"

    @property
    def is_asa_code(self) -> bool:
        """Check if this is an ASA code."""
        return self.code_type == "ASA"

    def get_fee_by_percentile(
        self, percentile: int, fee_type: str = "phys"
    ) -> Optional[Decimal]:
        """
        Get fee by percentile and type.

        Args:
            percentile: Fee percentile (25, 50, or 75)
            fee_type: Fee type ('phys' or 'med')

        Returns:
            Decimal fee amount or None if not found

        Raises:
            ValidationError: If invalid percentile or fee type
        """
        if percentile not in [25, 50, 75]:
            raise ValidationError({"percentile": _("Percentile must be 25, 50, or 75")})

        if fee_type not in ["phys", "med"]:
            raise ValidationError({"fee_type": _("Fee type must be 'phys' or 'med'")})

        field_name = f"{fee_type}_fee_{percentile}"
        value = getattr(self, field_name)
        return cast(Optional[Decimal], value)

    def get_recommended_fee(self) -> Decimal:
        """Get recommended fee (50th percentile physician fee)."""
        value = cast(Optional[Decimal], self.phys_fee_50)
        if value is not None:
            return value
        return Decimal("0")

    def get_adjusted_fee(
        self, percentile: int, fee_type: str = "phys", gaf: Optional[Decimal] = None
    ) -> Decimal:
        """
        Get GAF-adjusted fee.

        Args:
            percentile: Fee percentile (25, 50, or 75)
            fee_type: Fee type ('phys' or 'med')
            gaf: Geographic Adjustment Factor

        Returns:
            Decimal adjusted fee amount

        Raises:
            ValidationError: If invalid percentile or fee type
        """
        fee = self.get_fee_by_percentile(percentile, fee_type)
        if fee is None:
            return Decimal("0")

        if gaf is None:
            return fee

        return fee * gaf

    @classmethod
    def get_by_code(cls, code: str) -> "ProcedureCode":
        """Get procedure code by code value."""
        try:
            return cls.objects.get(code=code)
        except cls.DoesNotExist:
            raise ValidationError({"code": _("Invalid procedure code")})

    @classmethod
    def search(cls, query: str) -> "models.QuerySet[ProcedureCode]":
        """Search procedure codes."""
        return cls.objects.filter(
            models.Q(code__icontains=query) | models.Q(description__icontains=query)
        ).order_by("code")

    @classmethod
    def search_by_type(
        cls, code_type: str, query: str = ""
    ) -> "models.QuerySet[ProcedureCode]":
        """Search procedure codes by type."""
        qs = cls.objects.filter(code_type=code_type)
        if query:
            qs = qs.filter(
                models.Q(code__icontains=query) | models.Q(description__icontains=query)
            )
        return qs.order_by("code")
