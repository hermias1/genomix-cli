from genomix.agent.session_store import SessionStore

def test_save_and_load(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    msgs = [{"role": "user", "content": "What is BRCA1?"},{"role": "assistant", "content": "A tumor suppressor."}]
    sid = store.save_session(msgs, title="BRCA1")
    loaded = store.load_session(sid)
    assert len(loaded) == 2
    assert loaded[0]["content"] == "What is BRCA1?"

def test_search(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    store.save_session([{"role": "user", "content": "TP53 info"}], title="TP53")
    store.save_session([{"role": "user", "content": "Align reads"}], title="Alignment")
    results = store.search("TP53")
    assert len(results) == 1

def test_list_sessions(tmp_path):
    store = SessionStore(tmp_path / "sessions.db")
    store.save_session([{"role": "user", "content": "q1"}], title="S1")
    store.save_session([{"role": "user", "content": "q2"}], title="S2")
    assert len(store.list_sessions()) == 2
