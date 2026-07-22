from shipgate.cli import main


def test_gates_lib_path_command():
    code = main(["gates", "lib-path"])
    assert code == 0
