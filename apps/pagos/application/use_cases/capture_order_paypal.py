class CreateCaptureOrderPaypalUseCase:
    def __init__(self, gateway):
        self.gateway = gateway
    def execute(self,order_id:str):
        return self.gateway.capture_order(order_id)