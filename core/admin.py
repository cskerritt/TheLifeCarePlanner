"""
Core Admin Module

This module configures the Django admin interface for core app models,
providing customized list displays, filters, and actions.
"""

from typing import Any, Optional, Sequence, Tuple

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import ProcedureCode, User


@admin.register(ProcedureCode)  # type: ignore
class ProcedureCodeAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProcedureCode model.

    Provides custom list display, filtering, search, and actions
    for managing procedure codes through the admin interface.
    """

    list_display = [
        "code",
        "code_type",
        "category",
        "description",
        "display_med_fee_50",
        "display_med_fee_75",
        "display_phys_fee_50",
        "display_phys_fee_75",
    ]
    list_filter = [
        "code_type",
        "category",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = ["code", "description"]
    readonly_fields: Sequence[str] = [
        "created_at",
        "updated_at",
        "display_med_fee_50",
        "display_med_fee_75",
        "display_phys_fee_50",
        "display_phys_fee_75",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "code",
                    "code_type",
                    "category",
                    "description",
                )
            },
        ),
        (
            _("Fee Source Information"),
            {
                "fields": (
                    "primary_fee_source",
                    "fee_source_year",
                    "fee_source_region",
                )
            },
        ),
        (
            _("Physician Fee Reference (PFR)"),
            {
                "fields": ("phys_fee_50", "phys_fee_75", "phys_fee_90"),
                "description": _(
                    "Fees from CMS analytical files reflecting market rates"
                ),
            },
        ),
        (
            _("Medical Fee Update Schedule (MFUS)"),
            {
                "fields": ("med_fee_50", "med_fee_75", "med_fee_90"),
                "description": _(
                    "Fees derived from Medicare Physician Fee Schedule data"
                ),
            },
        ),
        (
            _("ASA Details"),
            {
                "fields": ("base_units",),
                "classes": ("collapse",),
                "description": _("Only applicable for ASA codes."),
            },
        ),
        (_("Additional Information"), {"fields": ("notes", "is_facility")}),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    ]
    actions = [
        "mark_as_facility",
        "unmark_as_facility",
        "set_primary_source_mfus",
        "set_primary_source_pfr",
    ]
    save_on_top = True
    ordering = ["code"]
    list_per_page = 50

    @admin.display(
        description=_("Medicare 50th %"),
        ordering="med_fee_50",
    )
    def display_med_fee_50(self, obj: ProcedureCode) -> str:
        """Format Medicare 50th percentile fee."""
        return f"${obj.med_fee_50:,.2f}" if obj.med_fee_50 else "-"

    @admin.display(
        description=_("Medicare 75th %"),
        ordering="med_fee_75",
    )
    def display_med_fee_75(self, obj: ProcedureCode) -> str:
        """Format Medicare 75th percentile fee."""
        return f"${obj.med_fee_75:,.2f}" if obj.med_fee_75 else "-"

    @admin.display(
        description=_("Physician 50th %"),
        ordering="phys_fee_50",
    )
    def display_phys_fee_50(self, obj: ProcedureCode) -> str:
        """Format physician 50th percentile fee."""
        return f"${obj.phys_fee_50:,.2f}" if obj.phys_fee_50 else "-"

    @admin.display(
        description=_("Physician 75th %"),
        ordering="phys_fee_75",
    )
    def display_phys_fee_75(self, obj: ProcedureCode) -> str:
        """Format physician 75th percentile fee."""
        return f"${obj.phys_fee_75:,.2f}" if obj.phys_fee_75 else "-"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        """Get the queryset for the admin view."""
        qs = super().get_queryset(request)
        return qs.select_related("fee_schedule", "fee_resource")

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet[Any],
        search_term: str,
    ) -> Tuple[QuerySet[Any], bool]:
        """Custom search for procedure codes."""
        queryset, may_have_duplicates = super().get_search_results(
            request, queryset, search_term
        )

        # Add custom search logic here if needed

        return queryset, may_have_duplicates

    def get_readonly_fields(
        self, request: HttpRequest, obj: Optional[ProcedureCode] = None
    ) -> Sequence[str]:
        """Get readonly fields based on permissions."""
        user = getattr(request, "user", None)
        if user and getattr(user, "is_superuser", False):
            return self.readonly_fields
        return tuple(list(self.readonly_fields) + ["code", "code_type"])

    class Media:
        css = {"all": ("css/admin/procedure_code.css",)}
        js = ("js/admin/procedure_code.js",)


@admin.register(User)  # type: ignore
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model."""

    list_display = ["username", "email", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active"]
    search_fields = ["username", "email"]
    readonly_fields: Sequence[str] = ["created_at", "updated_at"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        """Get the queryset for the admin view."""
        qs = super().get_queryset(request)
        return qs.select_related("profile", "organization")
