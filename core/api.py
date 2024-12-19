"""
Core API Module

This module provides API views for core functionality.
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Type, Union, cast

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import ModelViewSet

from .models import ProcedureCode
from .serializers import ProcedureCodeSerializer
from .utils import safe_decimal

# Constants
DEFAULT_CACHE_TTL = 60 * 60 * 24  # 24 hours
MIN_GAF = Decimal("0.01")
MAX_GAF = Decimal("5.00")


class ProcedureCodeViewSet(ModelViewSet):
    """
    ViewSet for managing procedure codes.
    """

    queryset: QuerySet[ProcedureCode] = ProcedureCode.objects.all()
    serializer_class = ProcedureCodeSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "type",
                openapi.IN_QUERY,
                description="Filter by code type (CPT, HCPCS, ASA)",
                type=openapi.TYPE_STRING,
                enum=["CPT", "HCPCS", "ASA"],
            )
        ]
    )
    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(getattr(settings, "CACHE_TTL", DEFAULT_CACHE_TTL)))
    def by_code_type(self, request: Request) -> Response:
        """
        Return procedure codes grouped by code type.

        Query Parameters:
            type (str): Optional. Filter by code type (CPT, HCPCS, ASA)

        Returns:
            Response: List of procedure codes
        """
        code_type = request.query_params.get("type")
        if code_type and code_type not in dict(ProcedureCode.CODE_TYPES):
            raise DRFValidationError(
                {"type": _("Invalid code type. Must be one of: CPT, HCPCS, ASA")}
            )

        codes = self.filter_queryset(self.get_queryset())
        if code_type:
            codes = codes.filter(code_type=code_type)

        page = self.paginate_queryset(codes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(codes, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "gaf",
                openapi.IN_QUERY,
                description="Geographic Adjustment Factor",
                type=openapi.TYPE_NUMBER,
                required=False,
                default=1.0,
            )
        ]
    )
    @action(detail=True, methods=["get"])
    @method_decorator(cache_page(getattr(settings, "CACHE_TTL", DEFAULT_CACHE_TTL)))
    def adjusted_fees(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        Return adjusted fees for a procedure code based on GAF factor.

        Query Parameters:
            gaf (float): Geographic Adjustment Factor (default: 1.0)

        Returns:
            Response: Adjusted fee information

        Raises:
            DRFValidationError: If GAF factor is invalid
        """
        code = cast(ProcedureCode, self.get_object())
        gaf_str = request.query_params.get("gaf", "1.0")

        try:
            gaf_factor = safe_decimal(gaf_str, default="1.0000")
            if not MIN_GAF <= gaf_factor <= MAX_GAF:
                raise DRFValidationError(
                    {"gaf": _(f"GAF factor must be between {MIN_GAF} and {MAX_GAF}.")}
                )
        except (InvalidOperation, ValueError) as e:
            raise DRFValidationError(
                {"gaf": _("Invalid GAF factor. Must be a valid number.")}
            )

        try:
            adjusted_fee_50 = code.get_fee_by_percentile(50, "phys", gaf_factor)
            adjusted_fee_75 = code.get_fee_by_percentile(75, "phys", gaf_factor)
        except ValidationError as e:
            raise DRFValidationError(e.message_dict)

        return Response(
            {
                "code": code.code,
                "code_type": code.code_type,
                "description": code.description,
                "base_fee_50": code.get_fee_by_percentile(50, "phys"),
                "base_fee_75": code.get_fee_by_percentile(75, "phys"),
                "adjusted_fee_50": adjusted_fee_50,
                "adjusted_fee_75": adjusted_fee_75,
                "gaf_factor": gaf_factor,
                "base_units": code.base_units if code.is_asa_code else None,
            }
        )
