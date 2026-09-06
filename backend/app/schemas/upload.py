from pydantic import BaseModel


class CloudinarySignatureResponse(BaseModel):
    cloud_name: str
    api_key: str
    timestamp: int
    signature: str
    folder: str
