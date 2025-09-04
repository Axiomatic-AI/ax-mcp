from pydantic import BaseModel


class PhysicsModelProposerResponse(BaseModel):
    physics_model_code: str
    parameters: dict[str, float]
    optimization_results: str
    last_message: str
