class FlowRequest:
    def __init__(self, version=None, action=None, screen=None, data=None,
                 flow_token=None):
        self.version = version
        self.action = action
        self.screen = screen
        self.data = data
        self.flow_token = flow_token


class FlowResponse:
    def __init__(self, version=None, action=None, screen=None, data=None):
        self.version = version
        self.action = action
        self.screen = screen
        self.data = data
