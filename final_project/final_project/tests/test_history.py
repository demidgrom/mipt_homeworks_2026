from gigavibemiptcode.history import MessageHistory


def test_trim_by_message_count() -> None:
    history = MessageHistory(limit_messages=2, limit_chars=None)
    history.append('user', 'one')
    history.append('assistant', 'two')
    history.append('user', 'three')

    assert [message['content'] for message in history.messages] == ['two', 'three']


def test_trim_by_total_chars() -> None:
    history = MessageHistory(limit_messages=None, limit_chars=5)
    history.append('user', 'abc')
    history.append('assistant', 'de')
    history.append('user', 'fg')

    assert [message['content'] for message in history.messages] == ['de', 'fg']


def test_long_single_message_is_cut_from_left() -> None:
    history = MessageHistory(limit_messages=None, limit_chars=4)
    history.append('user', 'abcdef')

    assert history.messages[0]['content'] == 'cdef'


def test_system_prompt_is_added_only_to_payload() -> None:
    history = MessageHistory(limit_messages=10, limit_chars=100)
    history.append('user', 'hello')

    payload = history.build_payload('sys')

    assert payload[0] == {'role': 'system', 'content': 'sys'}
    assert history.messages == [{'role': 'user', 'content': 'hello'}]
