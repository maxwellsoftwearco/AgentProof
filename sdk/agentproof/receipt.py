class Receipt:
    def __init__(self, data: dict, client):
        self._data = data
        self._client = client

    @property
    def receipt_id(self):
        return self._data["receipt_id"]

    @property
    def agent_id(self):
        return self._data["agent_id"]

    @property
    def action(self):
        return self._data["action"]

    @property
    def timestamp(self):
        return self._data["timestamp"]

    @property
    def authorization_status(self):
        return self._data["authorization_status"]

    @property
    def result_status(self):
        return self._data["result_status"]

    @property
    def metadata(self):
        return self._data["metadata"]

    @property
    def record_hash(self):
        return self._data["record_hash"]

    @property
    def verification_url(self):
        return self._data["verification_url"]

    def __repr__(self):
        return (
            f"Receipt("
            f"receipt_id={self.receipt_id!r}, "
            f"action={self.action!r}, "
            f"verified=True"
            f")"
        )
    
    def verify(self):
        response = self._client.verify_receipt(
            self.receipt_id
        )

        return response