"""Fault decoding and transition tests, without HA or a live controller."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "system_faults", Path(__file__).parents[1] / "custom_components/xcc/system_faults.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

DESCRIPTOR = '''<page><block data="DIAG1" name_en="Current errors">
<row text="Chyba" text_en="Flow error HP1" visData="1;A0B;1"><button prop="RESET"/></row>
<row text="Cidlo" text_en="Flow sensor HP1" visData="1;A0BOMER;1"/>
<row text_en="DHW heating element error" visData="1;CHYBY-TUVSANITERR;1"/>
</block><block data="DIAG1"><row text_en="History" visData="1;VARIANT;1"/></block></page>'''

def snapshot(packed=0, dhw=0):
    return f'''<PAGE><INPUT PS=";A0B;A0F;A0C;A0D;A0E;A0G;A0BOMER" VALUE="{packed}"/>
    <INPUT P="CHYBY-TUVSANITERR" VALUE="{dhw}"/></PAGE>'''

def test_labels_do_not_include_history_or_controls():
    labels = module.fault_definitions(DESCRIPTOR)
    assert set(labels) == {"A0B", "A0BOMER", "CHYBY-TUVSANITERR"}
    assert labels["A0B"] == "Flow error HP1"
    assert module.fault_definitions(DESCRIPTOR, False)["A0B"] == "Chyba"

@pytest.mark.parametrize("packed,flow,meter", [(0,False,False),(1,False,False),(2,True,False),(128,False,True),(130,True,True)])
def test_bit_positions_include_empty_slots(packed, flow, meter):
    result = module.fault_snapshot(snapshot(packed,1), module.fault_definitions(DESCRIPTOR))
    assert result == {"A0B":flow, "A0BOMER":meter, "CHYBY-TUVSANITERR":True}

@pytest.mark.parametrize("xml", ["Error: timeout", "<PAGE/>", "<LOGIN/>", snapshot(-1), snapshot(0,2), snapshot('bad')])
def test_bad_data_never_clears_fault(xml):
    tracker = module.FaultTracker()
    tracker.definitions = module.fault_definitions(DESCRIPTOR)
    tracker.update(snapshot(2))
    with pytest.raises(Exception):
        tracker.update(xml)
    assert not tracker.available
    assert tracker.active == {"A0B":"Flow error HP1"}
    assert tracker.update(snapshot(2)) == []

def test_transitions_initial_active_second_fault_and_clear():
    tracker = module.FaultTracker()
    tracker.definitions = module.fault_definitions(DESCRIPTOR)
    assert tracker.update(snapshot(2)) == [("A0B","Flow error HP1",True)]
    assert tracker.update(snapshot(2)) == []
    assert tracker.update(snapshot(130)) == [("A0BOMER","Flow sensor HP1",True)]
    assert tracker.update(snapshot(128)) == [("A0B","Flow error HP1",False)]
    assert tracker.update(snapshot(0)) == [("A0BOMER","Flow sensor HP1",False)]

def test_initial_clear_quiet_and_unknown_visibility_rejected():
    tracker = module.FaultTracker()
    tracker.definitions = module.fault_definitions(DESCRIPTOR)
    assert tracker.update(snapshot()) == []
    with pytest.raises(ValueError):
        module.fault_definitions(DESCRIPTOR.replace('1;A0B;1','2;A0B;1'))
