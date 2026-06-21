class Argument:
    def __init__(
            self, report_dir: str = "",
            project_id: int = 0,
            task_id: int = 0,
            tester_name: int = 0,
            tcsp: str = "",
            tcs: str = "",
            user_name: str = "",
            product_name: str = "",
            mp_folder_path: str = ""
            ):
        self.report_dir = report_dir
        self.project_id = project_id
        self.task_id = task_id
        self.tester_name = tester_name
        self.tcsp = tcsp
        self.tcs = tcs
        self.user_name = user_name
        self.product_name = product_name
        self.mp_folder_path = mp_folder_path


class Result:
    def __init__(self, is_ok: bool, err_code: str = "", assert_number: str = "", exception: Exception | None = None) -> None:
        self.is_ok = is_ok
        self.err_code = err_code
        self.assert_number = assert_number

        # variables below are filled by tool
        self.test_result = ""
        self.exception = ""
        self.test_target_time = ""  # burnin time
        self.test_duration = ""
        self.error_attribute = ""  # assign to 0: pps, 1: fw

        self.is_continued_with_failure = False

    def __bool__(self) -> bool:
        return self.is_ok