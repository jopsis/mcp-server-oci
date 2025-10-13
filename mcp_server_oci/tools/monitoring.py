"""
Tools for managing OCI Monitoring and Observability resources.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import oci

logger = logging.getLogger(__name__)


def list_alarms(monitoring_client: oci.monitoring.MonitoringClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all alarms in a compartment.

    Args:
        monitoring_client: OCI Monitoring client
        compartment_id: OCID of the compartment

    Returns:
        List of alarms with their details
    """
    try:
        alarms_response = oci.pagination.list_call_get_all_results(
            monitoring_client.list_alarms,
            compartment_id
        )

        alarms = []
        for alarm in alarms_response.data:
            alarms.append({
                "id": alarm.id,
                "display_name": alarm.display_name,
                "compartment_id": alarm.compartment_id,
                "metric_compartment_id": alarm.metric_compartment_id,
                "namespace": alarm.namespace,
                "query": alarm.query,
                "severity": alarm.severity,
                "lifecycle_state": alarm.lifecycle_state,
                "is_enabled": alarm.is_enabled,
                "destinations": alarm.destinations,
                "time_created": str(alarm.time_created),
                "time_updated": str(alarm.time_updated),
            })

        logger.info(f"Found {len(alarms)} alarms in compartment {compartment_id}")
        return alarms

    except Exception as e:
        logger.exception(f"Error listing alarms: {e}")
        raise


def get_alarm(monitoring_client: oci.monitoring.MonitoringClient, alarm_id: str) -> Dict[str, Any]:
    """
    Get details of a specific alarm.

    Args:
        monitoring_client: OCI Monitoring client
        alarm_id: OCID of the alarm

    Returns:
        Details of the alarm
    """
    try:
        alarm = monitoring_client.get_alarm(alarm_id).data

        alarm_details = {
            "id": alarm.id,
            "display_name": alarm.display_name,
            "compartment_id": alarm.compartment_id,
            "metric_compartment_id": alarm.metric_compartment_id,
            "metric_compartment_id_in_subtree": alarm.metric_compartment_id_in_subtree,
            "namespace": alarm.namespace,
            "resource_group": alarm.resource_group,
            "query": alarm.query,
            "resolution": alarm.resolution,
            "pending_duration": alarm.pending_duration,
            "severity": alarm.severity,
            "body": alarm.body,
            "is_enabled": alarm.is_enabled,
            "lifecycle_state": alarm.lifecycle_state,
            "suppress": {
                "time_suppress_from": str(alarm.suppression.time_suppress_from) if alarm.suppression else None,
                "time_suppress_until": str(alarm.suppression.time_suppress_until) if alarm.suppression else None,
                "description": alarm.suppression.description if alarm.suppression else None,
            } if alarm.suppression else None,
            "destinations": alarm.destinations,
            "repeat_notification_duration": alarm.repeat_notification_duration,
            "time_created": str(alarm.time_created),
            "time_updated": str(alarm.time_updated),
        }

        logger.info(f"Retrieved details for alarm {alarm_id}")
        return alarm_details

    except Exception as e:
        logger.exception(f"Error getting alarm details: {e}")
        raise


def get_alarm_history(monitoring_client: oci.monitoring.MonitoringClient,
                      alarm_id: str,
                      alarm_historytype: str = "STATE_TRANSITION_HISTORY") -> List[Dict[str, Any]]:
    """
    Get alarm state history.

    Args:
        monitoring_client: OCI Monitoring client
        alarm_id: OCID of the alarm
        alarm_historytype: Type of history (STATE_TRANSITION_HISTORY, STATE_HISTORY, RULE_HISTORY)

    Returns:
        List of alarm history entries
    """
    try:
        history_response = oci.pagination.list_call_get_all_results(
            monitoring_client.get_alarm_history,
            alarm_id,
            alarm_historytype=alarm_historytype
        )

        history = []
        for entry in history_response.data:
            history.append({
                "summary": entry.summary,
                "timestamp": str(entry.timestamp),
                "timestamp_triggered": str(entry.timestamp_triggered) if hasattr(entry, 'timestamp_triggered') and entry.timestamp_triggered else None,
            })

        logger.info(f"Retrieved {len(history)} history entries for alarm {alarm_id}")
        return history

    except Exception as e:
        logger.exception(f"Error getting alarm history: {e}")
        raise


def list_metrics(monitoring_client: oci.monitoring.MonitoringClient,
                 compartment_id: str,
                 namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List available metrics in a compartment.

    Args:
        monitoring_client: OCI Monitoring client
        compartment_id: OCID of the compartment
        namespace: Optional namespace to filter metrics

    Returns:
        List of available metrics
    """
    try:
        list_metrics_details = oci.monitoring.models.ListMetricsDetails(
            compartment_id=compartment_id,
            namespace=namespace
        )

        metrics_response = oci.pagination.list_call_get_all_results(
            monitoring_client.list_metrics,
            compartment_id,
            list_metrics_details
        )

        metrics = []
        for metric in metrics_response.data:
            metrics.append({
                "name": metric.name,
                "namespace": metric.namespace,
                "resource_group": metric.resource_group,
                "compartment_id": metric.compartment_id,
                "dimensions": metric.dimensions,
            })

        logger.info(f"Found {len(metrics)} metrics in compartment {compartment_id}")
        return metrics

    except Exception as e:
        logger.exception(f"Error listing metrics: {e}")
        raise


def query_metric_data(monitoring_client: oci.monitoring.MonitoringClient,
                      compartment_id: str,
                      query: str,
                      start_time: str,
                      end_time: str,
                      resolution: str = "1m") -> List[Dict[str, Any]]:
    """
    Query metric data for a time range.

    Args:
        monitoring_client: OCI Monitoring client
        compartment_id: OCID of the compartment
        query: Metric query in MQL format
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
        resolution: Data resolution (1m, 5m, 1h)

    Returns:
        List of metric data points
    """
    try:
        summarize_metrics_data_details = oci.monitoring.models.SummarizeMetricsDataDetails(
            namespace="oci_computeagent",  # This will be overridden by the query
            query=query,
            start_time=datetime.fromisoformat(start_time.replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(end_time.replace('Z', '+00:00')),
            resolution=resolution
        )

        metrics_data_response = monitoring_client.summarize_metrics_data(
            compartment_id,
            summarize_metrics_data_details
        )

        data_points = []
        for metric_data in metrics_data_response.data:
            data_points.append({
                "namespace": metric_data.namespace,
                "resource_group": metric_data.resource_group,
                "compartment_id": metric_data.compartment_id,
                "name": metric_data.name,
                "dimensions": metric_data.dimensions,
                "aggregated_datapoints": [
                    {
                        "timestamp": str(dp.timestamp),
                        "value": dp.value
                    }
                    for dp in metric_data.aggregated_datapoints
                ] if metric_data.aggregated_datapoints else [],
                "resolution": metric_data.resolution,
            })

        logger.info(f"Retrieved metric data with {len(data_points)} series")
        return data_points

    except Exception as e:
        logger.exception(f"Error querying metric data: {e}")
        raise


def search_logs(logging_search_client: oci.loggingsearch.LogSearchClient,
                search_logs_details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Search logs using the Logging Search API.

    Args:
        logging_search_client: OCI LoggingSearch client
        search_logs_details: Search parameters including query, time range, and limit

    Returns:
        List of log entries matching the search criteria
    """
    try:
        search_details = oci.loggingsearch.models.SearchLogsDetails(
            time_start=datetime.fromisoformat(search_logs_details['time_start'].replace('Z', '+00:00')),
            time_end=datetime.fromisoformat(search_logs_details['time_end'].replace('Z', '+00:00')),
            search_query=search_logs_details['search_query'],
            is_return_field_info=search_logs_details.get('is_return_field_info', False)
        )

        logs_response = logging_search_client.search_logs(search_details)

        log_entries = []
        for result in logs_response.data.results:
            log_entries.append({
                "time": str(result.time),
                "log_content": result.data,
            })

        logger.info(f"Found {len(log_entries)} log entries")
        return log_entries

    except Exception as e:
        logger.exception(f"Error searching logs: {e}")
        raise


def list_log_groups(logging_client: oci.logging.LoggingManagementClient,
                    compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all log groups in a compartment.

    Args:
        logging_client: OCI Logging Management client
        compartment_id: OCID of the compartment

    Returns:
        List of log groups with their details
    """
    try:
        log_groups_response = oci.pagination.list_call_get_all_results(
            logging_client.list_log_groups,
            compartment_id
        )

        log_groups = []
        for log_group in log_groups_response.data:
            log_groups.append({
                "id": log_group.id,
                "display_name": log_group.display_name,
                "description": log_group.description,
                "compartment_id": log_group.compartment_id,
                "time_created": str(log_group.time_created),
                "time_last_modified": str(log_group.time_last_modified),
                "lifecycle_state": log_group.lifecycle_state,
            })

        logger.info(f"Found {len(log_groups)} log groups in compartment {compartment_id}")
        return log_groups

    except Exception as e:
        logger.exception(f"Error listing log groups: {e}")
        raise


def list_logs(logging_client: oci.logging.LoggingManagementClient,
              log_group_id: str) -> List[Dict[str, Any]]:
    """
    List all logs in a log group.

    Args:
        logging_client: OCI Logging Management client
        log_group_id: OCID of the log group

    Returns:
        List of logs with their details
    """
    try:
        logs_response = oci.pagination.list_call_get_all_results(
            logging_client.list_logs,
            log_group_id
        )

        logs = []
        for log in logs_response.data:
            logs.append({
                "id": log.id,
                "log_group_id": log.log_group_id,
                "display_name": log.display_name,
                "log_type": log.log_type,
                "lifecycle_state": log.lifecycle_state,
                "is_enabled": log.is_enabled,
                "retention_duration": log.retention_duration,
                "compartment_id": log.compartment_id,
                "time_created": str(log.time_created),
                "time_last_modified": str(log.time_last_modified),
            })

        logger.info(f"Found {len(logs)} logs in log group {log_group_id}")
        return logs

    except Exception as e:
        logger.exception(f"Error listing logs: {e}")
        raise
