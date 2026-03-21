import json
from pathlib import Path
import pytest
from genomix.swarm.manager import SwarmManager, TaskStatus


def test_submit_task(tmp_path):
    sm = SwarmManager(state_dir=tmp_path)
    task = sm.submit(command="/align", args=["data/sample.fastq.gz"])
    assert task.status == TaskStatus.PENDING
    assert task.command == "/align"


def test_list_tasks(tmp_path):
    sm = SwarmManager(state_dir=tmp_path)
    sm.submit(command="/qc", args=["data/reads.fastq"])
    sm.submit(command="/blast", args=["data/query.fasta"])
    assert len(sm.list_tasks()) == 2


def test_task_state_persisted(tmp_path):
    sm = SwarmManager(state_dir=tmp_path)
    task = sm.submit(command="/align", args=["x.fastq"])
    data = json.loads((tmp_path / f"{task.id}.json").read_text())
    assert data["command"] == "/align"


def test_cancel_task(tmp_path):
    sm = SwarmManager(state_dir=tmp_path)
    task = sm.submit(command="/qc", args=[])
    sm.cancel(task.id)
    assert sm.get_task(task.id).status == TaskStatus.CANCELLED
