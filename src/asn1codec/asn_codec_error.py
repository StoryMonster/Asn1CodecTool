
class AsnCodeError(RuntimeError):
    def __init__(self, error_info):
        super(RuntimeError, self).__init__(error_info)