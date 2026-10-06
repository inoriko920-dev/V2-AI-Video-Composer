from __future__ import annotations

import json
from pathlib import Path

import pytest

from aavc.application.services.vertical_slice import create_project_state
from aavc.persistence.serializer import loads_project

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "step10"


def _payload():
    state = create_project_state(
        title="wave-d-validation",
        scene_docx=FIXTURE / "scene_asset_demo.docx",
        asset_directory=FIXTURE / "assets",
    )
    scene = state.scenes[0]
    payload = state.to_dict()
    payload["animations"] = [
        {
            "scene_number": scene.scene_number,
            "asset_id": scene.asset_ids[0],
            "enter_effect": "Fade",
            "exit_effect": "Fade",
            "intensity": 1.0,
            "locked": False,
            "keyframe_tracks": [
                {
                    "property_name": "opacity",
                    "keyframes": [
                        {"time": 0.0, "value": 0.0},
                        {"time": 1.0, "value": 1.0},
                    ],
                }
            ],
        }
    ]
    return payload


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda data: data["animations"][0]["keyframe_tracks"][0]["keyframes"][0].update(
                {"time": 1.5}
            ),
            "rentang 0–1",
        ),
        (
            lambda data: data["animations"][0]["keyframe_tracks"][0].update(
                {"property_name": "unknown"}
            ),
            "property_name tidak didukung",
        ),
        (
            lambda data: data["animations"][0]["keyframe_tracks"][0]["keyframes"][0].update(
                {"easing": "magic"}
            ),
            "easing tidak didukung",
        ),
    ],
)
def test_invalid_schema_v3_keyframe_payload_is_rejected(mutate, expected: str) -> None:
    payload = _payload()
    mutate(payload)

    with pytest.raises(ValueError, match=expected):
        loads_project(json.dumps(payload))
