"""
Canned / fabricated data used by the demo handlers to simulate
realistic HTCondor output without requiring a live installation.
"""

from datetime import datetime, timedelta

# Simulated "now" for consistent output
_NOW = datetime(2025, 7, 15, 14, 32, 0)

# ---------------------------------------------------------------------------
# Mock job ClassAds
# ---------------------------------------------------------------------------

MOCK_JOBS = [
    {
        "ClusterId": 1042,
        "ProcId": 0,
        "Owner": "adesai",
        "JobStatus": 2,  # Running
        "JobStatusStr": "Running",
        "Cmd": "/home/adesai/sim/run_analysis.sh",
        "Args": "--config params.yaml",
        "RequestCpus": 1,
        "RequestMemory": 4096,
        "RequestDisk": 10_000_000,
        "RemoteHost": "slot1@e1001.chtc.wisc.edu",
        "QDate": _NOW - timedelta(hours=2, minutes=17),
        "JobStartDate": _NOW - timedelta(hours=1, minutes=45),
        "ImageSize": 312_000,
        "HoldReason": "",
    },
    {
        "ClusterId": 1042,
        "ProcId": 1,
        "Owner": "adesai",
        "JobStatus": 2,  # Running
        "JobStatusStr": "Running",
        "Cmd": "/home/adesai/sim/run_analysis.sh",
        "Args": "--config params.yaml",
        "RequestCpus": 1,
        "RequestMemory": 4096,
        "RequestDisk": 10_000_000,
        "RemoteHost": "slot1@e1002.chtc.wisc.edu",
        "QDate": _NOW - timedelta(hours=2, minutes=17),
        "JobStartDate": _NOW - timedelta(hours=1, minutes=30),
        "ImageSize": 298_000,
        "HoldReason": "",
    },
    {
        "ClusterId": 1042,
        "ProcId": 2,
        "Owner": "adesai",
        "JobStatus": 1,  # Idle
        "JobStatusStr": "Idle",
        "Cmd": "/home/adesai/sim/run_analysis.sh",
        "Args": "--config params.yaml",
        "RequestCpus": 1,
        "RequestMemory": 4096,
        "RequestDisk": 10_000_000,
        "RemoteHost": "",
        "QDate": _NOW - timedelta(hours=2, minutes=17),
        "JobStartDate": None,
        "ImageSize": 0,
        "HoldReason": "",
    },
    {
        "ClusterId": 1043,
        "ProcId": 0,
        "Owner": "adesai",
        "JobStatus": 5,  # Held
        "JobStatusStr": "Held",
        "Cmd": "/home/adesai/ml/train_model.py",
        "Args": "",
        "RequestCpus": 4,
        "RequestMemory": 16_384,
        "RequestDisk": 50_000_000,
        "RemoteHost": "",
        "QDate": _NOW - timedelta(days=1, hours=3),
        "JobStartDate": _NOW - timedelta(days=1, hours=2),
        "ImageSize": 1_200_000,
        "HoldReason": "Job exceeded memory limit (request_memory = 16384 MB)",
    },
    {
        "ClusterId": 1044,
        "ProcId": 0,
        "Owner": "adesai",
        "JobStatus": 4,  # Completed
        "JobStatusStr": "Completed",
        "Cmd": "/home/adesai/preprocess/clean_data.sh",
        "Args": "raw_data.csv",
        "RequestCpus": 1,
        "RequestMemory": 2048,
        "RequestDisk": 5_000_000,
        "RemoteHost": "slot1@e1005.chtc.wisc.edu",
        "QDate": _NOW - timedelta(days=2),
        "JobStartDate": _NOW - timedelta(days=2) + timedelta(minutes=5),
        "ImageSize": 98_000,
        "HoldReason": "",
    },
    {
        "ClusterId": 1045,
        "ProcId": 0,
        "Owner": "adesai",
        "JobStatus": 1,  # Idle
        "JobStatusStr": "Idle",
        "Cmd": "/home/adesai/sim/run_analysis.sh",
        "Args": "--config params_v2.yaml",
        "RequestCpus": 1,
        "RequestMemory": 4096,
        "RequestDisk": 10_000_000,
        "RemoteHost": "",
        "QDate": _NOW - timedelta(minutes=10),
        "JobStartDate": None,
        "ImageSize": 0,
        "HoldReason": "",
    },
]


# ---------------------------------------------------------------------------
# Mock machine / slot ClassAds
# ---------------------------------------------------------------------------

MOCK_MACHINES = [
    {
        "Name": "slot1@e1001.chtc.wisc.edu",
        "Machine": "e1001.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Claimed",
        "Activity": "Busy",
        "TotalCpus": 8,
        "TotalMemory": 32_768,
        "LoadAvg": 1.02,
    },
    {
        "Name": "slot1@e1002.chtc.wisc.edu",
        "Machine": "e1002.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Claimed",
        "Activity": "Busy",
        "TotalCpus": 8,
        "TotalMemory": 32_768,
        "LoadAvg": 0.98,
    },
    {
        "Name": "slot1@e1003.chtc.wisc.edu",
        "Machine": "e1003.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Unclaimed",
        "Activity": "Idle",
        "TotalCpus": 8,
        "TotalMemory": 32_768,
        "LoadAvg": 0.01,
    },
    {
        "Name": "slot1@e1004.chtc.wisc.edu",
        "Machine": "e1004.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Unclaimed",
        "Activity": "Idle",
        "TotalCpus": 16,
        "TotalMemory": 65_536,
        "LoadAvg": 0.00,
    },
    {
        "Name": "slot1@e1005.chtc.wisc.edu",
        "Machine": "e1005.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Claimed",
        "Activity": "Busy",
        "TotalCpus": 8,
        "TotalMemory": 32_768,
        "LoadAvg": 1.05,
    },
    {
        "Name": "slot1@e1006.chtc.wisc.edu",
        "Machine": "e1006.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Unclaimed",
        "Activity": "Idle",
        "TotalCpus": 8,
        "TotalMemory": 32_768,
        "LoadAvg": 0.02,
    },
    {
        "Name": "slot1@e2001.chtc.wisc.edu",
        "Machine": "e2001.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Owner",
        "Activity": "Idle",
        "TotalCpus": 4,
        "TotalMemory": 16_384,
        "LoadAvg": 0.15,
    },
    {
        "Name": "gpu01.chtc.wisc.edu",
        "Machine": "gpu01.chtc.wisc.edu",
        "OpSys": "LINUX",
        "Arch": "X86_64",
        "State": "Claimed",
        "Activity": "Busy",
        "TotalCpus": 32,
        "TotalMemory": 131_072,
        "LoadAvg": 4.20,
    },
]


# ---------------------------------------------------------------------------
# Status code mapping
# ---------------------------------------------------------------------------

JOB_STATUS_MAP = {
    0: "Unexpanded",
    1: "Idle",
    2: "Running",
    3: "Removed",
    4: "Completed",
    5: "Held",
    6: "Transferring Output",
    7: "Suspended",
}
