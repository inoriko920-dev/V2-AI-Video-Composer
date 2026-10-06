from aavc.rendering.benchmark import benchmark_command_build


def test_benchmark_harness_handles_10_100_and_500_scenes() -> None:
    for count in (10, 100, 500):
        result = benchmark_command_build(count)
        assert result.scene_count == count
        assert result.command_build_seconds >= 0
        assert result.filter_graph_characters > 0
        assert result.windows_command_units_before_externalization > 0
