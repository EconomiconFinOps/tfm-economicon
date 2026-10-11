"""Offline real tokenizer checks of expanded and configured admission budgets."""
from pathlib import Path
import pytest
from app.core.chat_resources import load_resources, TokenBudgetExceeded
from app.core.summary_resources import load_resources as summary_resources
from app.agents.schemas import chat_provider_schema

ROOT = Path(__file__).resolve().parents[1]/'app/agents/prompt_resources/jup035'


def test_expanded_chat_admits_over_old_ceiling():
    resources = load_resources(ROOT/'chat/v2')
    messages = [{'role': 'system', 'content': resources.system},
                {'role': 'user', 'content': 'dato '*12000}]
    assert resources.check_messages(messages, chat_provider_schema()) > 8192


def test_configured_chat_limit_includes_system_schema_and_reserves(monkeypatch):
    monkeypatch.setenv('CHAT_CONTEXT_TOKENS', '16384')
    resources = load_resources(ROOT/'chat/v2')
    messages = [{'role': 'system', 'content': resources.system},
                {'role': 'user', 'content': 'dato '*20000}]
    with pytest.raises(TokenBudgetExceeded):
        resources.check_messages(messages, chat_provider_schema())


def test_summary_input_admits_large_complete_pair():
    resources = summary_resources(ROOT/'summary/v2', ROOT/'chat/v2/tokenizer.json')
    payload = {'previous_summary': None, 'pairs': [
        {'question_ref': 'q-'+'1'*64, 'answer_ref': 'a-'+'2'*64,
         'question': 'Pregunta sintetica', 'answer': 'texto literal '*2500}]}
    _, measured = resources.prepare_input(payload)
    assert measured > 4096


def test_configured_summary_limit_counts_full_input_and_output(monkeypatch):
    monkeypatch.setenv('SUMMARY_CONTEXT_TOKENS', '17392')
    resources = summary_resources(ROOT/'summary/v2', ROOT/'chat/v2/tokenizer.json')
    payload = {'previous_summary': None, 'pairs': [
        {'question_ref': 'q-'+'1'*64, 'answer_ref': 'a-'+'2'*64,
         'question': 'Pregunta sintetica', 'answer': 'dato '*10000}]}
    with pytest.raises(ValueError, match='Summary input token limit'):
        resources.prepare_input(payload)


@pytest.mark.parametrize('value', ['0', '-1', '1048577', 'NaN'])
def test_invalid_config_is_rejected_at_resource_load(monkeypatch, value):
    monkeypatch.setenv('CHAT_CONTEXT_TOKENS', value)
    with pytest.raises(ValueError):
        load_resources(ROOT/'chat/v2')
