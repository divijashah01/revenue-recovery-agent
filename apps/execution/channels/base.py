class ChannelResult:
    def __init__(self, success, detail="", cost=0.0):
        self.success = success
        self.detail = detail
        self.cost = cost