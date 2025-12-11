from typing import Dict, Any

# --- THREAT THRESHOLDS ---
TEMP_WARNING = 80.0    
TEMP_CRITICAL = 90.0   

LOAD_WARNING = 80.0    
LOAD_CRITICAL = 95.0   

DPC_CRITICAL = 500000  
CONTEXT_SWITCH_CRITICAL = 1000000 

def analyze_metric(metric_name: str, value: float, warning_val: float, critical_val: float) -> Dict[str, str]:
    """Determines the status (color) and message for a single metric."""
    status = "SAFE" 
    message = f"Normal {metric_name} usage."
    
    if value >= critical_val:
        status = "THREAT" 
        message = f"CRITICAL: {metric_name} is too high ({value}). Immediate action required!"
    elif value >= warning_val:
        status = "WARNING" 
        message = f"HIGH: {metric_name} is elevated. Check background tasks."
        
    return {"status": status, "message": message}


def get_health_status(current_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes all system metrics and returns the overall status and alerts."""
    
    analysis_results = {}
    
    # 1. CPU Analysis
    cpu_temp = current_metrics['cpu']['temperature']
    cpu_usage = current_metrics['cpu']['usage_percent']
    
    analysis_results['cpu_temp'] = analyze_metric(
        "CPU Temperature", cpu_temp, TEMP_WARNING, TEMP_CRITICAL
    )
    analysis_results['cpu_usage'] = analyze_metric(
        "CPU Usage", cpu_usage, LOAD_WARNING, LOAD_CRITICAL
    )
    
    # 2. GPU Analysis (FIXED: Checks if GPU exists first)
    if current_metrics.get('gpu'):
        # Note: keys match the new monitor.py ('temp' and 'usage')
        gpu_temp = current_metrics['gpu']['temp']
        gpu_usage = current_metrics['gpu']['usage']

        analysis_results['gpu_temp'] = analyze_metric(
            "GPU Temperature", gpu_temp, TEMP_WARNING, TEMP_CRITICAL
        )
        analysis_results['gpu_usage'] = analyze_metric(
            "GPU Usage", gpu_usage, LOAD_WARNING, LOAD_CRITICAL
        )
    else:
        # If no GPU, we skip analysis
        pass
    
    # 3. Kernel/Stall Analysis
    dpcs = current_metrics['kernel']['dpcs_stalls']
    
    if dpcs >= DPC_CRITICAL:
        analysis_results['kernel_stalls'] = {
            "status": "THREAT",
            "message": f"CRITICAL KERNEL STALLS: High DPC count ({dpcs}). Drivers are stalling."
        }
    else:
        ctx_switches = current_metrics['kernel']['context_switches']
        if ctx_switches >= CONTEXT_SWITCH_CRITICAL:
            analysis_results['kernel_ctx'] = {
                "status": "WARNING",
                "message": f"WARNING: High context switching ({ctx_switches})."
            }
        else:
            analysis_results['kernel_status'] = {
                "status": "SAFE",
                "message": "Kernel metrics nominal."
            }
            
    # 4. Determine Overall Threat Level
    statuses = [res['status'] for res in analysis_results.values()]
    
    if "THREAT" in statuses:
        overall_status = "THREAT"
    elif "WARNING" in statuses:
        overall_status = "WARNING"
    else:
        overall_status = "SAFE"
        
    return {
        "status": overall_status,
        "details": analysis_results
    }