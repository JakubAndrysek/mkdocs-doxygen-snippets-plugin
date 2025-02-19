from mkdoxy.doxygen_generator import DoxygenGenerator


def test_merge_doxygen_input_empty_src_dirs(tmp_path):
    # When src_dirs is empty, the function should return doxy_input unchanged.
    src_dirs = ""
    doxy_input = "dir1 dir2"
    run_folder = tmp_path / "run"
    run_folder.mkdir()

    result = DoxygenGenerator.merge_doxygen_input(src_dirs, doxy_input, run_folder)
    assert result == doxy_input


def test_merge_doxygen_input_empty_doxy_input(tmp_path):
    # When doxy_input is empty, the function should return src_dirs unchanged.
    src_dirs = "dir1 dir2"
    doxy_input = ""
    run_folder = tmp_path / "run"
    run_folder.mkdir()

    result = DoxygenGenerator.merge_doxygen_input(src_dirs, doxy_input, run_folder)
    assert result == src_dirs


def test_merge_doxygen_input_both_non_empty(tmp_path):
    # When both src_dirs and doxy_input are provided, the result should contain all unique paths.
    src_dirs = "a b"
    doxy_input = "b c"
    run_folder = tmp_path / "run"
    run_folder.mkdir()

    result = DoxygenGenerator.merge_doxygen_input(src_dirs, doxy_input, run_folder)
    # The returned string is a space-separated list of paths relative to run_folder.
    # We compare as sets because the order may not be predictable.
    result_set = set(result.split())
    expected_set = {"a", "b", "c"}
    assert result_set == expected_set


def test_merge_doxygen_input_duplicates(tmp_path):
    # Duplicate paths in the inputs should be deduplicated.
    src_dirs = "a a"
    doxy_input = "a"
    run_folder = tmp_path / "run"
    run_folder.mkdir()

    result = DoxygenGenerator.merge_doxygen_input(src_dirs, doxy_input, run_folder)
    result_list = result.split()
    # Expect only one occurrence of "a"
    assert result_list == ["a"]
