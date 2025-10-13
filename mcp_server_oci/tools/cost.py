"""
Tools for managing OCI Cost Management and Usage resources.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import oci

logger = logging.getLogger(__name__)


def get_cost_usage_summary(usage_api_client: oci.usage_api.UsageapiClient,
                           tenant_id: str,
                           time_usage_started: str,
                           time_usage_ended: str,
                           granularity: str = "DAILY") -> List[Dict[str, Any]]:
    """
    Get cost and usage summary for a tenancy.

    Args:
        usage_api_client: OCI UsageApi client
        tenant_id: OCID of the tenancy
        time_usage_started: Start time in ISO format (YYYY-MM-DD)
        time_usage_ended: End time in ISO format (YYYY-MM-DD)
        granularity: Granularity of the data (DAILY, MONTHLY)

    Returns:
        List of cost and usage summaries
    """
    try:
        request_summarized_usages_details = oci.usage_api.models.RequestSummarizedUsagesDetails(
            tenant_id=tenant_id,
            time_usage_started=time_usage_started,
            time_usage_ended=time_usage_ended,
            granularity=granularity,
            is_aggregate_by_time=True
        )

        usage_response = oci.pagination.list_call_get_all_results(
            usage_api_client.request_summarized_usages,
            request_summarized_usages_details=request_summarized_usages_details
        )

        summaries = []
        for item in usage_response.data.items:
            summaries.append({
                "time_usage_started": str(item.time_usage_started),
                "time_usage_ended": str(item.time_usage_ended),
                "computed_amount": item.computed_amount,
                "computed_quantity": item.computed_quantity,
                "currency": item.currency,
                "service": item.service,
                "resource_name": item.resource_name,
                "compartment_name": item.compartment_name,
                "compartment_id": item.compartment_id,
                "unit": item.unit,
            })

        logger.info(f"Retrieved {len(summaries)} usage summaries for tenancy {tenant_id}")
        return summaries

    except Exception as e:
        logger.exception(f"Error getting cost usage summary: {e}")
        raise


def get_cost_by_service(usage_api_client: oci.usage_api.UsageapiClient,
                       tenant_id: str,
                       time_usage_started: str,
                       time_usage_ended: str) -> List[Dict[str, Any]]:
    """
    Get cost breakdown by service.

    Args:
        usage_api_client: OCI UsageApi client
        tenant_id: OCID of the tenancy
        time_usage_started: Start time in ISO format (YYYY-MM-DD)
        time_usage_ended: End time in ISO format (YYYY-MM-DD)

    Returns:
        List of costs grouped by service
    """
    try:
        request_summarized_usages_details = oci.usage_api.models.RequestSummarizedUsagesDetails(
            tenant_id=tenant_id,
            time_usage_started=time_usage_started,
            time_usage_ended=time_usage_ended,
            granularity="DAILY",
            group_by=["service"]
        )

        usage_response = oci.pagination.list_call_get_all_results(
            usage_api_client.request_summarized_usages,
            request_summarized_usages_details=request_summarized_usages_details
        )

        # Aggregate by service
        service_costs = {}
        for item in usage_response.data.items:
            service = item.service
            if service not in service_costs:
                service_costs[service] = {
                    "service": service,
                    "total_cost": 0.0,
                    "currency": item.currency,
                    "unit": item.unit,
                }
            service_costs[service]["total_cost"] += float(item.computed_amount) if item.computed_amount else 0.0

        result = list(service_costs.values())
        logger.info(f"Retrieved cost breakdown for {len(result)} services")
        return result

    except Exception as e:
        logger.exception(f"Error getting cost by service: {e}")
        raise


def get_cost_by_compartment(usage_api_client: oci.usage_api.UsageapiClient,
                            tenant_id: str,
                            time_usage_started: str,
                            time_usage_ended: str) -> List[Dict[str, Any]]:
    """
    Get cost breakdown by compartment.

    Args:
        usage_api_client: OCI UsageApi client
        tenant_id: OCID of the tenancy
        time_usage_started: Start time in ISO format (YYYY-MM-DD)
        time_usage_ended: End time in ISO format (YYYY-MM-DD)

    Returns:
        List of costs grouped by compartment
    """
    try:
        request_summarized_usages_details = oci.usage_api.models.RequestSummarizedUsagesDetails(
            tenant_id=tenant_id,
            time_usage_started=time_usage_started,
            time_usage_ended=time_usage_ended,
            granularity="DAILY",
            group_by=["compartmentName"]
        )

        usage_response = oci.pagination.list_call_get_all_results(
            usage_api_client.request_summarized_usages,
            request_summarized_usages_details=request_summarized_usages_details
        )

        # Aggregate by compartment
        compartment_costs = {}
        for item in usage_response.data.items:
            compartment = item.compartment_name
            if compartment not in compartment_costs:
                compartment_costs[compartment] = {
                    "compartment_name": compartment,
                    "compartment_id": item.compartment_id,
                    "total_cost": 0.0,
                    "currency": item.currency,
                }
            compartment_costs[compartment]["total_cost"] += float(item.computed_amount) if item.computed_amount else 0.0

        result = list(compartment_costs.values())
        logger.info(f"Retrieved cost breakdown for {len(result)} compartments")
        return result

    except Exception as e:
        logger.exception(f"Error getting cost by compartment: {e}")
        raise


def list_budgets(budget_client: oci.budget.BudgetClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all budgets in a compartment.

    Args:
        budget_client: OCI Budget client
        compartment_id: OCID of the compartment

    Returns:
        List of budgets with their details
    """
    try:
        budgets_response = oci.pagination.list_call_get_all_results(
            budget_client.list_budgets,
            compartment_id
        )

        budgets = []
        for budget in budgets_response.data:
            budgets.append({
                "id": budget.id,
                "display_name": budget.display_name,
                "compartment_id": budget.compartment_id,
                "target_compartment_id": budget.target_compartment_id,
                "amount": budget.amount,
                "reset_period": budget.reset_period,
                "lifecycle_state": budget.lifecycle_state,
                "alert_rule_count": budget.alert_rule_count,
                "time_created": str(budget.time_created),
                "actual_spend": budget.actual_spend,
                "forecasted_spend": budget.forecasted_spend,
                "time_spend_computed": str(budget.time_spend_computed) if budget.time_spend_computed else None,
            })

        logger.info(f"Found {len(budgets)} budgets in compartment {compartment_id}")
        return budgets

    except Exception as e:
        logger.exception(f"Error listing budgets: {e}")
        raise


def get_budget(budget_client: oci.budget.BudgetClient, budget_id: str) -> Dict[str, Any]:
    """
    Get details of a specific budget.

    Args:
        budget_client: OCI Budget client
        budget_id: OCID of the budget

    Returns:
        Details of the budget
    """
    try:
        budget = budget_client.get_budget(budget_id).data

        budget_details = {
            "id": budget.id,
            "display_name": budget.display_name,
            "description": budget.description,
            "compartment_id": budget.compartment_id,
            "target_compartment_id": budget.target_compartment_id,
            "target_type": budget.target_type,
            "targets": budget.targets,
            "amount": budget.amount,
            "reset_period": budget.reset_period,
            "budget_processing_period_start_offset": budget.budget_processing_period_start_offset,
            "processing_period_type": budget.processing_period_type,
            "lifecycle_state": budget.lifecycle_state,
            "alert_rule_count": budget.alert_rule_count,
            "version": budget.version,
            "actual_spend": budget.actual_spend,
            "forecasted_spend": budget.forecasted_spend,
            "time_spend_computed": str(budget.time_spend_computed) if budget.time_spend_computed else None,
            "time_created": str(budget.time_created),
            "time_updated": str(budget.time_updated),
        }

        logger.info(f"Retrieved details for budget {budget_id}")
        return budget_details

    except Exception as e:
        logger.exception(f"Error getting budget details: {e}")
        raise
